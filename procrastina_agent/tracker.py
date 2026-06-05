"""
ProcrastinaAI Desktop Agent — Window Tracker (Windows)

Detects the currently focused application and window title on Windows.
Uses win32gui and psutil to read the active window's process name and title.

COLLECTS (privacy-safe):
  - Application process name (e.g., 'code.exe', 'chrome.exe')
  - Friendly window title (e.g., 'views.py — procrastina_ai - Visual Studio Code')
  - Focus duration (time spent in each app before switching)

DOES NOT COLLECT:
  - Typed text, clipboard, screenshots, files, browser history

WORKS WITH:
  - Windows 10, Windows 11
  - UWP apps, Win32 apps, elevated windows
"""

import ctypes
import logging
from typing import Optional, Tuple

import psutil

logger = logging.getLogger(__name__)

# Windows API constants
GW_OWNER = 4

# Process names that should be ignored (system/desktop shells)
IGNORED_PROCESSES = {
    "explorer.exe",      # Windows shell / desktop / taskbar — not meaningful focus
    "searchhost.exe",    # Windows search overlay
    "shellexperiencehost.exe",
    "startmenuexperiencehost.exe",
    "textinputhost.exe",
    "runtimebroker.exe",
    "system",
    "idle",
}


def _get_foreground_window() -> int:
    """Return the handle (HWND) of the currently focused window."""
    user32 = ctypes.windll.user32
    return user32.GetForegroundWindow()


def _get_window_title(hwnd: int) -> str:
    """Return the text title of the given window handle."""
    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value.strip()


def _get_window_process(hwnd: int) -> Tuple[str, int]:
    """
    Return (process_name, pid) for the process that owns the given window.

    Falls back to ('unknown', 0) if the process can't be identified.
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pid_value = pid.value

    if pid_value == 0:
        return "unknown", 0

    try:
        proc = psutil.Process(pid_value)
        return proc.name(), pid_value
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown", pid_value


def _get_real_hwnd(hwnd: int) -> int:
    """
    Some top-level windows are owned by a hidden parent (e.g., Chrome popups).
    Walk up the owner chain to find the true top-level window.
    """
    user32 = ctypes.windll.user32
    while True:
        owner = user32.GetWindow(hwnd, GW_OWNER)
        if not owner:
            return hwnd
        hwnd = owner


class WindowInfo:
    """
    Snapshot of the currently focused window.

    Attributes:
        hwnd: Window handle
        title: Full window title text
        process_name: OS process name (e.g., 'code.exe')
        pid: Process ID
        is_valid: Whether this represents a real trackable window
    """

    __slots__ = ("hwnd", "title", "process_name", "pid", "is_valid")

    def __init__(self, hwnd: int, title: str, process_name: str, pid: int, is_valid: bool):
        self.hwnd = hwnd
        self.title = title
        self.process_name = process_name
        self.pid = pid
        self.is_valid = is_valid

    def __repr__(self):
        return (
            f"WindowInfo(process={self.process_name!r}, "
            f"title={self.title!r}, valid={self.is_valid})"
        )


def get_active_window() -> Optional[WindowInfo]:
    """
    Detect and return information about the currently focused window.

    Returns:
        WindowInfo with process_name, title, pid, is_valid.
        Returns None only on unexpected OS errors.

    Privacy:
        Only the process name and window title are captured.
        No file paths, typed text, or clipboard content is collected.
    """
    try:
        hwnd = _get_foreground_window()
        if not hwnd:
            return WindowInfo(0, "", "unknown", 0, is_valid=False)

        real_hwnd = _get_real_hwnd(hwnd)
        title = _get_window_title(real_hwnd)
        process_name, pid = _get_window_process(real_hwnd)

        # Skip the desktop shell and system processes
        if process_name.lower() in IGNORED_PROCESSES:
            return WindowInfo(real_hwnd, title, process_name, pid, is_valid=False)

        # Skip untitled windows (minimized to tray, splash screens)
        if not title:
            return WindowInfo(real_hwnd, title, process_name, pid, is_valid=False)

        return WindowInfo(real_hwnd, title, process_name, pid, is_valid=True)

    except Exception as e:
        logger.error(f"Failed to read active window: {e}")
        return None


def is_same_window(a: Optional[WindowInfo], b: Optional[WindowInfo]) -> bool:
    """
    Return True if two WindowInfo snapshots refer to the same application focus.
    Used to detect focus switches: if not is_same_window(prev, curr), a switch happened.

    Two windows are considered the "same" if they share the same process name.
    (We track app-level focus, not individual window focus.)
    """
    if a is None or b is None:
        return False
    return a.process_name.lower() == b.process_name.lower()
