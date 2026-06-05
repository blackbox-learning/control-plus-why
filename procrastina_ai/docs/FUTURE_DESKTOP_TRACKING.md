# ProcrastinaAI — Desktop Tracking Architecture

## Overview

This document describes the architecture for the ProcrastinaAI desktop activity tracking system. The backend includes a dedicated integration layer (`desktop_integration.py`) that validates, normalizes, and processes incoming events. A fully implemented Windows desktop agent (`procrastina_agent/`) monitors real application usage and sends activity data to the backend.

The existing manual workflow (Session → Disappearance → Report) remains unchanged. The desktop agent adds a parallel data stream that enriches reports with real application usage data.

---

## Current System (Manual Workflow)

### User Flow
```
Start My Day → Prediction → I Got Distracted → Save Reasons → Stop My Day → Report
```

### Models
| Model | Purpose |
|-------|--------|
| `Session` | Manual session (mood, interests, tasks, active_seconds) |
| `Disappearance` | User-logged distraction with AI response |
| `Report` | End-of-day report with AI summary |

### API Endpoints (Manual Workflow)
```
POST /api/create-session/          # Start My Day
POST /api/generate-prediction/     # AI prediction
POST /api/save-disappearance/      # I Got Distracted
POST /api/end-session/             # Stop My Day (auto-ends active agent session)
POST /api/generate-report/         # Generate report
GET  /api/session-data/            # Get session data (includes activity + agent status)
POST /api/activity-heartbeat/      # Browser activity heartbeat
GET  /api/idle-return-options/     # AI-generated options for idle-return popup
POST /api/save-return-reason/      # Save idle-return reason as Disappearance
GET  /api/recover-session/         # Server-side session recovery
POST /api/agent-disconnect/        # Force-end active agent session
```

---

## Current System (Automated + Manual Workflow)

### Architecture Diagram
```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ProcrastinaAI Backend                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────┐  ┌──────────────────────┐  ┌─────────────────┐  ┌────────┐ │
│  │ Models  │◄─│  activity_services   │◄─│ desktop_        │◄─│ Views  │ │
│  │         │  │                      │  │ integration     │  │        │ │
│  │ Session │  │ • start_session      │  │                 │  │ Manual │ │
│  │ Disapp  │  │ • log_event          │  │ • validate      │  │ API    │ │
│  │ Report  │  │ • log_idle           │  │ • normalize     │  │        │ │
│  │ ActSess │  │ • analytics          │  │ • categorize    │  │Activity│ │
│  │ ActLog  │  │ • report             │  │ • focus track   │  │ API    │ │
│  │ AppUsge │  │ • timeline           │  │ • idle mgmt     │  │        │ │
│  │ WebUsge │  │                      │  │                 │  │        │ │
│  │ IdlePer │  │                      │  │                 │  │        │ │
│  └─────────┘  └──────────────────────┘  └────────┬────────┘  └────────┘ │
│                                                    │                      │
└────────────────────────────────────────────────────┼──────────────────────┘
                                                     │
                                           ┌────────▼─────────┐
                                           │  Desktop Agent    │
                                           │  (Python)         │
                                           │                   │
                                           │ • Window tracking │
                                           │ • App monitoring  │
                                           │ • Idle detection  │
                                           │ • Process list    │
                                           │ • System tray     │
                                           └───────────────────┘
```

### Data Flow
```
Desktop Agent (pystray + psutil + pynput)
    ↓  POST /api/activity/start-session/
    ↓  POST /api/activity/log/         (every 1-2 seconds on window change)
    ↓  POST /api/activity/idle/        (after 5 min no input)
    ↓  POST /api/activity/idle-end/    (when input resumes)
    ↓  POST /api/activity/end-session/ (on shutdown)
    ↓
desktop_integration.py (validate, normalize app names, categorize, track focus)
    ↓
activity_services.py (store events, aggregate usage, build timeline)
    ↓
Database (ActivitySession, ActivityLog, ApplicationUsage, IdlePeriod)
    ↓
Report Generation (enhanced AI reports with real app usage data)
    ↓
Existing Frontend (dashboard shows live agent status, report shows top apps/timeline)
```

