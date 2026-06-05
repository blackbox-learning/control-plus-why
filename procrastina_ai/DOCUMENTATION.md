# ProcrastinaAI - Complete Project Documentation

---

## 1. Project Overview

**ProcrastinaAI** is a humor-first web application that treats procrastination as a craft. Built under the **Ctrl+Why** brand (*"We build useless products with serious engineering"*), it uses real AI (OpenAI GPT-3.5-turbo) to predict how users will procrastinate, roast them when they disappear, generate daily reports, and create absurd excuses for unfinished tasks.

**Core Idea:** Instead of fighting procrastination, embrace it with serious engineering and terrible advice. The app takes a genuine problem (procrastination) and wraps it in a premium, polished, sarcastic experience.

**Target Users:** Creators, students, developers, and anyone who procrastinates and can appreciate self-aware humor about it.

**How it works:** Users enter their tasks, mood, and interests. The AI predicts exactly how they'll procrastinate throughout the day. When inactivity is detected, a "Missing Person" popup asks where they went, and the AI roasts them. At day's end, a full report summarizes their procrastination achievements with a score.

---

## 2. Current Workflow

```
User Opens Landing Page
        |
Clicks "Start My Day"
        |
Setup Page: Enter Tasks (comma-separated text input)
        |
Select Mood (chip selector: Motivated / Sleepy / Burned Out / Lazy / Existential Crisis)
        |
Select Interests (multi-chip: YouTube / AI / Tech / Gaming / Instagram / Movies / Startups)
        |
Submit Form -> API creates Session in database
        |
AI Generates Procrastination Prediction (5-7 step journey)
        |
Prediction Page: Shows timeline + 94% confidence meter + AI warning
        |
Dashboard Page: Shows tasks, stats, excuses, AI observations
        |
Inactivity Detected -> "Where Did You Go?" Modal Appears
        |
User Selects Disappearance Reason (YouTube / Laptops / AI Tools / Startup / Comments / Other)
        |
AI Generates Sarcastic Roast Response -> Saved to database
        |
Daily Report Page: Adventure summary, analytics, achievements, AI summary
        |
Funny Reasons Page: AI-generated excuses for each unfinished task
```

**Note:** The prediction, dashboard, report, funny reasons, and disappearance pages currently contain hardcoded sample data in the HTML templates. The backend API endpoints exist and work, but the templates don't yet dynamically call the APIs to populate content. The JavaScript in `script.js` has the API integration functions, but they are not wired to the page templates via event handlers.

---

## 3. Current Features

### Frontend Features
- Glassmorphic dark theme UI with purple/blue gradient design system
- Responsive layout (mobile, tablet, desktop breakpoints)
- Chip-based selectors for mood (single-select) and interests (multi-select)
- Animated hero cards with floating animation
- Confidence meter with gradient progress bar
- Timeline journey visualization with step markers
- Modal overlay for disappearance popup
- Floating notification system (sarcastic random messages)
- Copy-to-clipboard functionality
- Template inheritance chain: `home/base.html` -> `procrastina_ai/base.html` -> page templates

### Backend Features
- Django 6.0.5 with SQLite database
- 3 database models with UUID primary keys
- 5 REST API endpoints returning JSON
- 7 page view endpoints rendering HTML
- CSRF token protection on all forms
- Session management via localStorage
- Django admin interface with custom fieldsets, filters, and search
- Environment variable support via python-dotenv

### AI Features
- Procrastination prediction generation (5-7 personalized steps)
- Sarcastic disappearance response generation (witty roasts)
- Daily report summary generation (3-4 sentence humorous analysis)
- Funny reasons generation (3-4 absurd excuses per task)
- All powered by OpenAI GPT-3.5-turbo with high temperature (0.8-0.9)

### Reporting Features
- Procrastination score calculation (0-100 formula)
- Tasks planned vs completed tracking
- Disappearance count tracking
- Most common excuse tracking
- AI-generated daily summary
- Achievement badges display

