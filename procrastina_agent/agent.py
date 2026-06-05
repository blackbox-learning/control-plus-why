"""
ProcrastinaAI Desktop Agent — Main Orchestrator

Ties together: tracker.py, idle_detector.py, api_client.py

AGENT LIFECYCLE:
  1. User clicks "Start My Day" in the browser
  2. Browser stores session ID in localStorage
  3. User runs: python agent.py <session_id>
  4. Agent calls POST /api/activity/start-session/
  5. Tracking loop starts:
     - Every TRACKING_INTERVAL_SECONDS: read active window
     - On focus switch: log app_focus event
     - On idle detected: log idle_start
     - On idle ended: log idle_end
     - Periodically flush event buffer
  6. User presses Ctrl+C or "Stop My Day" in browser
  7. Agent calls POST /api/activity/end-session/
  8. Clean shutdown

USAGE:
  python agent.py <session_id>

  session_id: UUID from the ProcrastinaAI "Start My Day" session.
              Found in browser localStorage: procrastina_ai_session.sessionId

EXAMPLE:
  python agent.py 550e8400-e29b-41d4-a716-446655440000

PRIVACY:
  This agent only reads the active window title and process name.
  It does NOT record: typed text, clipboard, screenshots, files, browser history.
"""

import argparse
import logging
import signal
import sys
import time
import threading
from datetime import datetime, timezone
from typing import Optional

import config
from api_client import APIClient
from tracker import get_active_window, WindowInfo
from idle_detector import IdleDetector

logger = logging.getLogger("procrastina_agent")


# ============================================================
# Agent State
# ============================================================

class AgentState:
    """Tracks the current state of the agent for focus-switch detection."""

    def __init__(self):
        self.current_app: Optional[str] = None          # current process_name
        self.current_title: str = ""                     # current window title
        self.app_focus_time: Optional[float] = None     # monotonic time when focus started
        self.event_buffer: list = []                     # buffered events not yet sent
        self.total_events_sent: int = 0
        self.focus_switch_count: int = 0
        self.last_flush_time: float = time.monotonic()
        self.is_idle: bool = False
        self.is_running: bool = False


# ============================================================
# Logging setup
# ============================================================

