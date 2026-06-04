# ProcrastinaAI™ - Complete Django Backend Setup Guide

**Everything is now consolidated in the `procrastina_ai` Django app!**

## 📁 Project Structure

All code stays inside the `procrastina_ai` app:

```
procrastina_ai/
├── models.py              ✅ Database models (Session, Disappearance, Report)
├── views.py               ✅ Page views + API endpoints (JSON)
├── urls.py                ✅ URL routing
├── services.py            ✅ AI generation functions
├── admin.py               ✅ Django admin config
├── apps.py                ✅ App configuration
├── migrations/            ✅ Database migrations
├── static/procrastina_ai/
│   ├── style.css          ✅ All styling (glassmorphism, dark theme)
│   └── script.js          ✅ Frontend + API integration
└── templates/procrastina_ai/
    ├── base.html          ✅ Layout wrapper
    ├── index.html         ✅ Landing page
    ├── setup.html         ✅ Setup form
    ├── prediction.html    ✅ Prediction timeline
    ├── dashboard.html     ✅ Dashboard
    ├── report.html        ✅ Daily report
    ├── funny_reasons.html ✅ Funny reasons
    └── disappearance.html ✅ Disappearance modal
```

## 🚀 Quick Start (5 Steps)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Django 6.0.5+
- OpenAI 4.28.0+
- python-dotenv 1.0.0+

### Step 2: Create .env File

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Get your OpenAI key from: https://platform.openai.com/api-keys

### Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the database tables:
- `procrastina_ai_session` - User sessions
- `procrastina_ai_disappearance` - Disappearances
- `procrastina_ai_report` - Daily reports

### Step 4: Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

Then visit `http://localhost:8000/admin` to manage data.

### Step 5: Start the Server

```bash
python manage.py runserver
```

Server runs at: http://localhost:8000

Visit: http://localhost:8000/projects/procrastina-ai/

## 📚 Database Models

### Session Model
Stores user session data:
- **mood** - User's mood (motivated, sleepy, lazy, etc.)
- **interests** - JSON array of user interests
- **tasks** - JSON array of tasks user planned
- **created_at** / **updated_at** - Timestamps

```python
session = Session.objects.create(
    mood='sleepy',
    interests=['YouTube', 'AI', 'Gaming'],
    tasks=['Record Video', 'Send Email']
)
```

### Disappearance Model
Tracks where user went during procrastination:
- **session** - Foreign key to Session
- **disappearance_type** - Type: youtube, ai_tools, startup, etc.
- **custom_location** - Custom text if "other" selected
- **ai_response** - AI-generated witty response
- **created_at** - Timestamp

### Report Model
Stores daily procrastination reports:
- **session** - Foreign key to Session
- **report_date** - Date of report
- **tasks_planned** / **tasks_completed** - Task counts
- **total_disappearances** - Count of disappearances
- **procrastination_score** - 0-100 score
- **ai_summary** - AI-generated summary
- **created_at** - Timestamp

## 🔌 API Endpoints

All endpoints are inside the `procrastina_ai` app, return JSON only.

### 1. Create Session
**POST** `/projects/procrastina-ai/api/create-session/`

Create a new user session.

**Request:**
```json
{
  "mood": "sleepy",
  "interests": ["YouTube", "AI", "Gaming"],
  "tasks": ["Record Video", "Send Email", "Code Review"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessionId": "uuid-here",
    "mood": "sleepy",
    "interests": ["YouTube", "AI", "Gaming"],
    "tasks": ["Record Video", "Send Email", "Code Review"],
    "message": "Session created successfully"
  }
}
```

### 2. Generate Prediction
**POST** `/projects/procrastina-ai/api/generate-prediction/`

Generate AI procrastination prediction.

**Request:**
```json
{
  "sessionId": "uuid-from-create-session",
  "mood": "sleepy",
  "interests": ["YouTube", "AI", "Gaming"],
  "tasks": ["Record Video", "Send Email"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessionId": "uuid",
    "prediction": [
      "Open email, immediately distracted",
      "Check YouTube for inspiration",
      "Find AI video, watch for 2 hours",
      "Research GPT-5 theories"
    ],
    "confidence": 94
  }
}
```

### 3. Save Disappearance
**POST** `/projects/procrastina-ai/api/save-disappearance/`

