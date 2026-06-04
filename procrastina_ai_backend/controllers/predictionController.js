const { v4: uuidv4 } = require('uuid');
const pool = require('../config/database');
const { generatePrediction } = require('../utils/openai');

// POST /generate-prediction
// Generates a procrastination prediction using OpenAI
const generatePredictionHandler = async (req, res) => {
  try {
    const { sessionId, mood, interests, tasks } = req.body;

    if (!sessionId || !mood || !interests || !tasks) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: sessionId, mood, interests, tasks'
      });
    }

    // Generate prediction using OpenAI
    const predictionResult = await generatePrediction(mood, interests, tasks);

    if (!predictionResult.success) {
      return res.status(500).json({
        success: false,
        error: 'Failed to generate prediction'
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
          'prediction',
          JSON.stringify({ mood, interests, tasks }),
          predictionResult.data,
          predictionResult.tokens
        ]
      );

      connection.release();

      // Parse the prediction steps
      const steps = predictionResult.data
        .split('\n')
        .filter(line => line.trim())
        .map(line => line.replace(/^\d+\.\s*/, '').trim());

      res.status(200).json({
        success: true,
        data: {
          responseId,
          sessionId,
          prediction: steps,
          fullText: predictionResult.data,
          confidence: 94
        }
      });
    } catch (error) {
      connection.release();
      throw error;
    }
  } catch (error) {
    console.error('Generate Prediction Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = {
  generatePredictionHandler
};
