const { v4: uuidv4 } = require('uuid');
const pool = require('../config/database');
const { generateDisappearanceResponse } = require('../utils/openai');

// POST /save-disappearance
// Tracks where user disappeared and generates AI response
const saveDisappearance = async (req, res) => {
  try {
    const { sessionId, disappearanceType, customLocation, mood, interests } = req.body;

    if (!sessionId || !disappearanceType) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: sessionId, disappearanceType'
      });
    }

    // Generate AI response using OpenAI
    const responseResult = await generateDisappearanceResponse(
      disappearanceType === 'other' ? customLocation : disappearanceType,
      mood || 'Unknown',
      interests || []
    );

    if (!responseResult.success) {
      return res.status(500).json({
        success: false,
        error: 'Failed to generate response'
      });
    }

    // Save to database
    const disappearanceId = uuidv4();
    const responseId = uuidv4();
    const connection = await pool.getConnection();

    try {
      // Save disappearance
      await connection.execute(
        'INSERT INTO disappearances (id, session_id, disappearance_type, custom_location, ai_response) VALUES (?, ?, ?, ?, ?)',
        [
          disappearanceId,
          sessionId,
          disappearanceType,
          customLocation || null,
          responseResult.data
        ]
      );

      // Save AI response
      await connection.execute(
        'INSERT INTO ai_responses (id, session_id, response_type, prompt, response_content, tokens_used) VALUES (?, ?, ?, ?, ?, ?)',
        [
          responseId,
          sessionId,
          'disappearance',
          JSON.stringify({ disappearanceType, customLocation, mood, interests }),
          responseResult.data,
          responseResult.tokens
        ]
      );

      connection.release();

      res.status(201).json({
        success: true,
        data: {
          disappearanceId,
          responseId,
          sessionId,
          disappearanceType,
          customLocation: customLocation || null,
          aiResponse: responseResult.data
        }
      });
    } catch (error) {
      connection.release();
      throw error;
    }
  } catch (error) {
    console.error('Save Disappearance Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = {
  saveDisappearance
};