def setup_logging():
    """Configure structured logging to stdout."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


# ============================================================
# Event building
# ============================================================

def build_app_focus_event(
    window_info: WindowInfo,
    prev_app: Optional[str] = None,
    prev_duration: float = 0,
) -> dict:
    """
    Build an app_focus event dict for the API.

    If prev_app is provided, also generates an app_blur event for the previous app
    (returned separately via the blur return).
    """
    event = {
        "event_type": "app_focus",
        "target_name": window_info.process_name,
        "windowTitle": window_info.title,
        "processName": window_info.process_name,
        "duration_seconds": 0,
        "metadata": {
            "pid": window_info.pid,
            "hwnd": window_info.hwnd,
        },
    }
    return event


def build_app_blur_event(process_name: str, duration: float) -> dict:
    """Build an app_blur event for when focus leaves an application."""
    return {
        "event_type": "app_blur",
        "target_name": process_name,
        "processName": process_name,
        "duration_seconds": duration,
        "windowTitle": "",
        "metadata": {},
    }


# ============================================================
# Core tracking loop
# ============================================================

def tracking_loop(state: AgentState, client: APIClient):
    """
    Main tracking loop. Runs until state.is_running is set to False.

    Every TRACKING_INTERVAL_SECONDS:
      1. Read current active window
      2. Compare to previous focus
      3. On switch: emit app_blur (prev) + app_focus (new)
      4. Buffer events; flush when buffer full or time elapsed
    """
    logger.info("Tracking loop started.")

    while state.is_running:
        window = get_active_window()

        if window is None or not window.is_valid:
            # No valid window — skip this tick
            time.sleep(config.TRACKING_INTERVAL_SECONDS)
            continue

        # Detect focus switch
        if state.current_app is not None and not _is_same_process(state.current_app, window.process_name):
            # App switched — emit blur for previous app, focus for new app
            duration = _elapsed_focus(state)

            blur_event = build_app_blur_event(state.current_app, duration)
            focus_event = build_app_focus_event(window)

            state.event_buffer.append(blur_event)
            state.event_buffer.append(focus_event)

            state.focus_switch_count += 1
            logger.debug(
                f"Focus switch: {state.current_app} → {window.process_name} "
                f"(after {duration:.0f}s)"
            )

            # Update state
            state.current_app = window.process_name
            state.current_title = window.title
            state.app_focus_time = time.monotonic()

        elif state.current_app is None:
            # First valid window — log initial focus
            focus_event = build_app_focus_event(window)
            state.event_buffer.append(focus_event)
            state.current_app = window.process_name
            state.current_title = window.title
            state.app_focus_time = time.monotonic()
            logger.info(f"Initial focus: {window.process_name} — {window.title}")

        else:
            # Same app — update title if changed (e.g., new tab in Chrome)
            if window.title != state.current_title:
                # Title change within same app: log a window_change event
                state.event_buffer.append({
                    "event_type": "window_change",
                    "target_name": window.process_name,
                    "windowTitle": window.title,
                    "processName": window.process_name,
                    "duration_seconds": 0,
                    "metadata": {"previous_title": state.current_title},
                })
                state.current_title = window.title

        # Flush buffer if threshold met
        _maybe_flush(state, client)

        time.sleep(config.TRACKING_INTERVAL_SECONDS)

    logger.info("Tracking loop stopped.")


def _is_same_process(a: str, b: str) -> bool:
    return a.lower() == b.lower()


def _elapsed_focus(state: AgentState) -> float:
    """Seconds since the current app gained focus."""
    if state.app_focus_time is None:
        return 0.0
    return time.monotonic() - state.app_focus_time


def _maybe_flush(state: AgentState, client: APIClient):
    """Flush the event buffer if it's full or the time interval has elapsed."""
    now_mono = time.monotonic()
    time_since_flush = now_mono - state.last_flush_time

    should_flush = (
        len(state.event_buffer) >= config.EVENT_BUFFER_SIZE
        or time_since_flush >= config.BUFFER_FLUSH_INTERVAL_SECONDS
    )

    if should_flush and state.event_buffer:
        events = state.event_buffer[:]
        state.event_buffer.clear()
        state.last_flush_time = now_mono

        result = client.log_batch(events)
        if result.get("success"):
            count = result["data"].get("loggedCount", len(events))
            state.total_events_sent += count
            logger.debug(f"Flushed {count} events (total sent: {state.total_events_sent})")
        else:
            # Put events back in buffer for retry
            state.event_buffer = events + state.event_buffer
            logger.warning(f"Flush failed: {result.get('error')}")


# ============================================================
# Idle callbacks
# ============================================================

def make_on_idle_start(state: AgentState, client: APIClient):
    """Return a callback for when idle starts."""
    def on_idle_start(idle_start_time: datetime):
        state.is_idle = True
        # Log a blur event for the currently focused app before idle
        if state.current_app:
            duration = _elapsed_focus(state)
            client.log_event(
                event_type="app_blur",
                target_name=state.current_app,
                window_title=state.current_title,
                process_name=state.current_app,
                duration_seconds=duration,
            )
        client.log_idle_start(
            idle_type="no_input",
            started_at=idle_start_time,
            last_active_app=state.current_app or "",
        )
    return on_idle_start


def make_on_idle_end(state: AgentState, client: APIClient):
    """Return a callback for when idle ends (activity resumes)."""
    def on_idle_end(idle_end_time: datetime, duration_seconds: float):
        state.is_idle = False
        client.log_idle_end(
            ended_at=idle_end_time,
            duration_seconds=duration_seconds,
        )
        # Reset current app so the next valid window triggers a fresh app_focus
        state.current_app = None
        state.current_title = ""
        state.app_focus_time = None
    return on_idle_end


# ============================================================
# Shutdown handling
# ============================================================

