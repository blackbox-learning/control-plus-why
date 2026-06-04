# ProcrastinaAI™ Backend - Quick Start Guide

## 📋 Prerequisites

Ensure you have the following installed:
- **Node.js** 16+ ([Download](https://nodejs.org/))
- **MySQL** 8.0+ ([Download](https://www.mysql.com/downloads/mysql/))
- **OpenAI API Key** ([Get one](https://platform.openai.com/api-keys))

## 🚀 Setup Instructions

### Step 1: Install Node Dependencies

```bash
cd procrastina_ai_backend
npm install
```

This will install:
- `express` - Web framework
- `mysql2` - MySQL driver
- `openai` - OpenAI API client
- `cors` - Cross-Origin Resource Sharing
- `dotenv` - Environment variables
- `uuid` - ID generation
- `nodemon` - Development auto-reload

### Step 2: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=procrastina_ai
DB_PORT=3306

# OpenAI Configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxx

# Server Configuration
PORT=5000
NODE_ENV=development
```

### Step 3: Create MySQL Database

1. **Open MySQL:**
```bash
mysql -u root -p
```

2. **Execute the schema:**
```bash
mysql -u root -p < procrastina_ai_backend/database/schema.sql
```

Or paste the contents of `database/schema.sql` in MySQL client.

### Step 4: Start the Server

**Development (with auto-reload):**
```bash
npm run dev
```

**Production:**
```bash
npm start
```

You should see:
```
╔══════════════════════════════════════════════════════════════╗
║        ProcrastinaAI™ Backend Server                         ║
║        How can I procrastinate more efficiently?             ║
╚══════════════════════════════════════════════════════════════╝

✅ Server running on port 5000
📍 http://localhost:5000

📚 API Endpoints:
   POST /api/create-session
   POST /api/generate-prediction
   POST /api/save-disappearance
   POST /api/generate-report
   POST /api/generate-funny-reasons

🔍 Check status: http://localhost:5000/health
```

## ✅ Verify Setup

### Health Check

Open your browser or run:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status":"ok","message":"ProcrastinaAI Backend is running"}
```

### Test API Endpoint

```bash
curl -X POST http://localhost:5000/api/create-session \
  -H "Content-Type: application/json" \
  -d '{
    "mood": "Sleepy",
    "interests": ["YouTube", "AI", "Gaming"],
    "tasks": ["Record Video", "Send Email", "Code Review"]
  }'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "userId": "uuid-here",
    "sessionId": "uuid-here",
    "mood": "Sleepy",
    "interests": ["YouTube", "AI", "Gaming"],
    "tasks": ["Record Video", "Send Email", "Code Review"],
    "message": "Session created successfully"
  }
}
```

## 🔌 Connect Frontend

Update your frontend to point to the backend:

```javascript
const API_BASE = 'http://localhost:5000/api';

// Example: Create session
async function createSession() {
  const response = await fetch(`${API_BASE}/create-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mood: 'Sleepy',
      interests: ['YouTube', 'AI', 'Gaming'],
      tasks: ['Record Video', 'Send Email']
    })
  });
  return await response.json();
}
```

## 🆘 Troubleshooting

### Error: "connect ECONNREFUSED 127.0.0.1:3306"
**Solution:** MySQL is not running. Start MySQL service.

On Windows:
```bash
mysql.server start
```

On Mac:
```bash
brew services start mysql
```

On Linux:
```bash
sudo systemctl start mysql
```

### Error: "Access denied for user 'root'@'localhost'"
**Solution:** Check your `DB_PASSWORD` in `.env` file.

### Error: "Unknown database 'procrastina_ai'"
**Solution:** Run the database schema:
```bash
mysql -u root -p < database/schema.sql
```

### Error: "OPENAI_API_KEY is required"
**Solution:** Add your OpenAI API key to `.env`:
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxx
```

Get a key at: https://platform.openai.com/api-keys

### Error: "Cannot find module 'openai'"
**Solution:** Reinstall dependencies:
```bash
npm install
```

## 📁 Project Structure

```
procrastina_ai_backend/
├── server.js                 # Express server entry point
├── package.json             # Dependencies
├── .env                     # Environment variables (created from .env.example)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── README.md                # Full documentation
├── QUICKSTART.md            # This file
├── config/
│   └── database.js          # MySQL pool configuration
├── routes/
│   ├── sessions.js          # POST /api/create-session
│   ├── predictions.js       # POST /api/generate-prediction
│   ├── disappearances.js    # POST /api/save-disappearance
│   ├── reports.js           # POST /api/generate-report
│   └── reasons.js           # POST /api/generate-funny-reasons
├── controllers/
│   ├── sessionController.js
│   ├── predictionController.js
│   ├── disappearanceController.js
│   ├── reportController.js
│   └── reasonController.js
├── utils/
│   └── openai.js            # OpenAI API integration
└── database/
    └── schema.sql           # MySQL database schema
```

## 🎯 Next Steps

1. ✅ Start the backend server
2. ✅ Test the health endpoint
3. ✅ Create your first session
4. ✅ Generate a prediction
5. ✅ Connect your frontend
6. ✅ Start procrastinating efficiently!

## 📞 Support

For issues or questions:
- Check the `README.md` for full API documentation
- Verify your `.env` configuration
- Check MySQL is running and accessible
- Ensure OpenAI API key is valid

## 🎉 Ready!

Your ProcrastinaAI™ backend is ready to power your procrastination tracking!

**Start the server:**
```bash
npm run dev
```

**Happy procrastinating!** 🚀
