# ProcrastinaAI — Complete Project Documentation

---

## 1. Project Overview

**ProcrastinaAI** is a humor-first web application that treats procrastination as a craft. Built under the **Ctrl+Why** brand (*"We build useless products with serious engineering"*), it uses AI (OpenRouter free models) to predict how users will procrastinate, roast them when they log distractions, generate daily reports, and create absurd excuses for unfinished tasks.

**Core Idea:** Instead of fighting procrastination, embrace it with serious engineering and terrible advice. The app takes a genuine problem (procrastination) and wraps it in a premium, polished, sarcastic experience.

**Target Users:** Creators, students, developers, and anyone who procrastinates and can appreciate self-aware humor about it.

**How it works:** Users enter their tasks, mood, and interests. The AI predicts exactly how they'll procrastinate throughout the day. When users get distracted, they manually click "I Got Distracted" and log where they went. The AI roasts them. When the desktop agent detects the user returning from an idle period (10+ minutes away), an idle-return popup asks where they went and generates an AI reaction. At day's end, they click "Stop My Day" (which auto-disconnects the agent) and get a full report with real activity metrics, a procrastination score, achievements, and an AI summary. Session recovery ensures no data is lost if the browser closes or the server restarts.

---

## 2. Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- OpenRouter API key (free — for AI features)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd control-plus-why
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openrouter_api_key_here
   ```
   Get a free API key from: https://openrouter.ai/keys

   **Note:** The `OPENAI_API_KEY` env var name is required because we use the OpenAI SDK pointed at OpenRouter's API.

5. **Set up the database:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

8. **Open your browser:**
   - Main site: http://127.0.0.1:8000/
   - ProcrastinaAI: http://127.0.0.1:8000/projects/procrastina-ai/
   - Admin panel: http://127.0.0.1:8000/admin/

---

## 3. Current Workflow

```
User Opens Landing Page
        |
Clicks "Start My Day"
        |
Setup Page: Enter tasks + select mood chips (7 options) + custom mood input
        |
Select interest chips (7 options) + add custom interests via tag input
        |
Submit Form -> API creates Session in database
        |
AI Generates Procrastination Prediction (5-7 step journey)
        |
Prediction Page: Timeline + confidence meter + AI warning -> "Accept My Fate"
        |
Dashboard: Status bar, floating "I Got Distracted" button, stats, tasks, leaderboard
        |
User Clicks "I Got Distracted" -> Modal with radio options appears
        |
User selects distraction type -> AI generates roast response -> Saved to DB
        |
Agent detects user returning from idle (10+ min) -> Idle-return popup appears
        |
User selects reason -> AI generates reaction -> Saved as Disappearance
        |
User Clicks "Stop My Day" -> Agent auto-disconnects -> Session ends -> Auto-redirect to Report
        |
Report Page: Session length, active/idle time, distractions, score, achievements, AI summary
        |
Funny Reasons Page: AI-generated excuses for each unfinished task
```

**All pages are fully connected to the backend API.** The frontend dynamically fetches real data and displays live stats.

---

## 4. Brand Identity

**ProcrastinaAI™** — *Professional Procrastination Management*

- **Logo:** SVG progress circle permanently stuck at 87%, with "PA" lettermark inside
- **Navigation:** Premium SaaS layout — Logo Left, Nav Center, Actions Right
- **Mobile:** Hamburger menu with smooth slide-in panel
- **Color scheme:** Dark futuristic theme with warm amber accent (`#f59e0b`)
- **Typography:** Inter (sans) + JetBrains Mono (monospace)
- **Design inspiration:** Linear, Arc, Raycast, Stripe

---

## 5. Pages and Routes

