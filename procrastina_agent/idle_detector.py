"""
ProcrastinaAI Desktop Agent — Idle Detector (Windows)

Monitors keyboard and mouse activity to detect when the user goes idle.
Uses pynput to listen for global input events without recording content.

PRIVACY RULES:
  - Only detects THAT input happened (timestamps)
  - Does NOT record what was typed, mouse positions, or click targets
  - No clipboard, screenshot, or file access

IDLE DETECTION LOGIC:
  - Every keyboard key press or mouse movement/click resets a "last input" timer
  - If no input is detected for IDLE_THRESHOLD_SECONDS (default: 5 minutes),
    the user is classified as idle
  - When input resumes, the idle period ends and duration is recorded

STATE MACHINE:
  ACTIVE ──(no input for threshold)──► IDLE
    ▲                                    │
    └────────(input detected)────────────┘
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from pynput import mouse, keyboard

import config

logger = logging.getLogger(__name__)


class IdleDetector:
    """
    Monitors global keyboard/mouse activity to detect idle periods.

    Callbacks:
        on_idle_start(idle_start_time: datetime) — called when idle threshold is exceeded
        on_idle_end(idle_end_time: datetime, duration_seconds: float) — called on resume

    Usage:
        detector = IdleDetector(on_idle_start=..., on_idle_end=...)
        detector.start()
        # ... agent runs ...
        detector.stop()
    """

    def __init__(
        self,
        idle_threshold: float = None,
        on_idle_start: Optional[Callable[[datetime], None]] = None,
        on_idle_end: Optional[Callable[[datetime, float], None]] = None,
    ):
        self._idle_threshold = idle_threshold or config.IDLE_THRESHOLD_SECONDS
        self._on_idle_start = on_idle_start
        self._on_idle_end = on_idle_end

        self._last_input_time: float = time.monotonic()
        self._is_idle: bool = False
        self._idle_started_at: Optional[datetime] = None
        self._idle_started_mono: Optional[float] = None

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._check_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._lock = threading.Lock()

    # ----------------------------------------------------------------
    # Input callbacks — only record THAT input happened
    # ----------------------------------------------------------------

    def _on_mouse_move(self, x, y):
        self._record_input()

    def _on_mouse_click(self, x, y, button, pressed):
        self._record_input()

    def _on_mouse_scroll(self, x, y, dx, dy):
        self._record_input()

    def _on_key_press(self, key):
        self._record_input()

    def _record_input(self):
        """Record that input was detected. Thread-safe."""
        with self._lock:
            now_mono = time.monotonic()

            if self._is_idle:
                # Input resumed — end idle period
                idle_duration = now_mono - self._idle_started_mono
                idle_ended_at = datetime.now(timezone.utc)
                self._is_idle = False
                self._idle_started_at = None
                self._idle_started_mono = None
                logger.info(f"Activity resumed. Idle lasted {idle_duration:.0f}s")

                if self._on_idle_end:
                    # Fire callback outside lock to avoid deadlocks
                    threading.Thread(
                        target=self._on_idle_end,
                        args=(idle_ended_at, idle_duration),
                        daemon=True,
                    ).start()

            self._last_input_time = now_mono

    # ----------------------------------------------------------------
    # Idle check loop
    # ----------------------------------------------------------------

    def _check_loop(self):
        """
        Background loop that checks for idle every second.
        Fires on_idle_start callback when the threshold is exceeded.
        """
        while not self._stop_event.wait(1.0):
            with self._lock:
                if self._is_idle:
                    continue  # Already idle; wait for _record_input to end it

                elapsed = time.monotonic() - self._last_input_time
                if elapsed >= self._idle_threshold:
                    # User has gone idle
                    self._is_idle = True
                    self._idle_started_at = datetime.now(timezone.utc)
                    self._idle_started_mono = time.monotonic()
                    logger.info(
                        f"No input for {elapsed:.0f}s — user is now idle."
                    )

                    if self._on_idle_start:
                        threading.Thread(
                            target=self._on_idle_start,
                            args=(self._idle_started_at,),
                            daemon=True,
                        ).start()

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def start(self):
        """Start monitoring input and the idle check loop."""
        if self._mouse_listener or self._keyboard_listener:
            logger.warning("IdleDetector already started.")
            return

        self._last_input_time = time.monotonic()
        self._is_idle = False
        self._stop_event.clear()

        # Start pynput listeners (suppress=False — we only observe, don't block)
        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)

        self._mouse_listener.start()
        self._keyboard_listener.start()

        # Start background idle check thread
        self._check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self._check_thread.start()

        logger.info(
            f"IdleDetector started (threshold={self._idle_threshold}s)"
        )

    def stop(self):
        """Stop monitoring. Ends any current idle period without firing callback."""
        self._stop_event.set()

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        if self._check_thread:
            self._check_thread.join(timeout=3)
            self._check_thread = None

        logger.info("IdleDetector stopped.")

    @property
    def is_idle(self) -> bool:
        """Whether the user is currently classified as idle."""
        with self._lock:
            return self._is_idle

    @property
    def seconds_since_last_input(self) -> float:
        """Seconds elapsed since the last detected input event."""
        with self._lock:
            return time.monotonic() - self._last_input_time
