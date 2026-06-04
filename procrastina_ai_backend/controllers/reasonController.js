const { v4: uuidv4 } = require('uuid');
const pool = require('../config/database');
const { generateFunnyReasons } = require('../utils/openai');

// POST /generate-funny-reasons
// Generates funny reasons to procrastinate on a task
const generateFunnyReasonsHandler = async (req, res) => {
  try {
    const { sessionId, taskName, mood } = req.body;

    if (!sessionId || !taskName) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: sessionId, taskName'
      });
    }

    // Generate funny reasons using OpenAI
    const reasonsResult = await generateFunnyReasons(taskName, mood || 'Unmotivated');

    if (!reasonsResult.success) {
      return res.status(500).json({
        success: false,
        error: 'Failed to generate funny reasons'
      });
    }

    // Save to database
    const responseId = uuidv4();
    const connection = await pool.getConnection();

    try {
      await connection.execute(
        'INSERT INTO ai_responses (id, session_id, response_type, prompt, response_content, tokens_used) VALUES (?, ?, ?, ?, ?, ?)',
        [
          responseId,
          sessionId,
          'funny_reasons',
          JSON.stringify({ taskName, mood }),
          reasonsResult.data,
          reasonsResult.tokens
        ]
      );

      connection.release();

      // Parse the reasons
      const reasons = reasonsResult.data
        .split('\n')
        .filter(line => line.trim() && line.includes('-'))
        .map(line => line.replace(/^-\s*/, '').trim());

      res.status(201).json({
        success: true,
        data: {
          responseId,
          sessionId,
          taskName,
          reasons: reasons.length > 0 ? reasons : [reasonsResult.data],
          fullText: reasonsResult.data
        }
      });
    } catch (error) {
      connection.release();
      throw error;
    }
  } catch (error) {
    console.error('Generate Funny Reasons Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = {
  generateFunnyReasonsHandler
};