| URL | Template | Description |
|-----|----------|-------------|
| `/projects/procrastina-ai/` | `index.html` | Landing page with hero, floating stat cards, AI roast preview |
| `/projects/procrastina-ai/setup/` | `setup.html` | Mood chips (7) + custom input, interest chips (7) + custom tag input, task input |
| `/projects/procrastina-ai/prediction/` | `prediction.html` | AI-generated timeline, confidence bar, AI warning |
| `/projects/procrastina-ai/dashboard/` | `dashboard.html` | Status bar, floating "I Got Distracted" button, stats grid, task list, leaderboard, AI observations |
| `/projects/procrastina-ai/report/` | `report.html` | Gated (locked until "Stop My Day"), session metrics, achievements, AI summary |
| `/projects/procrastina-ai/funny-reasons/` | `funny_reasons.html` | Per-task AI excuses with copy/regenerate |

**Report Gating:** The report page is inaccessible until the user clicks "Stop My Day". If they navigate to `/report/` while the session is active, they see: *"Your day is still running. Finish your procrastination journey first."*

**Per-Page Navigation:**
- Landing: Home, Demo Report
- Dashboard: Home, Dashboard, Reasons
- Report: Home, Dashboard

---

## 6. Database Structure

### Core Models (Manual Workflow)

#### Session
| Field | Type | Description |
|-------|------|-------------|
| id | UUIDField (PK) | Auto-generated UUID |
| mood | CharField(50) | User's mood selection |
| interests | JSONField | List of interests (preset + custom) |
| tasks | JSONField | List of planned tasks |
| is_active | BooleanField | Session active or ended |
| active_seconds | FloatField | Browser-tracked active time |
| ended_at | DateTimeField | When "Stop My Day" was clicked |
| activity_data_sufficient | BooleanField | Whether 30+ seconds of activity tracked |
| created_at / updated_at | DateTimeField | Timestamps |

#### Disappearance
| Field | Type | Description |
|-------|------|-------------|
| id | UUIDField (PK) | Auto-generated UUID |
| session | FK → Session | CASCADE, related_name='disappearances' |
| disappearance_type | CharField(100) | youtube, laptops, ai_tools, startup, comments, other |
| custom_location | CharField(255) | Custom distraction if "other" |
| ai_response | TextField | AI-generated roast |
| created_at | DateTimeField | Timestamp |

#### Report
| Field | Type | Description |
|-------|------|-------------|
| id | UUIDField (PK) | Auto-generated UUID |
| session | FK → Session | CASCADE, related_name='reports' |
| report_date | DateField | Auto-set |
| tasks_planned / tasks_completed | IntegerField | Task counts |
| total_disappearances | IntegerField | Distraction count |
| procrastination_score | IntegerField | 0-100 |
| ai_summary | TextField | AI-generated report text |

### Activity Tracking Models (Desktop Agent)

These models are actively used by the Windows desktop agent (`procrastina_agent/`):

#### ActivitySession
Tracks a connection from the desktop agent. Linked to a parent Session.
- Fields: source (desktop_agent), platform, client_version, total_active_seconds, total_idle_seconds, event_count, focus_change_count, last_active_app, last_idle_started, updated_at

#### ActivityLog
Individual activity events (app_focus, website_visit, input_detected, window_change, etc.)
- Fields: event_type, target_name, category, metadata (JSON), duration_seconds

#### ApplicationUsage
Aggregated time in specific applications (VS Code: 45min, Chrome: 2h, etc.)
- Fields: app_name, app_process, category, total_seconds, focus_events

#### WebsiteUsage
Aggregated time on specific websites (youtube.com: 1h30m, instagram.com: 25m)
- Fields: domain, title, url_path, category, total_seconds, visit_count

#### IdlePeriod
Detected periods of no user activity (no input, screen locked, system sleep)
- Fields: idle_type, started_at, ended_at, duration_seconds, last_active_app, last_active_domain

### Relationships
```
Session (1) ──→ (N) Disappearance
Session (1) ──→ (N) Report
Session (1) ──→ (N) ActivitySession ──→ (N) ActivityLog
                                    ──→ (N) ApplicationUsage
                                    ──→ (N) WebsiteUsage
                                    ──→ (N) IdlePeriod
```

---

## 7. Backend Architecture

### Views (`views.py`)
6 page views (render HTML) + 19 API views (return JSON). All function-based with `@csrf_exempt` on POST endpoints and `@require_http_methods` decorators.

