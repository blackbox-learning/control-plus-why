const { v4: uuidv4 } = require('uuid');
const pool = require('../config/database');

// POST /create-session
// Creates a new user session with mood, interests, and tasks
const createSession = async (req, res) => {
  try {
    const { mood, interests, tasks } = req.body;

    if (!mood || !interests || !tasks) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: mood, interests, tasks'
      });
    }

    const userId = uuidv4();
    const sessionId = uuidv4();

    const connection = await pool.getConnection();

    try {
      // Insert user
      await connection.execute(
        'INSERT INTO users (id, username, mood, interests) VALUES (?, ?, ?, ?)',
        [userId, `User_${userId.slice(0, 8)}`, mood, JSON.stringify(interests)]
      );

      // Insert session
      await connection.execute(
        'INSERT INTO sessions (id, user_id, mood, interests, tasks) VALUES (?, ?, ?, ?, ?)',
        [sessionId, userId, mood, JSON.stringify(interests), JSON.stringify(tasks)]
      );

      connection.release();

      res.status(201).json({
        success: true,
        data: {
          userId,
          sessionId,
          mood,
          interests,
          tasks,
          message: 'Session created successfully'
        }
      });
    } catch (error) {
      connection.release();
      throw error;
    }
  } catch (error) {
    console.error('Create Session Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
};

module.exports = {
  createSession
};
