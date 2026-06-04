const express = require('express');
const router = express.Router();
const { generatePredictionHandler } = require('../controllers/predictionController');

// POST /api/generate-prediction
router.post('/', generatePredictionHandler);

module.exports = router;