### AI Services (`services.py`)
5 AI generation functions using OpenRouter free models with automatic model fallback:
- `generate_prediction()` — 5-7 step procrastination journey
- `generate_disappearance_response()` — Witty roast for each distraction
- `generate_daily_report()` — Humorous end-of-day summary
- `generate_funny_reasons()` — 3-4 absurd excuses per task
- `generate_idle_return_options()` — Contextual popup options when user returns from idle

All use the `_call_ai()` helper which tries 4 free models in order:
1. `google/gemma-4-31b-it:free`
2. `nvidia/nemotron-3-super-120b-a12b:free`
3. `meta-llama/llama-3.3-70b-instruct:free`
4. `meta-llama/llama-3.2-3b-instruct:free`

### Desktop Integration Layer (`desktop_integration.py`)
Dedicated entry point for all incoming desktop agent events:
- Validates event payloads (required fields, valid event types)
- Normalizes 40+ OS process names to friendly display names (`code.exe` → `Visual Studio Code`)
- Auto-categorizes apps into known categories
- Detects and logs focus switches between applications
- Manages idle period lifecycle (start/end, auto-close on session end)
- Provides real-time agent status for dashboard display

### Activity Services (`activity_services.py`)
Service layer for desktop activity tracking:
- `start_activity_session()` / `end_activity_session()` — Manage tracking sessions
- `log_activity_event()` / `log_batch_events()` — Log app/website events
- `log_idle_period()` — Log idle periods
- `get_session_analytics()` — Unified analytics (manual + activity data, timeline)
- `generate_enhanced_report()` — Reports with real app/website usage data
- `get_activity_timeline()` — Chronological event flow for reports
- Auto-categorization of 40+ known apps and websites

### Models (`models.py`)
8 models: 3 core (Session, Disappearance, Report) + 5 activity tracking (ActivitySession, ActivityLog, ApplicationUsage, WebsiteUsage, IdlePeriod).

### URLs (`urls.py`)
Namespaced under `procrastina_ai`. 6 page routes + 19 API routes.

### Architecture Diagram
```
User Browser (Manual Workflow)          Windows Desktop Agent (procrastina_agent/)
    │                                        │
    │                                        │ tracker.py + idle_detector.py
    │                                        │       ↓
    │                                        │ api_client.py
    │                                        │       ↓
Django URL Router (control_plus_why/urls.py)
    │
procrastina_ai/urls.py
    │
Page Views → Render Templates (HTML)
Manual API Views → Parse JSON → services.py (AI) → Models → JSON
Activity API Views → Parse JSON → desktop_integration.py → activity_services.py → Models → JSON
```

---

## 8. API Endpoints

### Manual Workflow APIs (used by frontend)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/create-session/` | Start My Day — create session with mood, interests, tasks |
| POST | `/api/generate-prediction/` | AI prediction journey |
| POST | `/api/save-disappearance/` | Log distraction + get AI roast |
| POST | `/api/end-session/` | Stop My Day — end session, auto-end agent, store activity data |
| POST | `/api/generate-report/` | Generate daily report (auto-detects activity data) |
| POST | `/api/generate-funny-reasons/` | AI excuses per task |
| GET | `/api/session-data/?sessionId=xxx` | Full session data + stats + agent status |
| POST | `/api/activity-heartbeat/` | Browser activity tracker heartbeat |

### Idle Return + Session Recovery APIs (used by frontend)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/idle-return-options/?sessionId=xxx` | AI-generated contextual distraction options for idle-return popup |
| POST | `/api/save-return-reason/` | Save idle-return reason as Disappearance + AI reaction |
| GET | `/api/recover-session/` | Server-side session recovery (most recent active session) |
| POST | `/api/agent-disconnect/` | Force-end active agent ActivitySession |

### Activity Tracking APIs (used by Windows desktop agent)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/activity/start-session/` | Start activity tracking session |
| POST | `/api/activity/end-session/` | End activity tracking session |
| POST | `/api/activity/log/` | Log event(s) — single or batch |
| POST | `/api/activity/idle/` | Log idle period start |
| POST | `/api/activity/idle-end/` | Log idle period end |
| POST | `/api/activity/report/` | Enhanced report with activity data |
| POST | `/api/activity/analytics/` | Comprehensive session analytics |

