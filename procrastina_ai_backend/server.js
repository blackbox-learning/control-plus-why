const express = require('express');
const cors = require('cors');
require('dotenv').config();

// Import routes
const sessionsRouter = require('./routes/sessions');
const predictionsRouter = require('./routes/predictions');
const disappearancesRouter = require('./routes/disappearances');
const reportsRouter = require('./routes/reports');
const reasonsRouter = require('./routes/reasons');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'ProcrastinaAI Backend is running' });
});

// API Routes
app.post('/api/create-session', sessionsRouter);
app.post('/api/generate-prediction', predictionsRouter);
app.post('/api/save-disappearance', disappearancesRouter);
app.post('/api/generate-report', reportsRouter);
app.post('/api/generate-funny-reasons', reasonsRouter);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: err.message || 'Internal server error'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║        ProcrastinaAI™ Backend Server                         ║
║        How can I procrastinate more efficiently?             ║
╚══════════════════════════════════════════════════════════════╝

✅ Server running on port ${PORT}
📍 http://localhost:${PORT}

📚 API Endpoints:
   POST /api/create-session
   POST /api/generate-prediction
   POST /api/save-disappearance
   POST /api/generate-report
   POST /api/generate-funny-reasons

🔍 Check status: http://localhost:${PORT}/health
`);
});

module.exports = app;
