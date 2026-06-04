const express = require('express');
const router = express.Router();
const { generateFunnyReasonsHandler } = require('../controllers/reasonController');

// POST /api/generate-funny-reasons
router.post('/', generateFunnyReasonsHandler);

module.exports = router;