All POST endpoints are `@csrf_exempt` for external client compatibility.

---

## 9. Report Generation

### Dual Data Source Support

The report system automatically detects which data is available:

**Manual-only mode (current):**
- Uses disappearances, tasks, common excuse
- Browser activity tracker provides active/idle time
- Shows "Not enough activity data collected" if < 30 seconds tracked

**Activity-enhanced mode (with desktop agent):**
- Adds top applications, category breakdown, idle summary, activity timeline
- AI summary references real usage ("You spent 2h on YouTube")
- Productivity ratio and distraction score from actual data

### Report Metrics
- **Session Length** — Actual wall clock time from start to end
- **Active Time** — Seconds with detected browser activity (mousemove, click, keydown, scroll)
- **Idle Time** — Session length minus active time
- **Distractions Logged** — Count of manual distraction entries
- **Tasks Planned** — Number of tasks entered at setup

### Browser Activity Tracker
The frontend `script.js` includes an `ActivityTracker` module that:
- Listens to `mousemove`, `click`, `keydown`, `scroll`, `touchstart`
- Counts a second as "active" only if an actual event fires
- Sends heartbeat to server every 30 seconds
- Replaces the old fake calculation (`disCount * 25 + tasks * 15`)

---

## 10. Frontend Architecture

### Template Inheritance
```
procrastina_ai/base.html (nav, branding, mobile menu, footer)
    ├── index.html (landing page)
    ├── setup.html (onboarding form)
    ├── prediction.html (AI timeline)
    ├── dashboard.html (stats hub + modal)
    ├── report.html (gated report)
    └── funny_reasons.html (AI excuses)
```

### Navigation Blocks
Each page can override `{% block pa_nav %}` and `{% block pa_mobile_nav %}` to customize nav items.

### Design System (`style.css`)
- CSS custom properties for colors, typography, spacing, shadows
- Dark theme with warm amber accent (`#f59e0b`)
- Glassmorphism (backdrop-filter blur, semi-transparent surfaces)
- Premium gradients, smooth transitions
- Responsive: desktop → 768px tablet → 480px mobile
- Components: chips, stat cards, timeline steps, modals, floating buttons, status bars, badges

### JavaScript (`script.js`)
- API helpers (`apiPost`, `apiGet`, `fetchSessionData`) with CSRF handling
- Session management via `localStorage`
- Chip selection handler
- Notification system
- **ActivityTracker** — Real browser activity detection (mousemove, click, keydown, scroll, 30s heartbeat)
- **AgentPoller** — Polls agent status every 15s, updates dashboard panel, detects idle-return transitions
- **SessionRecovery** — Validates localStorage on page load, recovers active session from server if needed
- Display helpers (`showLoading`, `showError`, `showEmpty`)

---

## 11. Full Project Structure

