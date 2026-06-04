const express = require('express');
const router = express.Router();
const { createSession } = require('../controllers/sessionController');

// POST /api/create-session
router.post('/', createSession);

module.exports = router;
