const { v4: uuidv4 } = require('uuid');
const pool = require('../config/database');
const { generateReport } = require('../utils/openai');

// POST /generate-report
// Generates a daily procrastination report with AI summary
const generateReportHandler = async (req, res) => {
  try {
    const { sessionId, tasksPlanned, tasksCompleted, disappearances, commonExcuse } = req.body;

    if (!sessionId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required field: sessionId'
      });
    }

    const tasksCount = tasksPlanned || 0;
    const completedCount = tasksCompleted || 0;
    const disappearanceCount = disappearances || 0;
    const excuse = commonExcuse || 'Researching optimal workflow setup';

    // Generate report using OpenAI
    const reportResult = await generateReport(
      tasksCount,
      completedCount,
      disappearanceCount,
      excuse
    );

    if (!reportResult.success) {
      return res.status(500).json({
        success: false,
        error: 'Failed to generate report'
      });
    }

    // Calculate procrastination score (0-100)
    const procrastinationScore = tasksCount > 0 
      ? Math.max(0, Math.min(100, 100 - (completedCount / tasksCount) * 50 + disappearanceCount * 3))
      : 0;

    // Save to database
    const reportId = uuidv4();
    const responseId = uuidv4();
    const connection = await pool.getConnection();

    try {
      // Save report
      await connection.execute(
        'INSERT INTO reports (id, session_id, report_date, tasks_planned, tasks_completed, total_disappearances, procrastination_score, ai_summary) VALUES (?, ?, CURDATE(), ?, ?, ?, ?, ?)',
        [
          reportId,
          sessionId,
          tasksCount,
          completedCount,
          disappearanceCount,
          Math.round(procrastinationScore),
          reportResult.data
        ]
      );

      // Save AI response
      await connection.execute(
        'INSERT INTO ai_responses (id, session_id, response_type, prompt, response_content, tokens_used) VALUES (?, ?, ?, ?, ?, ?)',
        [
          responseId,
          sessionId,
          'report',
          JSON.stringify({ tasksPlanned, tasksCompleted, disappearances, commonExcuse }),
          reportResult.data,
          reportResult.tokens
        ]
      );

      connection.release();

      res.status(201).json({
        success: true,
        data: {
          reportId,
          responseId,
          sessionId,
          tasksPlanned: tasksCount,
          tasksCompleted: completedCount,
          totalDisappearances: disappearanceCount,
          procrastinationScore: Math.round(procrastinationScore),
          aiSummary: reportResult.data,
          date: new Date().toISOString().split('T')[0]
        }
      });
    } catch (error) {
      connection.release();
      throw error;
    }
  } catch (error) {
    console.error('Generate Report Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = {
  generateReportHandler
};