### User Interaction Features
- Setup form with text input + chip selectors
- Disappearance modal with radio options + custom text input
- Random sarcastic notifications on dashboard
- Copy and regenerate buttons on funny reasons

---

## 4. Pages and Routes

### `/projects/procrastina-ai/`
**Landing Page** (`templates/procrastina_ai/index.html`)
- Purpose: Introduce ProcrastinaAI and drive users to start
- Components: Hero section with CTA, 3 feature cards (Prediction, Missing Person Alerts, Daily Reports), AI roast card, footer link

### `/projects/procrastina-ai/setup/`
**Setup Page** (`templates/procrastina_ai/setup.html`)
- Purpose: Collect user's tasks, mood, and interests
- Components: Text input for tasks, chip group for mood (5 options), chip group for interests (7 options), custom text inputs, "Start My Day" submit button

### `/projects/procrastina-ai/prediction/`
**Prediction Page** (`templates/procrastina_ai/prediction.html`)
- Purpose: Show AI-generated procrastination journey
- Components: 94% confidence meter, 6-step timeline journey with markers, final "death" step, AI warning box, "Accept My Fate" CTA
- Note: Content is currently hardcoded sample data

### `/projects/procrastina-ai/dashboard/`
**Dashboard** (`templates/procrastina_ai/dashboard.html`)
- Purpose: Central hub showing procrastination stats
- Components: 4 stat cards (tasks, score, missing events, roasts), task list, recent excuses, AI responses, disappearance count, random sarcastic notifications
- Note: Content is currently hardcoded sample data

### `/projects/procrastina-ai/report/`
**Daily Report** (`templates/procrastina_ai/report.html`)
- Purpose: End-of-day procrastination analysis
- Components: Adventure timeline, analytics grid (4 cards), achievement badges (3), AI summary card, Export PDF / Share buttons
- Note: Content is currently hardcoded sample data

### `/projects/procrastina-ai/funny-reasons/`
**Funny Reasons** (`templates/procrastina_ai/funny_reasons.html`)
- Purpose: Show AI-generated excuses for each unfinished task
- Components: 4 task cards with reasons, copy-to-clipboard buttons, regenerate buttons
- Note: Content is currently hardcoded sample data

### `/projects/procrastina-ai/where-did-you-go/`
**Disappearance Modal** (`templates/procrastina_ai/disappearance.html`)
- Purpose: Ask where user went during procrastination, show AI response
- Components: Full-screen modal overlay, 6 radio options (YouTube/Laptops/AI Tools/Startup/Comments/Other), conditional custom text input, AI response card (shown after submit)
- Note: Uses hardcoded JavaScript responses, not the API endpoint

---

## 5. Database Structure

### Session Model

| Field | Type | Description |
|-------|------|-------------|
| id | UUIDField (PK) | Auto-generated UUID |
| mood | CharField(50) | Choices: motivated, sleepy, burned_out, lazy, existential_crisis |
| interests | JSONField | List of interests: ["YouTube", "AI", "Gaming"] |
| tasks | JSONField | List of tasks: ["Record Video", "Send Email"] |
| created_at | DateTimeField | Auto-set on creation |
| updated_at | DateTimeField | Auto-updated on save |

### Disappearance Model

| Field | Type | Description |
|-------|------|-------------|
| id | UUIDField (PK) | Auto-generated UUID |
| session | ForeignKey -> Session | CASCADE delete, related_name='disappearances' |
| disappearance_type | CharField(100) | Choices: youtube, laptops, ai_tools, startup, comments, other |
| custom_location | CharField(255) | Optional, for "other" type |
| ai_response | TextField | AI-generated witty response |
| created_at | DateTimeField | Auto-set on creation |

### Report Model