### Idle-Return Flow
```
Agent detects idle period (5+ min no input)
    ↓
User resumes activity → Agent sends app_focus event
    ↓
Frontend AgentPoller detects idle→active transition
    ↓
Frontend calls GET /api/idle-return-options/?sessionId=xxx
    ↓
AI generates contextual distraction options (based on user interests, past disappearances)
    ↓
Idle-return modal appears with dynamic options
    ↓
User selects reason → POST /api/save-return-reason/
    ↓
AI generates reaction → Saved as Disappearance → Modal closes
```

### Session Recovery Flow
```
Page load → SessionRecovery module runs
    ↓
Check localStorage for saved sessionId
    ↓
If found: Call GET /api/recover-session/
    ↓
Server checks for active Session with matching ID
    ↓
If active: Return session data → Restore frontend state → Resume AgentPoller
If not active: Clear localStorage → User starts fresh
```

---

## Database Schema (Activity Models)

### ActivitySession
Tracks a single connection from a desktop agent.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `session` | FK → Session | Parent manual session |
| `source` | CharField | 'desktop_agent', 'manual_api' |
| `client_version` | CharField | Version of client software |
| `platform` | CharField | OS: windows, macos, linux |
| `started_at` | DateTime | When tracking started |
| `updated_at` | DateTime | Last activity event received |
| `ended_at` | DateTime | When tracking ended |
| `is_active` | Boolean | Still running? |
| `total_active_seconds` | Float | Aggregated active time |
| `total_idle_seconds` | Float | Aggregated idle time |
| `event_count` | Integer | Total events received |
| `focus_change_count` | Integer | Number of app focus switches |
| `last_active_app` | CharField | Currently focused application |
| `last_idle_started` | DateTime | When current idle started (null if active) |

### ActivityLog
Individual activity events from desktop agent or browser extension.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `activity_session` | FK → ActivitySession | Parent activity session |
| `event_type` | CharField | 'app_focus', 'app_blur', 'website_visit', 'website_leave', 'input_detected', 'window_change', 'system_event' |
| `target_name` | CharField | App name or website domain |
| `category` | CharField | 'productivity', 'development', 'communication', 'social', 'entertainment', 'ai_tools', 'browsing', 'system', 'other' |
| `metadata` | JSON | Extra: window title, URL path, process name |
| `timestamp` | DateTime | When event occurred |
| `duration_seconds` | Float | Duration if applicable |

### ApplicationUsage
Aggregated time in specific applications.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `activity_session` | FK → ActivitySession | Parent activity session |
| `app_name` | CharField | Application name (VS Code, Chrome) |
| `app_process` | CharField | Process name (code.exe, chrome.exe) |
| `category` | CharField | Category |
| `total_seconds` | Float | Total time in app |
| `focus_events` | Integer | Times user focused this app |
| `first_seen` | DateTime | First focus time |
| `last_seen` | DateTime | Last focus time |

### WebsiteUsage
Aggregated time on specific websites.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `activity_session` | FK → ActivitySession | Parent activity session |
| `domain` | CharField | Domain (youtube.com, instagram.com) |
| `title` | CharField | Page title |
| `url_path` | CharField | URL path for deeper tracking |
| `category` | CharField | Category |
| `total_seconds` | Float | Total time on site |
| `visit_count` | Integer | Number of visits |
| `first_seen` | DateTime | First visit time |
| `last_seen` | DateTime | Last visit time |

### IdlePeriod
Detected periods of no user activity.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `activity_session` | FK → ActivitySession | Parent activity session |
| `idle_type` | CharField | 'no_input', 'screen_locked', 'system_sleep', 'away' |
| `started_at` | DateTime | When idle started |
| `ended_at` | DateTime | When idle ended |
| `duration_seconds` | Float | Duration of idle |
| `last_active_app` | CharField | App before idle |
| `last_active_domain` | CharField | Website before idle |

---

## Activity Tracking API

All endpoints are CSRF-exempt for external client access. All events go through `desktop_integration.py` for validation and normalization.

### POST `/api/activity/start-session/`
Start a new activity tracking session.