Track where user disappeared and get AI response.

**Request:**
```json
{
  "sessionId": "uuid",
  "disappearanceType": "youtube",
  "customLocation": null,
  "mood": "sleepy",
  "interests": ["YouTube"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "disappearanceId": "uuid",
    "sessionId": "uuid",
    "disappearanceType": "youtube",
    "aiResponse": "Ah yes, the classic YouTube rabbit hole..."
  }
}
```

### 4. Generate Report
**POST** `/projects/procrastina-ai/api/generate-report/`

Generate daily procrastination report with AI summary.

**Request:**
```json
{
  "sessionId": "uuid",
  "tasksPlanned": 4,
  "tasksCompleted": 1,
  "disappearances": 7,
  "commonExcuse": "Researching workflow"
}
```

**Response:**
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
    "date": "2024-06-04"
  }
}
```

### 5. Generate Funny Reasons
**POST** `/projects/procrastina-ai/api/generate-funny-reasons/`

Generate funny reasons to procrastinate on a task.

**Request:**
```json
{
  "sessionId": "uuid",
  "taskName": "Record Video",
  "mood": "motivated"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessionId": "uuid",
    "taskName": "Record Video",
    "reasons": [
      "Your lighting needs a complete overhaul...",
      "The camera probably needs 47 software updates...",
      "You have 73 browser tabs about cinematography..."
    ]
  }
}
```

## 🤖 Services Module (services.py)

All AI generation functions are in `services.py`:

```python
from procrastina_ai.services import (
    generate_prediction,           # Generate procrastination journey
    generate_disappearance_response,  # Generate AI roast
    generate_daily_report,         # Generate daily summary
    generate_funny_reasons         # Generate funny excuses
)

# All functions use OpenAI gpt-3.5-turbo model
# All return {'success': bool, 'data': ..., 'error': str}

result = generate_prediction('sleepy', ['YouTube'], ['Work'])
if result['success']:
    print(result['data'])  # Array of prediction steps
```

### Function Signatures

```python
# Generate procrastination prediction
generate_prediction(mood, interests, tasks)
# Returns: {'success': bool, 'data': list, 'confidence': int}

# Generate disappearance response
generate_disappearance_response(disappearance_type, custom_location, mood, interests)
# Returns: {'success': bool, 'data': str}

# Generate daily report
generate_daily_report(tasks_planned, tasks_completed, disappearances, common_excuse)
# Returns: {'success': bool, 'data': str, 'score': int}

# Generate funny reasons
generate_funny_reasons(task_name, mood)
# Returns: {'success': bool, 'data': list}
```

## 📖 Frontend Integration

The `script.js` file has all frontend functions to call the APIs:

```javascript
// Available functions in window.procrastinaAI object

// Create session
await procrastinaAI.createNewSession(mood, interests, tasks);

// Generate prediction
const result = await procrastinaAI.generateProcrastinationPrediction(mood, interests, tasks);
procrastinaAI.displayPredictionSteps(result.steps);

// Save disappearance
const response = await procrastinaAI.saveDisappearance(type, location, mood, interests);
procrastinaAI.displayDisappearanceResponse(response.aiResponse);

// Generate report
const report = await procrastinaAI.generateDailyReport(planned, completed, disappearances, excuse);
procrastinaAI.displayReportSummary(report);

// Generate funny reasons
const reasons = await procrastinaAI.generateFunnyReasons(taskName, mood);
procrastinaAI.displayFunnyReasons(taskName, reasons);

// Utilities
procrastinaAI.copyToClipboard(text);
procrastinaAI.showNotification(message, type);
procrastinaAI.getSessionId();
procrastinaAI.clearSession();
```

## 💾 Database Design

### Relationships

```
User Session
    ↓
    ├─→ Disappearance(s)
    │   └─→ AI Response
    │
    └─→ Report(s)
        ├─→ Statistics
        └─→ AI Summary
```

### Example Data Flow

```python
# 1. Create session
session = Session.objects.create(
    mood='sleepy',
    interests=['YouTube', 'AI'],
    tasks=['Record', 'Email']
)

# 2. Save disappearances
Disappearance.objects.create(
    session=session,
    disappearance_type='youtube',
    ai_response='Witty AI response here...'
)

