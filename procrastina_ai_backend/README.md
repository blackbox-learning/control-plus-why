# ProcrastinaAI™ Backend

**How can I procrastinate more efficiently?**

A Node.js/Express backend for the ProcrastinaAI™ procrastination tracking platform. Integrates OpenAI API for intelligent procrastination predictions, funny excuses, and witty AI responses.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- MySQL 8.0+
- OpenAI API key

### Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your database credentials and OpenAI API key:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=procrastina_ai
OPENAI_API_KEY=sk-xxxxxxxxx
PORT=5000
```

3. **Create the database:**
```bash
mysql -u root -p < database/schema.sql
```

4. **Start the server:**
```bash
npm start
```

For development with auto-reload:
```bash
npm run dev
```

Server will be available at `http://localhost:5000`

## 📚 API Endpoints

### 1. Create Session
**POST** `/api/create-session`

Creates a new user session with mood, interests, and tasks.

**Request:**
```json
{
  "mood": "Sleepy",
  "interests": ["YouTube", "AI", "Gaming"],
  "tasks": ["Record Video", "Send Email", "Code Review"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "userId": "uuid",
    "sessionId": "uuid",
    "mood": "Sleepy",
    "interests": ["YouTube", "AI", "Gaming"],
    "tasks": ["Record Video", "Send Email", "Code Review"],
    "message": "Session created successfully"
  }
}
```

---

### 2. Generate Prediction
**POST** `/api/generate-prediction`

Generates a procrastination prediction journey using AI.

**Request:**
```json
{
  "sessionId": "uuid",
  "mood": "Sleepy",
  "interests": ["YouTube", "AI", "Gaming"],
  "tasks": ["Record Video", "Send Email", "Code Review"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "responseId": "uuid",
    "sessionId": "uuid",
    "prediction": [
      "Open email, immediately distracted",
      "Check YouTube for 'quick' inspiration",
      "Find AI video, watch for 2 hours",
      "Research GPT-5 theories",
      "Realize time passed, panic sets in",
      "Make coffee and contemplate life",
      "Close laptop and nap"
    ],
    "confidence": 94
  }
}
```

---

### 3. Save Disappearance
**POST** `/api/save-disappearance`

Tracks where the user disappeared during a work session and generates witty AI response.

**Request:**
```json
{
  "sessionId": "uuid",
  "disappearanceType": "youtube",
  "mood": "Sleepy",
  "interests": ["YouTube", "AI", "Gaming"]
}
```

Or for custom location:
```json
{
  "sessionId": "uuid",
  "disappearanceType": "other",
  "customLocation": "Playing Valorant for 3 hours",
  "mood": "Lazy",
  "interests": ["Gaming"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "disappearanceId": "uuid",
    "responseId": "uuid",
    "sessionId": "uuid",
    "disappearanceType": "youtube",
    "aiResponse": "Ah yes, the classic YouTube rabbit hole. You went in for inspiration, stayed for the algorithm's trap. I've seen this plot before—never ends well for your deadline."
  }
}
```

---

### 4. Generate Report
**POST** `/api/generate-report`

Generates a daily procrastination report with AI summary.

**Request:**
```json
{
  "sessionId": "uuid",
  "tasksPlanned": 4,
  "tasksCompleted": 1,
  "disappearances": 7,
  "commonExcuse": "Researching optimal workflow setup"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "reportId": "uuid",
    "responseId": "uuid",
    "sessionId": "uuid",
    "tasksPlanned": 4,
    "tasksCompleted": 1,
    "totalDisappearances": 7,
    "procrastinationScore": 87,
    "aiSummary": "Today's adventure: you planned 4 tasks, completed 1, and took 7 scenic detours to wonderland. Your procrastination score of 87/100 is impressive—you're a professional!",
    "date": "2024-06-04"
  }
}
```

---

### 5. Generate Funny Reasons
**POST** `/api/generate-funny-reasons`

Generates hilarious reasons to procrastinate on a specific task.

**Request:**
```json
{
  "sessionId": "uuid",
  "taskName": "Record Video",
  "mood": "Motivated"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "responseId": "uuid",
    "sessionId": "uuid",
    "taskName": "Record Video",
    "reasons": [
      "Your lighting setup needs a complete overhaul. You can't record until Pinterest gives you better ideas.",
      "The camera probably needs 47 software updates and recalibration. Better check YouTube tutorials first.",
      "You have 73 browser tabs open about cinematography. Closing them seems like work, so recording seems unwise.",
      "Your background isn't aesthetic enough. You need to rearrange your entire room first. This is essential preparation."
    ]
  }
}
```

---

## 📊 Database Schema

### Tables

**users**
- `id` (UUID, Primary Key)
- `username` (VARCHAR)
- `mood` (VARCHAR)
- `interests` (JSON)
- `created_at`, `updated_at` (Timestamps)