**Request:**
```json
{
  "sessionId": "uuid-of-manual-session",
  "source": "desktop_agent",
  "clientVersion": "1.0.0",
  "platform": "windows"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "activitySessionId": "uuid",
    "sessionId": "uuid",
    "startedAt": "2026-06-05T10:00:00Z"
  }
}
```

### POST `/api/activity/log/`
Log one or more activity events. Raw process names are auto-normalized.

**Single event:**
```json
{
  "activitySessionId": "uuid",
  "eventType": "app_focus",
  "targetName": "code.exe",
  "windowTitle": "models.py - procrastina_ai",
  "processName": "code.exe",
  "durationSeconds": 0,
  "metadata": { "pid": 12345 }
}
```

**Response includes focus detection:**
```json
{
  "success": true,
  "data": {
    "eventId": "uuid",
    "eventType": "app_focus",
    "targetName": "Visual Studio Code",
    "category": "development",
    "focusChanged": true
  }
}
```

**Batch events:**
```json
{
  "activitySessionId": "uuid",
  "events": [
    {"event_type": "app_focus", "target_name": "code.exe", "duration_seconds": 120},
    {"event_type": "app_focus", "target_name": "chrome.exe", "duration_seconds": 60}
  ]
}
```

### POST `/api/activity/idle/`
Log an idle period start (no user activity detected).

**Request:**
```json
{
  "activitySessionId": "uuid",
  "idleType": "no_input",
  "startedAt": "2026-06-05T10:30:00Z",
  "lastActiveApp": "code.exe",
  "lastActiveDomain": "youtube.com"
}
```

### POST `/api/activity/idle-end/`
End an idle period (user resumed activity).

**Request:**
```json
{
  "activitySessionId": "uuid",
  "endedAt": "2026-06-05T10:35:00Z",
  "durationSeconds": 300
}
```

### POST `/api/activity/end-session/`
End an activity tracking session. Auto-closes any open idle periods.

**Request:**
```json
{
  "activitySessionId": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "activitySessionId": "uuid",
    "totalActiveSeconds": 3600,
    "totalIdleSeconds": 900,
    "eventCount": 247
  }
}
```

### POST `/api/activity/report/`
Generate enhanced report with activity data.

**Request:**
```json
{
  "sessionId": "uuid-of-manual-session"
}
```

### POST `/api/activity/analytics/`
Get comprehensive session analytics (manual + activity data, timeline, idle periods).

---

## Desktop Integration Layer

`desktop_integration.py` is the dedicated entry point for all desktop agent events.

### Responsibilities
- **Validate** incoming event payloads (check required fields, valid event types)
- **Normalize** application names (`code.exe` → `Visual Studio Code`)
- **Categorize** apps/websites automatically using `activity_services.py`
- **Track focus** changes between applications
- **Manage idle** periods (start/end, auto-close on session end)
- **Get agent status** for dashboard display

### Process Name Normalization
The agent sends raw OS process names. The integration layer converts them:

| Raw Process Name | Normalized Name |
|-----------------|----------------|
| `code.exe` | Visual Studio Code |
| `chrome.exe` | Google Chrome |
| `spotify.exe` | Spotify |
| `discord.exe` | Discord |
| `explorer.exe` | File Explorer |
| `windowsterminal.exe` | Terminal |
| `slack.exe` | Slack |

Supports 40+ process names across Windows, macOS, and Linux.

---

### Desktop Agent Implementation (Windows)

The desktop agent is fully implemented in `procrastina_agent/`.

#### Architecture
```
procrastina_agent/
├── agent.py              Main orchestrator — tracking loop, focus detection, shutdown
├── tracker.py            Active window reader via ctypes.windll + psutil
├── idle_detector.py      Keyboard/mouse listener via pynput for idle detection
├── api_client.py         HTTP client — session lifecycle, event batching, offline buffer
├── config.py             Configurable values (URLs, thresholds, buffer sizes)
├── test_integration.py   Full lifecycle smoke test (8/8 checks passed)
├── requirements.txt      Dependencies: psutil, pynput, requests
└── README.md             Installation, running, API flow, troubleshooting
```

