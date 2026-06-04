const express = require('express');
const router = express.Router();
const { saveDisappearance } = require('../controllers/disappearanceController');

// POST /api/save-disappearance
router.post('/', saveDisappearance);

module.exports = router;