def make_shutdown_handler(state: AgentState, client: APIClient):
    """Return a signal handler for clean shutdown on Ctrl+C."""
    def handler(signum, frame):
        if not state.is_running:
            # Second Ctrl+C — force exit
            logger.warning("Force exit.")
            sys.exit(1)

        logger.info("Shutdown requested. Ending activity session...")
        state.is_running = False

        # Send final blur for current app
        if state.current_app and state.app_focus_time:
            duration = _elapsed_focus(state)
            state.event_buffer.append(build_app_blur_event(state.current_app, duration))

        # Flush remaining events
        if state.event_buffer:
            _maybe_flush_force(state, client)

        # End activity session
        result = client.end_session()
        if result.get("success"):
            data = result["data"]
            logger.info(
                f"\nSession ended successfully.\n"
                f"  Total events sent : {state.total_events_sent}\n"
                f"  Focus switches    : {state.focus_switch_count}\n"
                f"  Active time       : {data.get('totalActiveSeconds', 0):.0f}s\n"
                f"  Idle time         : {data.get('totalIdleSeconds', 0):.0f}s"
            )
        else:
            logger.error(f"Failed to end session cleanly: {result.get('error')}")

    return handler


def _maybe_flush_force(state: AgentState, client: APIClient):
    """Force-flush all buffered events regardless of threshold."""
    while state.event_buffer:
        events = state.event_buffer[:config.EVENT_BUFFER_SIZE]
        state.event_buffer = state.event_buffer[config.EVENT_BUFFER_SIZE:]
        result = client.log_batch(events)
        if result.get("success"):
            state.total_events_sent += result["data"].get("loggedCount", len(events))
        else:
            logger.warning(f"Force flush failed for {len(events)} events.")


# ============================================================
# Entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="procrastina_agent",
        description="ProcrastinaAI Windows Desktop Activity Agent",
        epilog=(
            "Example:\n"
            "  python agent.py 550e8400-e29b-41d4-a716-446655440000\n\n"
            "The session_id is created when you click 'Start My Day' in the browser.\n"
            "Find it in browser DevTools: localStorage.getItem('procrastina_ai_session')"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "session_id",
        type=str,
        help="UUID of the ProcrastinaAI session (from 'Start My Day')",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help=f"Backend URL (default: {config.API_BASE_URL})",
    )
    args = parser.parse_args()

    setup_logging()
    logger.info("=" * 50)
    logger.info("  ProcrastinaAI Desktop Agent v" + config.AGENT_VERSION)
    logger.info("  Platform: Windows")
    logger.info("  Session : " + args.session_id)
    logger.info("  Backend : " + (args.api_url or config.API_BASE_URL))
    logger.info("=" * 50)

    # Initialize components
    client = APIClient(base_url=args.api_url)
    state = AgentState()

    # Start activity session on backend
    result = client.start_session(args.session_id)
    if not result.get("success"):
        logger.error(f"Cannot start activity session: {result.get('error')}")
        logger.error(
            "Make sure:\n"
            "  1. The Django server is running (python manage.py runserver)\n"
            "  2. You have an active ProcrastinaAI session ('Start My Day')\n"
            "  3. The session ID is correct"
        )
        sys.exit(1)

    logger.info("Activity session started on backend.")
    logger.info("Starting idle detector and tracking loop...")
    logger.info("Press Ctrl+C to stop tracking and end the session.\n")

    # Start idle detector
    idle_detector = IdleDetector(
        idle_threshold=config.IDLE_THRESHOLD_SECONDS,
        on_idle_start=make_on_idle_start(state, client),
        on_idle_end=make_on_idle_end(state, client),
    )
    idle_detector.start()

    # Register shutdown handler
    state.is_running = True
    signal.signal(signal.SIGINT, make_shutdown_handler(state, client))

    # Run tracking loop (blocks until is_running = False)
    try:
        tracking_loop(state, client)
    except Exception as e:
        logger.error(f"Tracking loop crashed: {e}", exc_info=True)
    finally:
        idle_detector.stop()
        logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