| Field | Type | Description |
|-------|------|-------------|
| id | UUIDField (PK) | Auto-generated UUID |
| session | ForeignKey -> Session | CASCADE delete, related_name='reports' |
| report_date | DateField | Auto-set on creation |
| tasks_planned | IntegerField | Number of planned tasks |
| tasks_completed | IntegerField | Number of completed tasks |
| total_disappearances | IntegerField | Count of disappearances |
| procrastination_score | IntegerField | 0-100 score |
| ai_summary | TextField | AI-generated report summary |
| created_at | DateTimeField | Auto-set on creation |

### Relationships

```
Session (1) ----> (N) Disappearance
Session (1) ----> (N) Report
```

### Data Flow

1. User submits setup form -> `Session` created with mood/interests/tasks
2. User triggers disappearance -> `Disappearance` created linked to Session with AI response
3. Day ends -> `Report` created linked to Session with stats and AI summary

---

## 6. Backend Architecture

### Views (`views.py`)
7 page views (render HTML) + 5 API views (return JSON). All function-based with `@require_http_methods` decorators. Page views simply render templates. API views parse JSON request bodies, validate fields, interact with models and services, and return structured JSON responses.

### Services (`services.py`)
4 AI generation functions that encapsulate all OpenAI interactions. Each constructs a personalized prompt, calls GPT-3.5-turbo, parses the response, and returns a standardized dict: `{'success': bool, 'data': ..., 'error': str}`.

### Models (`models.py`)
3 models handling all data persistence with UUID primary keys, JSON fields for flexible arrays, and foreign key relationships.

### Admin (`admin.py`)
Custom admin configuration for all 3 models with list displays, filters, search fields, readonly fields, collapsible fieldsets, and a computed `disappearances_count` method.

### URLs (`urls.py`)
Namespaced under `procrastina_ai`. 7 page routes + 5 API routes (prefixed with `api/`). Mounted at `/projects/procrastina-ai/` in the root URL conf.

### Architecture Diagram

```
User Browser
    |
Django URL Router (control_plus_why/urls.py)
    |
procrastina_ai/urls.py (namespaced routing)
    |
Page Views -> Render Templates (return HTML)
API Views -> Parse JSON -> Call Services -> Save Models -> Return JSON
    |
services.py (OpenAI API calls)
    |
models.py (database read/write)
```

No `forms.py` exists. Form handling is done manually in views via `json.loads(request.body)` for API views, and via HTML forms with chip selectors in templates.

---

## 7. AI Functionality

All AI features are in `services.py` using OpenAI GPT-3.5-turbo.

### Prediction Generation
- **Function:** `generate_prediction(mood, interests, tasks)`
- **Prompt:** Asks AI to generate a 5-7 step procrastination journey personalized to the user's mood, interests, and tasks
- **Temperature:** 0.8 (creative but somewhat focused)
- **Max tokens:** 300
- **Parsing:** Splits response by newline, strips numbered prefixes
- **Returns:** `{'success': True, 'data': [steps], 'confidence': 94}`

### Disappearance Response
- **Function:** `generate_disappearance_response(disappearance_type, custom_location, mood, interests)`
- **Prompt:** Asks AI for ONE witty, sarcastic 2-3 sentence roast about where user went
- **Temperature:** 0.9 (highly creative)
- **Max tokens:** 150
- **Returns:** `{'success': True, 'data': 'roast text'}`

### Daily Report
- **Function:** `generate_daily_report(tasks_planned, tasks_completed, disappearances, common_excuse)`
- **Prompt:** Asks AI for a 3-4 sentence humorous summary referencing the stats
- **Temperature:** 0.8
- **Max tokens:** 200
- **Score formula:** `max(0, min(100, 100 - (completed/planned)*50 + disappearances*3))`
- **Returns:** `{'success': True, 'data': 'summary', 'score': 87}`

