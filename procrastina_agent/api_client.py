"""
ProcrastinaAI Desktop Agent — API Client

Handles all HTTP communication between the desktop agent and the Django backend.
Manages session lifecycle, event batching, retries, and offline buffering.

ENDPOINTS USED:
  POST /api/activity/start-session/   — Begin activity tracking
  POST /api/activity/log/             — Send activity events (single or batch)
  POST /api/activity/idle/            — Report idle period start
  POST /api/activity/idle-end/        — Report idle period end
  POST /api/activity/end-session/     — End activity tracking
"""

import time
import logging
import requests
from datetime import datetime, timezone

import config

logger = logging.getLogger(__name__)


class APIClient:
    """
    HTTP client for the ProcrastinaAI activity API.

    Lifecycle:
      1. create_session(session_id) → stores activity_session_id
      2. log_event(...) / log_batch(...) → sends activity events
      3. log_idle_start(...) / log_idle_end(...) → manages idle periods
      4. end_session() → cleanly ends tracking

    Offline mode:
      If the backend is unreachable, events are stored in an offline buffer.
      When connection returns, flush_offline_buffer() sends them in batch.
    """

    def __init__(self, base_url=None, api_prefix=None):
        self.base_url = (base_url or config.API_BASE_URL).rstrip("/")
        self.api_prefix = (api_prefix or config.API_PREFIX).rstrip("/")
        self.activity_session_id = None
        self._consecutive_failures = 0
        self._offline_buffer = []  # events queued while backend unreachable
        self._is_online = True

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _url(self, endpoint: str) -> str:
        """Build a full API URL from an endpoint name."""
        return f"{self.base_url}{self.api_prefix}/{endpoint}/"

    def _post(self, endpoint: str, payload: dict) -> dict:
        """
        POST to the backend with retry logic.

        Returns:
            dict: {'success': True/False, 'data': ..., 'error': ...}
            {'success': False, 'error': '...'} on failure.
        """
        url = self._url(endpoint)
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Reset failure counter on success
            self._consecutive_failures = 0
            self._is_online = True
            logger.debug(f"POST {endpoint} → 200 OK")
            return data

        except requests.exceptions.ConnectionError:
            self._handle_connection_failure(endpoint, payload)
            return {"success": False, "error": "Connection refused. Backend unreachable."}

        except requests.exceptions.Timeout:
            self._handle_connection_failure(endpoint, payload)
            return {"success": False, "error": "Request timed out."}

        except requests.exceptions.HTTPError as e:
            logger.warning(f"POST {endpoint} → HTTP {e.response.status_code}: {e.response.text}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}

        except Exception as e:
            logger.error(f"POST {endpoint} → unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def _handle_connection_failure(self, endpoint: str, payload: dict):
        """Called when the backend is unreachable. Buffers event for later retry."""
        self._consecutive_failures += 1
        self._is_online = False
        logger.warning(
            f"Connection failed ({self._consecutive_failures}/"
            f"{config.API_MAX_RETRIES_BEFORE_OFFLINE}): {endpoint}"
        )
        # Buffer log events (not start/end-session calls) for offline replay
        if endpoint == "activity/log":
            self._offline_buffer.append({"endpoint": endpoint, "payload": payload})
        elif endpoint == "activity/idle":
            self._offline_buffer.append({"endpoint": endpoint, "payload": payload})
        elif endpoint == "activity/idle-end":
            self._offline_buffer.append({"endpoint": endpoint, "payload": payload})

    # ----------------------------------------------------------------
    # Session lifecycle
    # ----------------------------------------------------------------

    def start_session(self, session_id: str) -> dict:
        """
        Start an activity tracking session linked to the parent Django Session.

        Args:
            session_id: UUID of the parent Session (from Start My Day)

        Returns:
            dict: {
                'success': True,
                'data': {'activitySessionId': '<uuid>', ...}
            }
        """
        payload = {
            "sessionId": session_id,
            "source": config.AGENT_SOURCE,
            "clientVersion": config.AGENT_VERSION,
            "platform": config.AGENT_PLATFORM,
        }
        result = self._post("activity/start-session", payload)

        if result.get("success"):
            self.activity_session_id = result["data"]["activitySessionId"]
            logger.info(
                f"Activity session started: {self.activity_session_id} "
                f"(parent: {session_id})"
            )
        else:
            logger.error(f"Failed to start activity session: {result.get('error')}")

        return result

    def end_session(self) -> dict:
        """
        End the current activity tracking session.
        Flushes any remaining offline buffer events first.

        Returns:
            dict: {
                'success': True,
                'data': {'totalActiveSeconds': float, 'eventCount': int, ...}
            }
        """
        if not self.activity_session_id:
            logger.warning("end_session called but no active session.")
            return {"success": False, "error": "No active activity session."}

        # Try to flush offline buffer before ending
        self.flush_offline_buffer()

        payload = {"activitySessionId": self.activity_session_id}
        result = self._post("activity/end-session", payload)

        if result.get("success"):
            logger.info(
                f"Activity session ended: {self.activity_session_id} "
                f"(events: {result['data'].get('eventCount', 0)}, "
                f"active: {result['data'].get('totalActiveSeconds', 0)}s)"
            )
            self.activity_session_id = None
        else:
            logger.error(f"Failed to end activity session: {result.get('error')}")

        return result

    # ----------------------------------------------------------------
    # Event logging
    # ----------------------------------------------------------------

    def log_event(
        self,
        event_type: str,
        target_name: str,
        window_title: str = "",
        process_name: str = "",
        duration_seconds: float = 0,
        metadata: dict = None,
    ) -> dict:
        """
        Log a single activity event.

        Args:
            event_type: 'app_focus', 'app_blur', 'window_change', 'input_detected'
            target_name: Application name (raw process name OK; backend normalizes)
            window_title: Full window title text
            process_name: Raw OS process name (e.g., 'code.exe')
            duration_seconds: How long this event lasted
            metadata: Extra data dict

        Returns:
            dict from backend (includes 'focusChanged' flag)
        """
        if not self.activity_session_id:
            return {"success": False, "error": "No active activity session."}

        payload = {
            "activitySessionId": self.activity_session_id,
            "eventType": event_type,
            "targetName": target_name,
            "windowTitle": window_title,
            "processName": process_name,
            "durationSeconds": duration_seconds,
            "metadata": metadata or {},
        }
        return self._post("activity/log", payload)

    def log_batch(self, events: list) -> dict:
        """
        Log multiple events in a single API call.

        Args:
            events: list of event dicts, each with keys:
                event_type, target_name, windowTitle, processName,
                duration_seconds, metadata

        Returns:
            dict: {'success': True, 'data': {'loggedCount': int, 'failedCount': int}}
        """
        if not self.activity_session_id:
            return {"success": False, "error": "No active activity session."}

        if not events:
            return {"success": True, "data": {"loggedCount": 0, "failedCount": 0}}

        # Normalize event keys to match backend expectations
        normalized = []
        for ev in events:
            normalized.append({
                "event_type": ev.get("event_type", "input_detected"),
                "target_name": ev.get("target_name", "Unknown"),
                "duration_seconds": ev.get("duration_seconds", 0),
                "metadata": ev.get("metadata", {}),
                "windowTitle": ev.get("windowTitle", ""),
                "processName": ev.get("processName", ""),
            })

        payload = {
            "activitySessionId": self.activity_session_id,
            "events": normalized,
        }
        result = self._post("activity/log", payload)
        if result.get("success"):
            logger.debug(f"Batch logged: {result['data'].get('loggedCount', 0)} events")
        return result

    # ----------------------------------------------------------------
    # Idle management
    # ----------------------------------------------------------------

    def log_idle_start(
        self,
        idle_type: str = "no_input",
        started_at: datetime = None,
        last_active_app: str = "",
    ) -> dict:
        """
        Report that the user has gone idle.

        Args:
            idle_type: 'no_input', 'screen_locked', 'system_sleep'
            started_at: When idle began (defaults to now)
            last_active_app: Application that was focused before idle

        Returns:
            dict from backend
        """
        if not self.activity_session_id:
            return {"success": False, "error": "No active activity session."}

        if started_at is None:
            started_at = datetime.now(timezone.utc)

        payload = {
            "activitySessionId": self.activity_session_id,
            "idleType": idle_type,
            "startedAt": started_at.isoformat(),
            "lastActiveApp": last_active_app,
            "lastActiveDomain": "",
        }
        result = self._post("activity/idle", payload)
        if result.get("success"):
            logger.info(f"Idle started: type={idle_type}, last_app={last_active_app}")
        return result

    def log_idle_end(
        self,
        ended_at: datetime = None,
        duration_seconds: float = 0,
    ) -> dict:
        """
        Report that the user has resumed activity after idle.

        Args:
            ended_at: When activity resumed (defaults to now)
            duration_seconds: How long the idle period lasted

        Returns:
            dict from backend
        """
        if not self.activity_session_id:
            return {"success": False, "error": "No active activity session."}

        if ended_at is None:
            ended_at = datetime.now(timezone.utc)

        payload = {
            "activitySessionId": self.activity_session_id,
            "endedAt": ended_at.isoformat(),
            "durationSeconds": duration_seconds,
        }
        result = self._post("activity/idle-end", payload)
        if result.get("success"):
            logger.info(f"Idle ended: duration={duration_seconds:.0f}s")
        return result

    # ----------------------------------------------------------------
    # Offline buffer management
    # ----------------------------------------------------------------

    def flush_offline_buffer(self) -> int:
        """
        Send all buffered offline events to the backend.

        Returns:
            int: Number of events successfully flushed
        """
        if not self._offline_buffer:
            return 0

        logger.info(f"Flushing {len(self._offline_buffer)} offline buffered events...")
        flushed = 0

        for item in self._offline_buffer[:]:
            result = self._post(item["endpoint"], item["payload"])
            if result.get("success"):
                self._offline_buffer.remove(item)
                flushed += 1
            else:
                # Still failing — stop trying this round
                break

        if flushed > 0:
            logger.info(f"Flushed {flushed} events. {len(self._offline_buffer)} remaining.")
        return flushed

    @property
    def is_online(self) -> bool:
        return self._is_online

    @property
    def is_active(self) -> bool:
        return self.activity_session_id is not None
