"""
ProcrastinaAI Desktop Agent — Integration Smoke Test

Tests the full agent→backend lifecycle without running the real tracking loop.
Run this to verify your setup before using the real agent.

Usage:
  cd procrastina_agent
  python test_integration.py
"""

import sys
import time
import config
from api_client import APIClient
from tracker import get_active_window

PASS = "✓"
FAIL = "✗"

def main():
    results = []

    # Step 1: Create a Django session
    print("Step 1/7: Creating Django session...")
    client = APIClient()
    # Use _post directly to create a session (normally done via browser)
    session_result = client._post("create-session", {
        "mood": "motivated",
        "interests": ["Coding", "Music"],
        "tasks": ["Write tests", "Review code", "Deploy app"],
    })
    if session_result.get("success"):
        session_id = session_result["data"]["sessionId"]
        results.append((PASS, f"Django session created: {session_id[:8]}..."))
    else:
        results.append((FAIL, f"Django session failed: {session_result.get('error')}"))
        print_results(results)
        sys.exit(1)

    # Step 2: Start activity session
    print("Step 2/7: Starting activity session...")
    start_result = client.start_session(session_id)
    if start_result.get("success"):
        act_session_id = start_result["data"]["activitySessionId"]
        results.append((PASS, f"Activity session started: {act_session_id[:8]}..."))
    else:
        results.append((FAIL, f"Activity session failed: {start_result.get('error')}"))
        print_results(results)
        sys.exit(1)

    # Step 3: Read current active window
    print("Step 3/7: Reading active window...")
    window = get_active_window()
    if window and window.is_valid:
        results.append((PASS, f"Active window: {window.process_name} — {window.title[:50]}"))
    else:
        results.append((PASS, "No valid foreground window detected (normal during test)"))

    # Step 4: Send single event
    print("Step 4/7: Sending single app_focus event...")
    log_result = client.log_event(
        event_type="app_focus",
        target_name="code.exe",
        window_title="test_integration.py - procrastina_agent - Visual Studio Code",
        process_name="code.exe",
        duration_seconds=0,
    )
    if log_result.get("success"):
        results.append((PASS, f"Single event logged (focusChanged={log_result['data'].get('focusChanged', 'N/A')})"))
    else:
        results.append((FAIL, f"Single event failed: {log_result.get('error')}"))

    # Step 5: Send batch events
    print("Step 5/7: Sending batch events...")
    batch_result = client.log_batch([
        {"event_type": "app_blur", "target_name": "code.exe", "duration_seconds": 120},
        {"event_type": "app_focus", "target_name": "chrome.exe", "windowTitle": "YouTube", "processName": "chrome.exe"},
        {"event_type": "app_blur", "target_name": "chrome.exe", "duration_seconds": 60},
        {"event_type": "app_focus", "target_name": "spotify.exe", "windowTitle": "Lo-Fi Beats", "processName": "spotify.exe"},
    ])
    if batch_result.get("success"):
        count = batch_result["data"].get("loggedCount", 0)
        results.append((PASS, f"Batch logged: {count} events"))
    else:
        results.append((FAIL, f"Batch failed: {batch_result.get('error')}"))

    # Step 6: Test idle start/end
    print("Step 6/7: Testing idle lifecycle...")
    idle_start_result = client.log_idle_start(
        idle_type="no_input",
        last_active_app="spotify.exe",
    )
    if idle_start_result.get("success"):
        results.append((PASS, "Idle start logged"))
    else:
        results.append((FAIL, f"Idle start failed: {idle_start_result.get('error')}"))

    time.sleep(0.5)
    idle_end_result = client.log_idle_end(duration_seconds=180)
    if idle_end_result.get("success"):
        results.append((PASS, f"Idle end logged (duration={idle_end_result['data'].get('durationSeconds', 0)}s)"))
    else:
        results.append((FAIL, f"Idle end failed: {idle_end_result.get('error')}"))

    # Step 7: End activity session
    print("Step 7/7: Ending activity session...")
    end_result = client.end_session()
    if end_result.get("success"):
        data = end_result["data"]
        results.append((PASS, (
            f"Session ended — events: {data.get('eventCount', 0)}, "
            f"active: {data.get('totalActiveSeconds', 0)}s, "
            f"idle: {data.get('totalIdleSeconds', 0)}s"
        )))
    else:
        results.append((FAIL, f"End session failed: {end_result.get('error')}"))

    print_results(results)


def print_results(results):
    print("\n" + "=" * 60)
    print("  INTEGRATION TEST RESULTS")
    print("=" * 60)
    for status, msg in results:
        print(f"  {status}  {msg}")
    print("=" * 60)
    passed = sum(1 for s, _ in results if s == PASS)
    total = len(results)
    print(f"  {passed}/{total} checks passed")
    if passed == total:
        print("  ✓ All good — the agent can connect and send data!")
    else:
        print("  ✗ Some checks failed — see errors above.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