**sessions**
- `id` (UUID, Primary Key)
- `user_id` (Foreign Key to users)
- `mood`, `interests`, `tasks` (JSON)
- `session_started`, `session_ended` (Timestamps)

**tasks**
- `id` (UUID, Primary Key)
- `session_id` (Foreign Key)
- `task_name`, `task_category`, `estimated_time`, `actual_time`
- `completed` (Boolean)

**disappearances**
- `id` (UUID, Primary Key)
- `session_id` (Foreign Key)
- `disappearance_type` (VARCHAR)
- `custom_location` (VARCHAR)
- `duration_minutes` (INT)
- `ai_response` (TEXT)

**ai_responses**
- `id` (UUID, Primary Key)
- `session_id` (Foreign Key)
- `response_type` (VARCHAR: prediction, disappearance, report, funny_reasons)
- `prompt` (TEXT)
- `response_content` (LONGTEXT)
- `tokens_used` (INT)

**reports**
- `id` (UUID, Primary Key)
- `session_id` (Foreign Key)
- `report_date` (DATE)
- `tasks_planned`, `tasks_completed`, `total_disappearances`, `procrastination_score` (INT)
- `ai_summary` (LONGTEXT)

---

## 🔧 Configuration

All configuration is handled via environment variables in `.env`:

```env
# Database
DB_HOST=localhost              # MySQL host
DB_USER=root                   # MySQL user
DB_PASSWORD=password           # MySQL password
DB_NAME=procrastina_ai         # Database name
DB_PORT=3306                   # MySQL port

# OpenAI
OPENAI_API_KEY=sk-xxxxx       # Your OpenAI API key

# Server
PORT=5000                      # Server port
NODE_ENV=development           # Environment
```

---

## 🎯 Integration with Frontend

The backend returns JSON responses suitable for:
- HTML/CSS/JavaScript frontend (CORS enabled)
- Mobile apps
- Desktop applications

### Example Frontend Integration

```javascript
// Create session
const response = await fetch('http://localhost:5000/api/create-session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    mood: 'Sleepy',
    interests: ['YouTube', 'AI', 'Gaming'],
    tasks: ['Record Video', 'Send Email', 'Code Review']
  })
});

const data = await response.json();
const sessionId = data.data.sessionId;

// Generate prediction
const predictionResponse = await fetch('http://localhost:5000/api/generate-prediction', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sessionId,
    mood: 'Sleepy',
    interests: ['YouTube', 'AI', 'Gaming'],
    tasks: ['Record Video', 'Send Email', 'Code Review']
  })
});

const predictionData = await predictionResponse.json();
console.log(predictionData.data.prediction); // Array of prediction steps
```

---

## 📝 Error Handling

All errors return JSON with error details:

```json
{
  "success": false,
  "error": "Missing required fields: sessionId, mood, interests, tasks"
}
```

Common HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (missing fields)
- `500` - Server Error

---

## 🔑 OpenAI Integration

The backend uses OpenAI's GPT-3.5-turbo model for:

1. **Predictions** - Generate procrastination journeys
2. **Disappearance Responses** - Witty comments about where users went
3. **Reports** - Daily procrastination summaries
4. **Funny Reasons** - Creative excuses to procrastinate

All responses are sarcastic, hilarious, and personalized based on mood and interests.

---

## 📦 Project Structure

```
procrastina_ai_backend/
├── server.js                    # Main Express server
├── package.json                 # Dependencies
├── .env.example                 # Environment variables template
├── config/
│   └── database.js             # MySQL connection pool
├── routes/
│   ├── sessions.js             # Session routes
│   ├── predictions.js          # Prediction routes
│   ├── disappearances.js       # Disappearance routes
│   ├── reports.js              # Report routes
│   └── reasons.js              # Funny reasons routes
├── controllers/
│   ├── sessionController.js    # Session logic
│   ├── predictionController.js # Prediction logic
│   ├── disappearanceController.js
│   ├── reportController.js
│   └── reasonController.js
├── utils/
│   └── openai.js               # OpenAI API integration
└── database/
    └── schema.sql              # MySQL schema
```

---

## 🚀 Deployment

### Local Testing
```bash
npm run dev
```

### Production
```bash
NODE_ENV=production npm start
```

### Docker (Optional)
To containerize the backend, create a `Dockerfile` and `docker-compose.yml`.

---

## 🎉 Features

✅ Create user sessions with profiles  
✅ Generate AI procrastination predictions  
✅ Track where users disappear with AI responses  
✅ Generate daily procrastination reports  
✅ Create funny reasons to procrastinate  
✅ MySQL database for persistence  
✅ OpenAI integration for intelligent responses  
✅ CORS enabled for frontend integration  
✅ JSON-only API responses  
✅ Error handling and validation  

---

## 📄 License

MIT

---

## 🎭 About

ProcrastinaAI™ - *How can I procrastinate more efficiently?*

Built with ❤️ and procrastination