```
control-plus-why/
├── manage.py                          # Django CLI entry point
├── requirements.txt                   # Python dependencies
├── .env                               # Environment variables (you create this)
├── GETTING_STARTED.md                 # Beginner's guide
├── README.md                          # Project overview
│
├── control_plus_why/                  # Django project configuration
│   ├── settings.py                    # Main Django settings
│   ├── urls.py                        # Root URL routing
│   ├── asgi.py / wsgi.py             # Server configs
│
├── home/                              # Landing page app
│   ├── views.py                       # index() and about() views
│   ├── templates/home/                # Homepage + about page
│   └── static/home/                   # Global styles + logo
│
├── procrastina_agent/                 # Windows Desktop Agent
│   ├── agent.py                       # Main orchestrator
│   ├── tracker.py                     # Active window tracker (Windows)
│   ├── idle_detector.py               # Idle detection via pynput
│   ├── api_client.py                  # HTTP client for Django backend
│   ├── config.py                      # Agent configuration
│   ├── test_integration.py            # Lifecycle smoke test
│   ├── requirements.txt               # Agent dependencies
│   └── README.md                      # Agent documentation
│
└── procrastina_ai/                    # ProcrastinaAI app
    ├── models.py                      # 8 models (3 core + 5 activity)
    ├── views.py                       # 6 page views + 19 API views
    ├── services.py                    # AI generation (OpenRouter free models)
    ├── activity_services.py           # Activity processing service layer
    ├── desktop_integration.py         # Agent integration layer (validate, normalize, categorize)
    ├── urls.py                        # 6 page + 19 API URL patterns
    ├── admin.py                       # Admin panel configuration
    ├── tests/                         # Test suite (39 tests)
    │   ├── __init__.py
    │   ├── test_session_flow.py       # 10 tests — session lifecycle + recovery
    │   ├── test_agent_connection.py   # 9 tests — agent start/end/disconnect
    │   ├── test_activity_tracking.py  # 6 tests — event logging + focus detection
    │   ├── test_idle_detection.py     # 6 tests — idle start/end/accumulation
    │   └── test_report_generation.py  # 8 tests — reports + idle-return options
    ├── docs/
    │   ├── DOCUMENTATION.md           # This file
    │   ├── GETTING_STARTED.md         # Beginner's guide
    │   ├── FUTURE_DESKTOP_TRACKING.md # Desktop agent architecture
    │   ├── PROJECT_HEALTH_CHECK.md    # System health status (all components)
    │   └── SYSTEM_TEST_REPORT.md      # Test execution results (39 tests)
    ├── migrations/
    │   ├── 0001_initial.py
    │   ├── 0002_...py
    │   ├── 0003_session_active_seconds_and_more.py
    │   ├── 0004_activitysession_...py
    │   └── 0005_activitysession_focus_change_count_and_more.py
    ├── static/procrastina_ai/
    │   ├── script.js                  # Frontend JS + ActivityTracker + AgentPoller + SessionRecovery
    │   └── style.css                  # Design system (~1880 lines)
    └── templates/procrastina_ai/
        ├── base.html                  # Premium nav + branding + mobile menu
        ├── index.html                 # Landing page
        ├── setup.html                 # Setup form with chips + custom inputs
        ├── prediction.html            # AI prediction timeline
        ├── dashboard.html             # Status bar + agent panel + stats
        ├── report.html                # Gated report with top apps + timeline
        └── funny_reasons.html         # AI excuses per task
```

---

## 12. AI Configuration

### Provider
**OpenRouter** — Aggregator API for multiple LLM providers. Used because it offers free model access.

### Model Fallback Chain
When a model is rate-limited or unavailable, the system automatically tries the next:
1. `google/gemma-4-31b-it:free`
2. `nvidia/nemotron-3-super-120b-a12b:free`
3. `meta-llama/llama-3.3-70b-instruct:free`
4. `meta-llama/llama-3.2-3b-instruct:free`

### SDK Setup
Uses the OpenAI Python SDK pointed at OpenRouter's base URL:
```python
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),  # OpenRouter key
    base_url='https://openrouter.ai/api/v1',
)
```

### AI Writing Standard
All AI outputs follow strict rules:
- 2-4 short lines maximum
- Simple words a kid would understand
- Funny but kind — tease, don't insult
- Sound like a friend texting a joke

---

## 13. Desktop Agent

A Windows desktop agent (`procrastina_agent/`) is fully implemented and tested.

### Features
- **Active window tracking** — reads the focused application via `ctypes.windll` + `psutil`
- **Window title detection** — captures the full title (e.g., `views.py — procrastina_ai - Visual Studio Code`)
- **Application switching** — detects focus changes and logs `app_blur` + `app_focus` events
- **Idle detection** — monitors keyboard/mouse via `pynput`; triggers idle after 5 minutes of no input
- **Event batching** — buffers events and flushes in batches to reduce HTTP overhead
- **Offline resilience** — stores events locally if the backend is unreachable, replays when connection returns
- **Clean shutdown** — `Ctrl+C` flushes remaining events and ends the session gracefully