### Funny Reasons
- **Function:** `generate_funny_reasons(task_name, mood)`
- **Prompt:** Asks AI for 3-4 absurd reasons to procrastinate on a specific task
- **Temperature:** 0.9
- **Max tokens:** 250
- **Parsing:** Splits by newline, strips dash prefixes. Falls back to raw text if parsing fails.
- **Returns:** `{'success': True, 'data': [reasons]}`

### Fallback Logic
- All functions wrap in try/except and return `{'success': False, 'error': str(e)}` on failure
- Funny reasons has a fallback: if parsed list is empty, returns the raw AI text as a single-item list
- The OpenAI client is initialized at module level with `os.getenv('OPENAI_API_KEY')` -- if the key is missing, all API calls will fail gracefully

---

## 8. Daily Report Generation

### Inputs

| Parameter | Type | Source |
|-----------|------|--------|
| tasks_planned | int | User input (from session data) |
| tasks_completed | int | User input (self-reported) |
| disappearances | int | Count of Disappearance records for session |
| common_excuse | str | Most frequent disappearance_type or user input |

### Processing Steps

1. Construct prompt with stats embedded
2. Call OpenAI GPT-3.5-turbo (temperature 0.8, max 200 tokens)
3. Parse response text as AI summary
4. Calculate procrastination score: `100 - (completed/planned)*50 + disappearances*3` (clamped 0-100)
5. Save Report record linked to Session

### Output Structure

```json
{
  "success": true,
  "data": {
    "reportId": "uuid",
    "sessionId": "uuid",
    "tasksPlanned": 4,
    "tasksCompleted": 1,
    "totalDisappearances": 7,
    "procrastinationScore": 87,
    "aiSummary": "Today's adventure: you planned 4 tasks...",
    "date": "2026-06-04"
  }
}
```

### Sample Report (from hardcoded template)

> *"You attempted to build a website. You accidentally became a laptop consultant. By the way, did you know the 27th laptop model has a really good display? You do now."*
>
> Stats: 4 planned, 1 completed, 7 disappearances, most common excuse: "Need coffee"
> Achievements: Opened 50 Tabs, Professional Researcher, Elite Procrastinator

---

## 9. Missing Person System

### How inactivity is detected
**Currently: not automated.** The disappearance modal is a standalone page at `/projects/procrastina-ai/where-did-you-go/` that can be navigated to directly. There is no inactivity timer or automatic trigger in the current codebase. The dashboard and `script.js` reference a `setupDisappearanceModal()` function, but there is no automatic popup after idle time.

### How reasons are collected
The `disappearance.html` template shows a modal with 6 radio options:
- Watching YouTube
- Looking At Laptops
- Researching AI Tools
- Planning A Startup
- Reading Comments
- Other (shows custom text input)

### How responses are generated
**Two systems exist but are not connected:**
1. **Template-level:** The disappearance page has hardcoded JavaScript responses for each option (lines 69-76 in `disappearance.html`)
2. **API-level:** The `api_save_disappearance` endpoint calls `generate_disappearance_response()` which uses OpenAI to generate a personalized roast

The template currently uses the hardcoded responses, not the API.

### How events are stored
When the API endpoint is used, a `Disappearance` record is created with:
- FK to the current Session
- The selected disappearance_type
- Optional custom_location
- AI-generated response text
- Timestamp

---

## 10. Folder Structure

```
procrastina_ai/
|-- __init__.py
|-- admin.py
|-- apps.py
|-- models.py
|-- services.py
|-- tests.py
|-- urls.py
|-- views.py
|-- static/
|   +-- procrastina_ai/
|       |-- script.js
|       +-- style.css
+-- templates/
    +-- procrastina_ai/
        |-- base.html
        |-- index.html
        |-- setup.html
        |-- prediction.html
        |-- dashboard.html
        |-- report.html
        |-- funny_reasons.html
        +-- disappearance.html
```

Note: The `migrations/` directory does not yet exist. It will be created when `python manage.py makemigrations` is first run.

---

