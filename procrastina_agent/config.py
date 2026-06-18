"""
ProcrastinaAI Desktop Agent — Configuration

All configurable values for the agent. Modify these to match your setup.
"""

import os

# ============================================================
# Backend Connection
# ============================================================
# URL of the running Django development server.
# Default: http://localhost:8000
# If using a different host/port, update this value.
API_BASE_URL = "http://localhost:8000"

# The URL path prefix for ProcrastinaAI API endpoints.
# Must match the urls.py configuration in the Django project.
API_PREFIX = "/projects/procrastina-ai/api"

# ============================================================
# Agent Identity
# ============================================================
# Sent to the backend on every start-session call.
AGENT_SOURCE = "desktop_agent"
AGENT_VERSION = "1.0.0"
AGENT_PLATFORM = "windows"

# ============================================================
# Tracking Behaviour
# ============================================================
# How often (in seconds) the tracker polls the active window.
# 2 seconds balances accuracy with low CPU usage.
TRACKING_INTERVAL_SECONDS = 2

# How long (in seconds) of no keyboard/mouse input before idle is declared.
# 600 seconds = 10 minutes. Matches the automatic workflow: when the user
# steps away for 10 minutes, the idle-return popup fires on return.
IDLE_THRESHOLD_SECONDS = int(os.environ.get('IDLE_THRESHOLD_SECONDS', 600))

# How many events to buffer before sending a batch to the backend.
# Batching reduces HTTP overhead. 10 events ≈ 20 seconds of normal use.
EVENT_BUFFER_SIZE = 10

# How often (in seconds) to flush the event buffer to the backend
# even if the buffer isn't full.
BUFFER_FLUSH_INTERVAL_SECONDS = 30

# ============================================================
# Logging
# ============================================================
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# ============================================================
# Retry / Resilience
# ============================================================
# How many seconds to wait before retrying a failed API call.
API_RETRY_DELAY_SECONDS = 5

# Maximum number of consecutive API failures before the agent
# enters offline mode (buffers events locally until connection returns).
API_MAX_RETRIES_BEFORE_OFFLINE = 5