#### How It Works
1. **`agent.py`** starts the tracking loop, idle detector, and API client
2. **`tracker.py`** polls the active window every 2 seconds using `ctypes.windll.user32` + `psutil.Process.name()`
3. **`idle_detector.py`** runs pynput keyboard/mouse listeners; after 5 minutes with no input, fires `on_idle_start`
4. **`api_client.py`** manages the HTTP session — buffers events, batches sends, retries on failure, stores events offline if backend unreachable

#### Focus Switch Detection
When the active application changes (e.g., `code.exe` → `chrome.exe`):
- An `app_blur` event is emitted for the previous app (with duration)
- An `app_focus` event is emitted for the new app
- The `focus_change_count` on `ActivitySession` is incremented

#### Title Change Detection
When the same app changes its window title (e.g., switching Chrome tabs):
- A `window_change` event is emitted with the new title and previous title in metadata

#### Privacy
The agent collects only:
- Application process name (e.g., `code.exe`)
- Window title text
- Focus duration
- Activity timestamps
- Idle duration

It does NOT collect: typed text, clipboard, screenshots, files, browser history.

#### Usage
```powershell
cd procrastina_agent
pip install -r requirements.txt
python agent.py <session_id>
```

#### Required Python Packages
```
psutil>=5.9.0        # Process monitoring
pynput>=1.7.6        # Keyboard/mouse listening
requests>=2.28.0     # API communication
```

---

## Enhanced Frontend Display

### Dashboard (with desktop agent connected)
When activity data exists, the dashboard shows:
- **Desktop Agent Activity** panel with: Current Active App, Status (Active/Idle), Events count, Focus Switches
- Shows "Waiting for activity data" when no agent is connected
- Shows "DISCONNECTED" with "Reconnecting..." when agent connection is lost
- **Idle-return modal** appears automatically when agent detects user returning from idle (10+ min away)

### Agent Polling
The frontend `AgentPoller` module (in `script.js`):
- Polls `GET /api/session-data/` every **15 seconds** while on the dashboard
- Updates the agent status panel (Active App, Status, Events, Focus Switches)
- Detects idle→active transitions and triggers the idle-return popup
- Stops polling when the user clicks "Stop My Day" or navigates away

### Session Recovery
The frontend `SessionRecovery` module (in `script.js`):
- Runs on every page load
- Validates the sessionId stored in `localStorage`
- Calls `GET /api/recover-session/` to check if the session is still active on the server
- Restores session state if the server confirms an active session exists
- Clears stale localStorage entries if the server session has ended

## Auto-Disconnect on Stop
When the user clicks "Stop My Day":
1. Frontend calls `POST /api/end-session/` — ends the manual Session
2. Backend detects any active `ActivitySession` and auto-ends it (closes open idle periods, calculates totals)
3. Frontend `AgentPoller` stops polling
4. If the agent is still running locally, user can `Ctrl+C` it — the API will respond that the session is already ended (graceful handling)

### Report (with activity data)
When activity data exists, the report additionally shows:
- **Top Applications**: Ranked by time spent (VS Code: 42 min, Chrome: 27 min)
- **Category Breakdown**: Progress bars for Development, Entertainment, Communication, etc.
- **Idle Summary**: Each idle period with duration and context
- **Activity Timeline**: Chronological flow (VS Code → Chrome → YouTube → Idle → VS Code)

All sections gracefully fall back when no activity data is available.

---

## Auto-Categorization

The system auto-categorizes applications and websites:

### Applications
| App Name | Category |
|----------|----------|
| Visual Studio Code, Sublime, IntelliJ | development |
| Notion, Obsidian, Google Docs | productivity |
| Slack, Discord, Zoom, Teams | communication |
| Spotify, VLC, Steam | entertainment |
| Finder, File Explorer | system |

### Websites
| Domain | Category |
|--------|----------|
| youtube.com, netflix.com, twitch.tv | entertainment |
| instagram.com, twitter.com, reddit.com | social |
| chat.openai.com, claude.ai, gemini.google.com | ai_tools |
| github.com, stackoverflow.com | development |
| notion.so, figma.com | productivity |
| mail.google.com, web.whatsapp.com | communication |

Categories can be overridden via the API when logging events.

---

## Migration Path