## 11. File Responsibilities

### `models.py`
- **Purpose:** Database schema definition
- **Contains:** Session, Disappearance, Report models with UUID PKs, JSON fields, FKs
- **Connects to:** views.py (data read/write), admin.py (admin display), services.py (no direct link)

### `views.py`
- **Purpose:** HTTP request handling -- both page rendering and API logic
- **Contains:** 7 page views + 5 API endpoints with full docstrings
- **Connects to:** models.py (imports Session, Disappearance, Report), services.py (imports all 4 AI functions), urls.py (referenced by name)

### `services.py`
- **Purpose:** AI business logic, isolated from HTTP layer
- **Contains:** 4 functions using OpenAI client, prompt engineering, response parsing
- **Connects to:** views.py (called by API views), OpenAI API (external)

### `urls.py`
- **Purpose:** URL routing for all procrastina_ai endpoints
- **Contains:** 12 URL patterns (7 pages + 5 API), app_name namespace
- **Connects to:** views.py (imports all view functions), control_plus_why/urls.py (included via `include()`)

### `admin.py`
- **Purpose:** Django admin panel configuration
- **Contains:** 3 admin classes with custom list_display, list_filter, search_fields, fieldsets
- **Connects to:** models.py (registers all 3 models)

### `apps.py`
- **Purpose:** Django app metadata
- **Contains:** `ProcrastinaAiConfig` with verbose_name = 'ProcrastinaAI'
- **Connects to:** Django's app registry

### `static/procrastina_ai/script.js`
- **Purpose:** Frontend interactivity and API integration
- **Contains:** API request helper with CSRF, session management (localStorage), chip selection handler, functions for all 5 API calls + display helpers, notification system, copy-to-clipboard, disappearance modal handler, `window.procrastinaAI` global object
- **Connects to:** All API endpoints (via fetch), base.html (loaded via `<script>` tag)

### `static/procrastina_ai/style.css`
- **Purpose:** Complete visual design system
- **Contains:** CSS custom properties, glassmorphic dark theme, responsive grid layouts, chip selectors, stat cards, timeline, modal overlay, animations (float, slideDown, modalSlideIn), notification styles, 2 media query breakpoints
- **Connects to:** All templates (loaded via base.html `<link>` tag)

### `templates/procrastina_ai/base.html`
- **Purpose:** Layout wrapper for all ProcrastinaAI pages
- **Contains:** Extends `home/base.html`, loads style.css + script.js, wraps content in `.pa-container`
- **Connects to:** home/base.html (parent template), all page templates (children)

### `templates/procrastina_ai/index.html`
- **Purpose:** Landing page with hero section and feature showcase
- **Contains:** Hero with CTA to setup, 3 feature cards, AI roast card, footer link to report

### `templates/procrastina_ai/setup.html`
- **Purpose:** User onboarding form
- **Contains:** Task text input, mood chip group (5 options), interest chip group (7 options), custom text inputs, CSRF token, submit button

### `templates/procrastina_ai/prediction.html`
- **Purpose:** Display AI procrastination journey
- **Contains:** Confidence meter (94%), 6-step timeline with markers, final skull marker, AI warning box

### `templates/procrastina_ai/dashboard.html`
- **Purpose:** Central stats hub
- **Contains:** 4 stat cards, task list, excuse list, AI response boxes, disappearance count, inline script for random sarcastic notifications

### `templates/procrastina_ai/report.html`
- **Purpose:** Daily procrastination analysis
- **Contains:** Adventure timeline, analytics grid, achievement badges, AI summary card, export/share buttons

### `templates/procrastina_ai/funny_reasons.html`
- **Purpose:** AI excuses for unfinished tasks
- **Contains:** 4 task cards with reasons, inline copy-to-clipboard script, regenerate buttons

### `templates/procrastina_ai/disappearance.html`
- **Purpose:** Missing person modal + AI response
- **Contains:** Full-screen modal with radio options, conditional custom input, inline JS for hardcoded responses and form handling, response card