# 3. Create report
Report.objects.create(
    session=session,
    tasks_planned=2,
    tasks_completed=1,
    total_disappearances=3,
    procrastination_score=85,
    ai_summary='Daily summary here...'
)
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (Django settings)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### settings.py Changes

The `settings.py` has been updated to:
1. Load `.env` file with `python-dotenv`
2. Include `procrastina_ai` in `INSTALLED_APPS`
3. Set up database migrations

## 📝 Function-Based Views

All views are function-based and well-commented:

```python
# Page views (render HTML)
@require_http_methods(["GET"])
def prediction(request):
    return render(request, 'procrastina_ai/prediction.html')

# API views (return JSON)
@require_http_methods(["POST"])
def api_create_session(request):
    data = json.loads(request.body)
    # Process and return JSON
    return JsonResponse({'success': True, 'data': {...}})
```

Features:
- Well-documented with docstrings
- Clear parameter explanations
- Example request/response in docstrings
- Error handling with proper HTTP status codes
- CSRF protection built-in

## 🐛 Troubleshooting

### Error: "OpenAI API key not found"
**Solution:** Add `OPENAI_API_KEY` to `.env` file

### Error: "Module procrastina_ai.services not found"
**Solution:** Create `services.py` in procrastina_ai directory (should be included)

### Error: "Session not found"
**Solution:** Make sure to call `/api/create-session/` first to get sessionId

### Error: "Database table doesn't exist"
**Solution:** Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Error: "OpenAI API rate limit"
**Solution:** Wait a moment and retry, or upgrade OpenAI account

## ✅ Verification Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] Migrations run (`python manage.py migrate`)
- [ ] Server starts (`python manage.py runserver`)
- [ ] Admin accessible (`http://localhost:8000/admin`)
- [ ] Landing page loads (`http://localhost:8000/projects/procrastina-ai/`)
- [ ] Setup form works
- [ ] API endpoints respond with JSON

## 🎯 Key Features

✅ **Modular Architecture**
- All AI functions in `services.py`
- Clean separation of concerns
- Function-based views (easy to understand)

✅ **Database Models**
- Session, Disappearance, Report models
- Proper relationships and indexes
- Django ORM for safe queries

✅ **API Endpoints**
- 5 JSON endpoints
- CSRF protection
- Proper error handling
- HTTP status codes

✅ **Frontend Integration**
- JavaScript functions in `script.js`
- Easy to call APIs
- Session storage with localStorage
- Notification system

✅ **Well-Commented**
- Docstrings for all functions
- Example request/responses
- Beginner-friendly code
- Clear variable names

✅ **Admin Interface**
- View sessions, disappearances, reports
- Filter and search capabilities
- Custom display fields

## 📚 Next Steps

1. **Setup** (follow Quick Start above)
2. **Test API endpoints** using Postman or cURL
3. **Test frontend** by visiting pages
4. **Use admin** to view stored data
5. **Deploy** when ready

## 📞 Help & Support

### File Locations
- Models: `procrastina_ai/models.py`
- Views: `procrastina_ai/views.py`
- URLs: `procrastina_ai/urls.py`
- Services: `procrastina_ai/services.py`
- Frontend: `procrastina_ai/static/procrastina_ai/script.js`
- Templates: `procrastina_ai/templates/procrastina_ai/`

### Common Tasks

**View all sessions:**
```python
from procrastina_ai.models import Session
sessions = Session.objects.all()
```

**Query sessions by mood:**
```python
sleepy_sessions = Session.objects.filter(mood='sleepy')
```

**Get disappearances for a session:**
```python
session = Session.objects.first()
disappearances = session.disappearances.all()
```

**Check API response:**
```bash
curl -X POST http://localhost:8000/projects/procrastina-ai/api/create-session/ \
  -H "Content-Type: application/json" \
  -d '{"mood":"sleepy","interests":["YouTube"],"tasks":["Work"]}'
```

## 🎉 You're Ready!

Everything is now consolidated in the `procrastina_ai` Django app with:
- ✅ Models for data storage
- ✅ Services for AI generation
- ✅ Views for pages and APIs
- ✅ Well-commented, beginner-friendly code
- ✅ Complete frontend integration

**Start procrastinating more efficiently!** 🚀

---

*Built with ❤️ and procrastination*  
*ProcrastinaAI™ - How can I procrastinate more efficiently?*
