# Ctrl+Why — Beginner's Guide

> This guide is written for **anyone** — no coding experience needed.
> If you already know Python and Django, check out `procrastina_ai/DOCUMENTATION.md` instead.

---

## What is Ctrl+Why?

**Ctrl+Why** is a fun, experimental website that builds "useless" software with serious engineering. Think of it as a playground for absurd ideas — emotionally unstable chatbots, unnecessary AI tools, and overengineered solutions to problems that don't exist.

The motto: *"We build useless products with serious engineering. Some are funny. Some accidentally become useful. Most probably shouldn't exist."*

---

## What is ProcrastinaAI?

**ProcrastinaAI** is the first project on Ctrl+Why. It's a web app that:

1. **Predicts how you'll procrastinate** — You tell it your mood, interests, and tasks. It uses real AI to predict exactly how you'll waste your day.

2. **Tracks your distractions** — A desktop agent auto-detects when you go idle for 10+ minutes and silently creates a "pending disappearance". No immediate popup — you explain it later at your convenience. You can pick a reason (and get an AI roast) or let it "Remain A Mystery".

3. **Tracks real browser activity** — While you're on the dashboard, it tracks your actual mouse movements, clicks, and keystrokes to measure active vs idle time.

4. **Desktop Agent (Windows)** — An optional Python desktop agent can run alongside you, tracking which applications you use (VS Code, Chrome, Spotify, etc.), detecting idle periods, and building an accurate activity timeline. The data appears in your end-of-day report. The agent auto-disconnects when you click "Stop My Day" — no need to stop it manually.

5. **Pending Explanation Queue** — When the agent detects you've been idle for 10+ minutes, a pending disappearance is created silently in the background. A "🕵️ Unexplained: N" badge appears on the dashboard. You can review pending disappearances whenever you want, or wait until you click "Stop My Day" — which blocks until all are resolved. Each one can be explained (AI reaction generated) or left as a mystery.

6. **Generates a daily report** — When you click "Stop My Day" (after reviewing your tasks), the agent auto-disconnects and you get a report with real metrics (session length, active time, idle time), an explained vs unexplained breakdown, longest disappearance, average duration, Task Completion Summary with progress bar, What Happened To The Day analytics, a procrastination score (0–100), achievements, and an AI-written summary that references your explanation patterns and completion percentage.

7. **Makes excuses for you** — For every task you didn't finish (In Progress, Partially Completed, Abandoned, Never Started), the AI generates absurd but oddly convincing reasons why you shouldn't have done it anyway. Completed tasks show a ✅ badge — no excuses needed.

8. **Session Recovery** — If you close the browser accidentally, the app remembers your session. On your next visit, it checks the server and restores your active session so you don't lose progress.

**Example:**
> You planned to "Record Video". The AI says:
> - "Your webcam needs to rest before its big debut"
> - "The lighting in your room is in a union dispute"
> - "Your voice is on a spiritual retreat"

It's a joke, but built with real technology.

---

## What Does It Look Like?

### The Main Website (Ctrl+Why)
- **Dark theme** with a modern, clean design
- A homepage showing all projects (ProcrastinaAI is the first, others are "Coming Soon")
- An About page explaining the philosophy behind Ctrl+Why

### ProcrastinaAI
- **Premium dark design** — inspired by Linear, Arc, and Raycast with warm amber accents
- **PA brand logo** — A progress circle permanently stuck at 87%
- **Premium navigation** — Logo left, navigation center, actions right; hamburger menu on mobile
- **Setup page** — Type tasks, click mood chips (7 options + custom input), click interest chips (7 options + add custom interests as tags)
- **Prediction page** — Shows a full-day procrastination forecast: journey timeline with durations and risk/recovery probabilities, natural breaks (coffee, lunch, existential crisis), forecast metrics (productivity, distraction, completion scores), and AI warnings
- **Dashboard** — Status bar (day active, tasks, distractions, top excuse), centered floating "I Got Distracted" button, stats grid, task list, leaderboard, AI observations
- **Report page** — Gated until you click "Stop My Day". Shows session length, active/idle time, distractions, procrastination score, achievements, AI summary
- **Funny Reasons page** — Cards showing AI-generated excuses for each task, with copy and regenerate buttons

---

## How to Run the Project

