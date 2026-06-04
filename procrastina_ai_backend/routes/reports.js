const express = require('express');
const router = express.Router();
const { generateReportHandler } = require('../controllers/reportController');

// POST /api/generate-report
router.post('/', generateReportHandler);

module.exports = router;