### Phase 1: Backend Ready (COMPLETE)
- [x] Database models for activity tracking (5 models)
- [x] Service layer (`activity_services.py`) — event processing, analytics, timeline, enhanced reports
- [x] Desktop integration layer (`desktop_integration.py`) — validation, normalization, focus tracking
- [x] Activity API endpoints (8 endpoints including idle-end)
- [x] Idle-return + session recovery API endpoints (4 endpoints)
- [x] Enhanced report generation with dual data source support
- [x] Auto-categorization of 40+ apps/websites
- [x] Dashboard shows live agent status when connected (15s polling)
- [x] Report shows top apps, category breakdown, idle summary, activity timeline
- [x] Process name normalization (code.exe → Visual Studio Code)
- [x] Idle-return popup with AI-generated contextual options
- [x] Session recovery (localStorage + server-side validation)
- [x] Auto-disconnect agent on "Stop My Day"
- [x] Comprehensive test suite (39 tests across 5 files, all passing)
- [x] Accuracy fixes: idle double-counting, active seconds, server-computed durations

### Phase 2: Desktop Agent (COMPLETE)
- [x] Build Windows desktop agent (`procrastina_agent/agent.py`)
- [x] Implement active window tracking (`tracker.py` — ctypes.windll + psutil)
- [x] Implement idle detection (`idle_detector.py` — pynput keyboard/mouse listeners)
- [x] Build HTTP API client with batching and offline buffering (`api_client.py`)
- [x] Connect to ProcrastinaAI Activity API endpoints (all 7 endpoints)
- [x] Handle reconnection and event buffering (offline buffer + flush)
- [x] Focus switch detection (app_blur + app_focus events)
- [x] Window title change detection (window_change events)
- [x] Clean shutdown on Ctrl+C (flush events + end session)
- [x] Integration test with 8/8 lifecycle checks passing
- [x] Agent README with installation, running, API flow, troubleshooting

---

## File Structure

```
control-plus-why/
├── procrastina_agent/                 # Windows Desktop Agent
│   ├── agent.py                       # Main orchestrator
│   ├── tracker.py                     # Active window tracker (ctypes.windll + psutil)
│   ├── idle_detector.py               # Idle detection (pynput)
│   ├── api_client.py                  # HTTP client (batching, retries, offline buffer)
│   ├── config.py                      # Configuration (URLs, thresholds, buffer sizes)
│   ├── test_integration.py            # Full lifecycle smoke test
│   ├── requirements.txt               # psutil, pynput, requests
│   └── README.md                      # Agent documentation
│
├── procrastina_ai/                    # ProcrastinaAI Backend
│   ├── models.py                      # Session, Disappearance, Report + Activity models
│   ├── services.py                    # AI generation (predictions, responses, reports, idle-return options)
│   ├── activity_services.py           # Activity processing, analytics, timeline, enhanced reports
│   ├── desktop_integration.py         # Agent integration layer (validate, normalize, categorize)
│   ├── views.py                       # 6 page views + 19 API views
│   ├── urls.py                        # All URL routes (25 endpoints)
│   ├── tests/                         # Test suite (39 tests across 5 files)
│   ├── docs/
│   │   ├── DOCUMENTATION.md           # Full project documentation
│   │   ├── GETTING_STARTED.md         # Beginner's guide
│   │   ├── FUTURE_DESKTOP_TRACKING.md # This document
│   │   ├── PROJECT_HEALTH_CHECK.md    # System health status
│   │   └── SYSTEM_TEST_REPORT.md      # Test execution results (39 tests)
│   ├── static/procrastina_ai/
│   │   ├── script.js                  # Frontend utilities + ActivityTracker + AgentPoller + SessionRecovery
│   │   └── style.css                  # Premium dark design system
│   └── templates/procrastina_ai/
│       ├── base.html                  # Navigation, branding
│       ├── index.html                 # Landing page
│       ├── setup.html                 # Session setup
│       ├── prediction.html            # AI prediction
│       ├── dashboard.html             # Dashboard (shows agent status when connected)
│       ├── report.html                # Report (shows top apps, timeline when available)
│       └── funny_reasons.html         # Funny excuses
```