### What You Need First
- **Python** (version 3.10 or newer) — Download from [python.org](https://www.python.org/downloads/)
- **An OpenRouter API key** (free) — This powers the AI features. Get one at [openrouter.ai/keys](https://openrouter.ai/keys)

### Step-by-Step Setup

#### Step 1: Download the project
Download or clone the project folder to your computer. Open a terminal (called "Command Prompt" or "PowerShell" on Windows, "Terminal" on Mac).

Navigate to the project folder:
```
cd path/to/control-plus-why
```

#### Step 2: Create a virtual environment
A **virtual environment** is like a private space for this project's Python packages, so they don't interfere with other projects on your computer.

```
python -m venv venv
```

Then **activate** it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You'll know it worked because your terminal prompt will show `(venv)` at the beginning.

#### Step 3: Install the required packages
```
pip install -r requirements.txt
```
This installs Django (the web framework), OpenAI SDK (used to talk to OpenRouter), and python-dotenv (for reading settings).

#### Step 4: Create your settings file
Create a file named `.env` in the project root (same folder as `manage.py`). Add this line:
```
OPENAI_API_KEY=sk-or-v1-your-actual-openrouter-key-here
```
Replace the value with your real OpenRouter API key.

**Why the name `OPENAI_API_KEY`?** The app uses the OpenAI Python SDK pointed at OpenRouter's API. The SDK looks for this exact variable name. The key itself is from OpenRouter (free).

**Don't have a key?** The app still works — pages will load, but AI features (predictions, roasts, reports, excuses) will show fallback messages.

#### Step 5: Set up the database
```
python manage.py makemigrations
python manage.py migrate
```
This creates the database tables. Think of it as telling the app "set up your memory so you can remember user data."

#### Step 6: (Optional) Create an admin account
```
python manage.py createsuperuser
```
Follow the prompts. This lets you access the admin panel where you can view all saved data (sessions, disappearances, reports, activity tracking data).

#### Step 7: Start the server
```
python manage.py runserver
```

#### Step 8: Open your browser
Go to these addresses:

| What | Address |
|------|---------|
| Main website | http://127.0.0.1:8000/ |
| About page | http://127.0.0.1:8000/about/ |
| ProcrastinaAI | http://127.0.0.1:8000/projects/procrastina-ai/ |
| Admin panel | http://127.0.0.1:8000/admin/ |

To stop the server, press `Ctrl + C` in the terminal.

---

## How to Use ProcrastinaAI

1. Go to http://127.0.0.1:8000/projects/procrastina-ai/
2. Click **"Start My Day"**
3. On the Setup page:
   - Type your tasks (e.g., "Record Video, Send Email, Code Review")
   - Click your mood (Motivated, Sleepy, Burned Out, Lazy, Focused, Confused, Chaotic) — or type a custom mood
   - Click your interests (YouTube, AI, Gaming, Movies, Tech, Instagram, Startups) — or press Enter to add custom interests as tags
4. Click **"Start My Day"** to submit — the desktop agent is automatically launched in the background
5. You'll see an AI **Forecast** of your entire workday — a journey with durations, distraction risks, natural breaks, and funny metrics like "Chance of Finishing Every Task: 21%"
6. Click "Accept My Fate" to go to the **Dashboard**
7. If the desktop agent connected successfully, the agent panel shows **CONNECTED** and the "I Got Distracted" button is hidden. The agent now tracks your active windows automatically.
8. **Work normally.** The agent monitors your activity. After 10 minutes of no keyboard/mouse input, a **pending disappearance** is silently created in the background (no popup).
9. A **"🕵️ Unexplained: N"** badge appears on the dashboard status bar. You can click **"🕵️ Review Unexplained"** at any time to open the resolution modal.
10. In the modal, each pending disappearance shows its **duration** and **last active app**. You can:
    - **Explain**: Pick a reason (or type a custom one) → AI generates a humorous reaction → saved as [EXPLAINED]
    - **Remain A Mystery**: Skip it → marked as [UNEXPLAINED]
11. This cycle repeats throughout the day — work, go idle, return, explain (or not).
12. If the agent is unavailable, the dashboard shows **"Desktop Agent Not Connected — Manual Mode"** and the "I Got Distracted" button appears as a fallback.
13. When you're done for the day, click **"Stop My Day"** — if pending disappearances exist, you'll be asked to resolve them first. After all resolved, the **Task Review Modal** appears — mark each task as Completed, In Progress, Partially Completed, Abandoned, or Never Started.
14. After reviewing tasks, the session ends and you're redirected to your **Report**
15. Your report shows real metrics: session length, active time, idle time, disappearances, **explained vs unexplained breakdown**, longest disappearance, average duration, most common reason, focus changes, top applications, **Task Completion Summary with progress bar**, **What Happened To The Day analytics**, score, achievements, and AI summary
16. View **Funny Reasons** — completed tasks show a ✅ badge, AI-generated excuses only for incomplete tasks with status badges on every card

---

## Using the Desktop Agent

The desktop agent is a Python program that runs on your Windows computer and tracks which applications you use in real time. It is **automatically launched** when you click "Start My Day" — no manual setup required. It sends data to the ProcrastinaAI backend, which enriches your dashboard and report with actual app usage.

### What It Tracks
- **Active application** — which app is currently focused (VS Code, Chrome, Spotify, etc.)
- **Window title** — the full title text (e.g., `views.py — procrastina_ai - Visual Studio Code`)
- **Application switching** — every time you switch apps
- **Idle periods** — when you haven't touched keyboard/mouse for 10+ minutes

### What It Does NOT Track
No passwords, typed text, clipboard, screenshots, files, or browser history.

### How It Works (Automatic)

1. You click "Start My Day" on the Setup page
2. The session is created and the agent is **auto-launched** as a background subprocess
3. The agent connects to the backend and starts tracking your active windows
4. The dashboard shows **CONNECTED** in the agent panel
5. When you click "Stop My Day", the agent is **auto-disconnected** and its process is terminated

### Manual Agent Launch (Fallback)

If auto-launch fails, you can manually start the agent:

1. Open a second terminal (keep the Django server running in the first one)
2. Navigate to the agent folder and install its dependencies:
   ```
   cd procrastina_agent
   pip install -r requirements.txt
   ```
3. Start a session in the browser ("Start My Day")
4. Get your session ID from browser DevTools (F12) → Console:
   ```
   JSON.parse(localStorage.getItem('procrastina_ai_session')).sessionId
   ```
5. Run the agent with the session ID:
   ```
   python agent.py 550e8400-e29b-41d4-a716-446655440000
   ```
6. Use your computer normally. The agent runs silently in the terminal.
7. The agent **auto-disconnects** when you click "Stop My Day" in the browser — no need to manually `Ctrl+C` first. If you do `Ctrl+C`, it shuts down gracefully too.

### Example Output
```
21:30:02 [INFO] Initial focus: code.exe — views.py — procrastina_ai - Visual Studio Code
21:32:10 [INFO] Focus Changed: code.exe -> chrome.exe (after 128s)
21:34:55 [INFO] Focus Changed: chrome.exe -> spotify.exe (after 165s)
21:40:00 [INFO] Idle Started at 21:40:00 (last app: spotify.exe)
21:52:30 [INFO] Idle Ended at 21:52:30 (duration: 750s)
```

### Report With Agent Data
When the desktop agent sends data, your report additionally shows:
- **Top Applications** — ranked by time spent (e.g., VS Code: 42 min, Chrome: 27 min)
- **Category Breakdown** — Development: 45%, Entertainment: 20%, Communication: 15%
- **Idle Summary** — each idle period with duration and last active app
- **Activity Timeline** — chronological flow (VS Code → Chrome → Idle → VS Code)
- **Disappearances** — each disappearance with [EXPLAINED] or [MYSTERY] badge and AI reaction
- **Explained vs Unexplained** — count cards showing how many you explained vs left as mysteries
- **Longest Disappearance** — the longest idle period detected
- **Average Duration** — average idle duration across all disappearances
- **Focus Changes** — total number of app switches during the session
- **Most Common Reason** — the distraction type that appeared most often

---

## How Report Gating Works

The report is **locked** until you click "Stop My Day". This means:

- While your day is active: The Report link is hidden from navigation
- If you try to visit `/report/` directly: You see "Your day is still running. Finish your procrastination journey first."
- After clicking "Stop My Day": Session ends, report unlocks, you're auto-redirected to the report page
- The report shows a "Session Closed — You survived another day" badge

---

## Troubleshooting

### "python is not recognized"
Python isn't installed or isn't in your system PATH. Reinstall from [python.org](https://www.python.org/downloads/) and make sure to check "Add Python to PATH" during installation.

### "No module named django"
You forgot to activate the virtual environment or install the requirements. Run:
```
venv\Scripts\activate
pip install -r requirements.txt
```

### AI features return errors
- Check that your `.env` file exists and has a valid OpenRouter API key
- Free models on OpenRouter can be rate-limited — the app automatically tries 4 different models in order
- The app still works without the API key — pages load, but AI features show fallback messages

### "Port 8000 is already in use"
Another program is using port 8000. Either close that program or run on a different port:
```
python manage.py runserver 8080
```
Then visit http://127.0.0.1:8080/ instead.

### Database errors
If you see "no such table" errors, you forgot to run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

### "Activity data insufficient" on report
This means you spent less than 30 seconds on the dashboard before ending your day. The browser activity tracker needs at least 30 seconds of detected activity to show metrics. Just use the app normally and it'll collect data.

---

## Project Structure (Simplified)

```
control-plus-why/
│
├── manage.py              ← The "on/off switch" for Django commands
├── requirements.txt       ← List of packages the project needs
├── .env                   ← Your secret settings (OpenRouter API key)
│
├── control_plus_why/      ← Django's main settings folder
│   ├── settings.py        ← App configuration (which apps to load, database type)
│   └── urls.py            ← The "map" — which URLs go to which pages
│
├── home/                  ← The main website (homepage + about page)
│   ├── views.py           ← What happens when you visit / or /about/
│   ├── templates/         ← The HTML files
│   └── static/            ← CSS and images
│
├── procrastina_agent/     ← The Windows desktop agent (optional)
│   ├── agent.py           ← Main program — run this to start tracking
│   ├── tracker.py         ← Reads active window info
│   ├── idle_detector.py   ← Detects idle periods
│   ├── api_client.py      ← Talks to the Django backend
│   ├── config.py          ← Settings you can change
│   └── README.md          ← Agent-specific instructions
│
└── procrastina_ai/        ← The ProcrastinaAI project
    ├── models.py          ← Database structure (8 models)
    ├── views.py           ← Page views + API endpoints
    ├── services.py        ← AI functions (talks to OpenRouter)
    ├── activity_services.py ← Activity tracking service layer
    ├── desktop_integration.py ← Validates and normalizes agent data
    ├── urls.py            ← All page and API routes (28 endpoints)
    ├── admin.py           ← Admin panel configuration
    ├── tests/             ← Test suite (39 tests across 5 files)
    ├── templates/         ← HTML files for each page
    ├── static/            ← CSS styles + JavaScript
    ├── docs/              ← Technical documentation (DOCUMENTATION.md, GETTING_STARTED.md)
    └── migrations/        ← Database migration files
```

---

## Glossary

| Term | Plain English |
|------|---------------|
| **Python** | A programming language. This project is built with it. |
| **Django** | A web framework for Python. It handles pages, databases, and URLs. |
| **API** | A way for programs to talk to each other. The website sends data to AI and gets responses back. |
| **OpenRouter** | A free API that gives access to multiple AI models (Google, Meta, NVIDIA). We use it instead of paying for OpenAI directly. |
| **API Key** | A secret password that lets this project use the AI. OpenRouter keys are free. |
| **Virtual Environment** | A private folder for this project's Python packages. Keeps things organized. |
| **pip** | Python's package installer. Like an app store for Python tools. |
| **Database** | Where the app stores data (sessions, distractions, reports). This project uses SQLite. |
| **Migration** | Telling the database to create or update its tables. Run `makemigrations` then `migrate`. |
| **Template** | An HTML file that defines what a web page looks like. |
| **Static Files** | CSS (styles), JavaScript (interactivity), and images. |
| **Session** | A record of one user's procrastination journey (mood, tasks, interests, distractions). |
| **Disappearance** | A record of where a user went when they got distracted. |
| **Report** | A daily summary with real metrics, score, and AI-written analysis. |
| **Activity Tracker** | JavaScript module that detects real browser activity (mouse, clicks, keyboard, scroll) and sends a heartbeat every 30 seconds. |
| **AgentPoller** | JavaScript module that polls the server every 15 seconds to check if the desktop agent is connected and to detect idle-return transitions. |
| **SessionRecovery** | JavaScript module that restores an active session from the server if the browser was closed or the page was refreshed. |
| **Idle-Return Popup** | A modal that appears when the agent detects the user returning from an idle period (10+ minutes away). Asks where they went with AI-generated options. |
| **Pending Explanation Queue** | The system of auto-detected disappearances that sit as "pending" until the user explains them or marks them as a mystery. |
| **Report Gating** | The report is locked until "Stop My Day" is clicked. Prevents premature report access. |
| **Stop My Day Blocking** | When pending disappearances exist, "Stop My Day" is blocked until all are resolved (explained or skipped). |
| **CSRF Token** | A security check that prevents other websites from making fake requests. |
| **JSON** | A data format like `{"key": "value"}`. Used for sending data between browser and server. |
| **UUID** | A unique ID like `a1b2c3d4-e5f6-7890-abcd-ef1234567890`. Every record gets one. |
| **Superuser** | An admin account that can access the `/admin/` panel. |
| **Activity Session** | A tracking connection from the desktop agent. Stores events, app usage, and idle periods. |
| **Desktop Agent** | A Python program (`procrastina_agent/`) that runs on Windows and tracks which apps you use. Optional. |
| **Idle Period** | A stretch of time (5+ minutes) where no keyboard or mouse input was detected. |

---

## Need More Technical Details?

Read the full developer documentation at: `procrastina_ai/DOCUMENTATION.md`

It covers:
- Complete database schema (8 models)
- All 28 API endpoints with descriptions
- AI configuration and model fallback chain (5 AI functions)
- Backend architecture and service layers
- Activity tracking system and desktop agent
- Pending Explanation Queue workflow
- Session recovery
- Desktop agent architecture and file reference

For the desktop agent usage and setup: `procrastina_agent/README.md`