### `tests.py`
- **Purpose:** Test file (currently empty/default)

---

## 12. Cleanup Suggestions

### Unused / Non-Functional Code
1. **Tests are empty** -- `tests.py` has no test cases
2. **`style.css` has massive duplication** -- Lines 1562-1805 duplicate earlier styles (hero-landing, hero-copy, eyebrow, etc.) that already exist at lines 182-380. About 243 lines of redundant CSS.
3. **`script.js` `setupDisappearanceModal()`** is defined but the `disappearance.html` template has its own inline script that handles the form independently, making the script.js version unused
4. **Dashboard inline script** duplicates the notification logic that already exists in `script.js` (`showNotification`)

### Templates Not Connected to APIs
5. **All page templates (except setup.html) use hardcoded data** -- prediction.html, dashboard.html, report.html, funny_reasons.html, and disappearance.html all contain static sample content instead of dynamically calling the API endpoints. The API functions exist in script.js but are not wired to the templates.

### Missing CSRF Handling
6. **API views lack `@csrf_exempt`** -- The POST API endpoints use `@require_http_methods(["POST"])` but do not include `@csrf_exempt`. The script.js sends CSRF tokens, but if called from external tools (Postman, curl) or if the CSRF token is not present, requests will return 403.

### Model Choices Mismatch
7. **Disappearance type choices do not match template values** -- Model has `'ai_tools'` but template uses `'ai-tools'` (hyphen vs underscore). Same for disappearance form values vs model choices.

### Missing Migrations
8. **No migrations directory** -- `procrastina_ai/migrations/` does not exist yet. Running `makemigrations` will create it, but it should be tracked in git.

### Refactoring Opportunities
9. **Extract inline scripts from templates** -- `dashboard.html`, `funny_reasons.html`, and `disappearance.html` all have inline `<script>` blocks that should be moved to script.js or separate JS files
10. **Wire templates to actual APIs** -- The biggest gap: connect prediction.html, dashboard.html, report.html, funny_reasons.html, and disappearance.html to call the real API endpoints and display dynamic data
11. **Add form validation** -- Setup form has no client-side validation beyond `required` attribute
12. **Centralize notification messages** -- Sarcastic messages are hardcoded in dashboard.html; could be stored in a constant or fetched from backend

---

## 13. Future Improvements

### Immediate (Wire APIs to Templates)
- Connect `prediction.html` to call `generate-prediction` API on page load and render steps dynamically
- Connect `dashboard.html` to fetch real session data and populate stats
- Connect `report.html` to call `generate-report` API and display actual AI summary
- Connect `funny_reasons.html` to call `generate-funny-reasons` API per task
- Connect `disappearance.html` to use `save-disappearance` API instead of hardcoded responses
- Fix the `ai_tools` vs `ai-tools` mismatch between model choices and form values

### Short-Term
- Add an inactivity timer that automatically triggers the disappearance modal after X minutes of no interaction
- Add session persistence across page navigation (read session data from localStorage on every page)
- Add proper error states and loading spinners for API calls
- Write unit tests for models, services, and views
- Add rate limiting on API endpoints to control OpenAI costs
- Create actual migrations and commit them

### Medium-Term
- Add user authentication so sessions persist across visits
- Add historical data view (past sessions, reports, disappearances)
- Add shareable report cards (generate image/PDF from report data)
- Add email delivery of daily reports
- Add task completion tracking (mark tasks as done/ignored)
- Add streak tracking (days of elite procrastination)

### Long-Term
- Add a leaderboard (highest procrastination scores)
- Add social sharing of AI roasts
- Add multiple AI model support (let users pick GPT-4 for premium roasts)
- Add browser extension that detects procrastination in real-time
- Add team/org mode ("your team's procrastination report")
- Add export functionality (PDF reports, shareable links)
