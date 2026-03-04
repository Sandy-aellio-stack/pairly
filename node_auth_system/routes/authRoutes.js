const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

// Routes
router.post('/send-email-otp', authController.sendEmailOTP);
router.post('/verify-email-otp', authController.verifyEmailOTP);
router.post('/firebase-login', authController.firebaseLogin);
router.post('/login', authController.login);

module.exports = router;