### Files
| File | Purpose |
|------|--------|
| `agent.py` | Main orchestrator — tracking loop, focus detection, shutdown |
| `tracker.py` | Windows active window reader via `ctypes.windll` + `psutil` |
| `idle_detector.py` | Keyboard/mouse listener via `pynput` for idle detection |
| `api_client.py` | HTTP client — session lifecycle, event batching, offline buffer |
| `config.py` | All configurable values (URLs, thresholds, buffer sizes) |
| `test_integration.py` | Full lifecycle smoke test (8/8 checks passed) |

Full implementation details: `procrastina_agent/README.md` and `procrastina_ai/docs/FUTURE_DESKTOP_TRACKING.md`

---

## 14. Admin Panel

### Access
1. Create superuser: `python manage.py createsuperuser`
2. Visit: http://127.0.0.1:8000/admin/

### Available Models
| Model | What You Can Do |
|-------|-----------------|
| **Sessions** | View sessions, filter by mood/status, search by ID |
| **Disappearances** | View distractions, see AI responses, filter by type |
| **Reports** | View reports with scores and AI summaries |
| **Activity Sessions** | View desktop agent / extension connections |
| **Activity Logs** | View individual activity events |
| **Application Usage** | View aggregated app usage per session |
| **Website Usage** | View aggregated website time per session |
| **Idle Periods** | View detected idle windows |

---

## 15. Current Status

### Fully Working
- Complete manual workflow (Setup → Prediction → Dashboard → Report → Funny Reasons)
- All pages connected to backend APIs with real data
- AI features via OpenRouter free models with fallback
- Report gating (locked until "Stop My Day")
- Browser activity tracking (active/idle time)
- Premium SaaS navigation with mobile hamburger menu
- Custom mood and interest inputs with tag system
- Status bar with live stats on dashboard
- Per-page navigation customization
- Idle-return popup with AI-generated contextual options
- Session recovery (localStorage + server-side)
- Auto-disconnect agent on "Stop My Day"
- Agent status panel with live polling (15s interval)
- 39-test comprehensive test suite (all passing)

### Desktop Agent (Implemented)
- Windows desktop agent (`procrastina_agent/`) fully built and tested
- Active window tracking via `ctypes.windll` + `psutil`
- Idle detection via `pynput` keyboard/mouse listeners (5-minute threshold)
- Application focus switch detection with `app_blur` + `app_focus` events
- Event batching and offline buffering for resilience
- Integration test passes all 8 lifecycle checks
- Dashboard shows live agent status when connected
- Report shows top apps, category breakdown, idle summary, activity timeline

### Backend Activity Infrastructure
- 5 activity tracking models in database
- 7 activity API endpoints (including idle-end)
- Desktop integration layer (`desktop_integration.py`) for validation and normalization
- Activity service layer (`activity_services.py`) with analytics and timeline
- Auto-categorization of 40+ apps/websites
- Process name normalization (`code.exe` → `Visual Studio Code`)
- Enhanced report generation with dual data source support

---

## 16. Known Limitations

- **Windows-only agent** — Desktop agent uses `ctypes.windll` (Windows API). Manual fallback works on all platforms.
- **OpenRouter free-tier** — Rate limits and model availability may vary. 4-model fallback chain + hardcoded responses mitigate this.
- **Polling (not WebSockets)** — Dashboard polls every 15s instead of real-time push.
- **Single-user session recovery** — `recover-session` returns the most recent active session globally.
- **No authentication** — All API endpoints are public. Suitable for single-user; needs auth for multi-user.
- **SQLite default** — Adequate for development; PostgreSQL recommended for production.
- **Agent requires manual start** — `python agent.py <session_id>` via command line (no system tray yet).

---

## 17. Quick Deployment

1. Set environment variables in `.env`: `OPENAI_API_KEY`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`
2. Run `python manage.py migrate` and `python manage.py collectstatic --noinput`
3. Serve with Gunicorn: `gunicorn control_plus_why.wsgi:application --bind 0.0.0.0:8000 --workers 3`
4. Configure HTTPS via reverse proxy (nginx)
5. Desktop agent: `cd procrastina_agent && pip install -r requirements.txt && python agent.py <session_id>`
