# ProcrastinaAI Backend - Setup Checklist

## Pre-Flight Checks

### Required Software
- [ ] Node.js 16+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] MySQL 8.0+ installed and running
- [ ] OpenAI API key ready (from https://platform.openai.com/api-keys)

### Verify Installations
```bash
node --version
npm --version
mysql --version
```

---

## Backend Setup Checklist

### Step 1: Install Dependencies
```bash
cd procrastina_ai_backend
npm install
```

✅ Check: Look for "added X packages" message

### Step 2: Configure Environment
```bash
cp .env.example .env
```

Edit `.env` file:
- [ ] Set `DB_HOST` (usually `localhost`)
- [ ] Set `DB_USER` (usually `root`)
- [ ] Set `DB_PASSWORD` (your MySQL password)
- [ ] Set `OPENAI_API_KEY` (your OpenAI key)
- [ ] Verify `PORT=5000`

### Step 3: Create Database

Option A - Using Command Line:
```bash
mysql -u root -p < procrastina_ai_backend/database/schema.sql
```

Option B - Using MySQL Client:
1. Open MySQL Workbench or `mysql -u root -p`
2. Copy and paste contents of `database/schema.sql`
3. Execute

✅ Check: Database `procrastina_ai` created with 6 tables

### Step 4: Verify Database

```bash
mysql -u root -p -e "USE procrastina_ai; SHOW TABLES;"
```

Should see tables:
- [ ] users
- [ ] sessions
- [ ] tasks
- [ ] disappearances
- [ ] ai_responses
- [ ] reports

### Step 5: Start Backend Server

```bash
npm start
```

OR for development with auto-reload:
```bash
npm run dev
```

✅ Check: See startup message with "Server running on port 5000"

---

## Verification Checklist

### Health Check
```bash
curl http://localhost:5000/health
```

✅ Should return: `{"status":"ok","message":"ProcrastinaAI Backend is running"}`

### Test First API
```bash
curl -X POST http://localhost:5000/api/create-session \
  -H "Content-Type: application/json" \
  -d '{"mood":"Sleepy","interests":["YouTube"],"tasks":["Work"]}'
```

✅ Should return: JSON with `success: true` and session data

### Run Test Script

Windows:
```bash
test-api.bat
```

Mac/Linux:
```bash
bash test-api.sh
```

✅ All 7 tests should complete without errors

---

## Common Issues & Solutions

### Issue: "connect ECONNREFUSED 127.0.0.1:3306"
**Solution:** MySQL is not running
```bash
# Windows
mysql.server start

# Mac
brew services start mysql

# Linux
sudo systemctl start mysql
```

### Issue: "Access denied for user 'root'@'localhost'"
**Solution:** Check MySQL credentials in `.env`
```
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
```

### Issue: "Unknown database 'procrastina_ai'"
**Solution:** Run database schema
```bash
mysql -u root -p < procrastina_ai_backend/database/schema.sql
```

### Issue: "OPENAI_API_KEY is undefined"
**Solution:** Add OpenAI key to `.env`
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
```

Get a key at: https://platform.openai.com/api-keys

### Issue: "Cannot find module 'express'"
**Solution:** Install dependencies
```bash
npm install
```

### Issue: "Port 5000 already in use"
**Solution:** Change port in `.env` or stop other service
```
PORT=5001
```

### Issue: Backend runs but no responses from OpenAI
**Solution:** Check OpenAI API key has credits and is valid

---

## Frontend Integration Checklist

- [ ] Backend is running on `http://localhost:5000`
- [ ] Frontend can reach backend (CORS enabled)
- [ ] Update `API_BASE` in frontend to `http://localhost:5000/api`
- [ ] Copy `FRONTEND_INTEGRATION.js` functions to frontend
- [ ] Test all API endpoints from browser console
- [ ] Session IDs are being stored in localStorage

---

## Files & Directories

```
procrastina_ai_backend/
├── server.js                 ✅ Main server file
├── package.json              ✅ Dependencies
├── .env                      ✅ Configuration (CREATE FROM .env.example)
├── .env.example              ✅ Configuration template
├── .gitignore               ✅ Git ignore
├── README.md                 ✅ Full documentation
├── QUICKSTART.md             ✅ Quick setup guide
├── FRONTEND_INTEGRATION.js   ✅ Frontend API helper
├── test-api.sh              ✅ Test script (Mac/Linux)
├── test-api.bat             ✅ Test script (Windows)
├── config/
│   └── database.js          ✅ MySQL config
├── routes/
│   ├── sessions.js
│   ├── predictions.js
│   ├── disappearances.js
│   ├── reports.js
│   └── reasons.js
├── controllers/
│   ├── sessionController.js
│   ├── predictionController.js
│   ├── disappearanceController.js
│   ├── reportController.js
│   └── reasonController.js
├── utils/
│   └── openai.js            ✅ OpenAI integration
└── database/
    └── schema.sql           ✅ Database schema
```

---

## API Endpoints Ready

- [ ] POST `/api/create-session` - Create user session
- [ ] POST `/api/generate-prediction` - AI prediction
- [ ] POST `/api/save-disappearance` - Track disappearance
- [ ] POST `/api/generate-report` - Daily report
- [ ] POST `/api/generate-funny-reasons` - Funny excuses

All endpoints return JSON only.

---

## Next Steps

1. ✅ Complete setup checklist
2. ✅ Run test scripts
3. ✅ Verify all endpoints working
4. ✅ Connect frontend
5. ✅ Deploy to production (optional)

---

## Support

- **Full Docs:** See README.md
- **Quick Start:** See QUICKSTART.md
- **Frontend Help:** See FRONTEND_INTEGRATION.js
- **API Tests:** Run test-api.bat (Windows) or test-api.sh (Mac/Linux)

---

## Ready to Procrastinate!

Once all checks are complete, your ProcrastinaAI backend is ready!

```
npm start
```

Happy procrastinating! 🚀
