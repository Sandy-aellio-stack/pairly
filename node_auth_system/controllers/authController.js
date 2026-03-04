const User = require('../models/User');
const Otp = require('../models/Otp');
const nodemailer = require('nodemailer');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const JWT_SECRET = process.env.JWT_SECRET;

// Configure Nodemailer
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
    }
});

/**
 * 1. Send Email OTP
 * Route: POST /api/auth/send-email-otp
 */
exports.sendEmailOTP = async (req, res) => {
    const { email } = req.body;
    if (!email) return res.status(400).json({ error: 'Email is required' });

    try {
        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        const salt = await bcrypt.genSalt(10);
        const hashedOtp = await bcrypt.hash(otp, salt);

        // Store hashed OTP in DB
        await Otp.findOneAndUpdate(
            { identifier: email },
            { otp: hashedOtp, createdAt: new Date() },
            { upsert: true, new: true }
        );

        // Check for Mock Mode
        if (!process.env.EMAIL_USER || !process.env.EMAIL_PASS) {
            console.log('-----------------------------------------');
            console.log(`MOCK MODE: OTP for ${email} is ${otp}`);
            console.log('-----------------------------------------');
            return res.json({ message: 'OTP sent successfully (MOCK MODE - Check Console)' });
        }

        // Real Email Mode
        const mailOptions = {
            from: process.env.EMAIL_FROM || process.env.EMAIL_USER,
            to: email,
            subject: 'Your Login Verification Code',
            text: `Your 6-digit verification code: ${otp}. Expires in 5 minutes.`
        };

        try {
            await transporter.sendMail(mailOptions);
            res.json({ message: 'OTP sent successfully' });
        } catch (mailError) {
            console.error('CRITICAL: Nodemailer failed to send email!');
            console.error(mailError);
            return res.status(500).json({ error: 'Failed to send OTP' });
        }
    } catch (error) {
        console.error('Error in sendEmailOTP:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
};

/**
 * 2. Verify Email OTP
 * Route: POST /api/auth/verify-email-otp
 */
exports.verifyEmailOTP = async (req, res) => {
    const { email, otp } = req.body;
    if (!email || !otp) return res.status(400).json({ error: 'Email and OTP are required' });

    try {
        const record = await Otp.findOne({ identifier: email });
        if (!record) return res.status(400).json({ error: 'OTP expired or not found' });

        const isMatch = await bcrypt.compare(otp, record.otp);
        if (!isMatch) return res.status(400).json({ error: 'Invalid OTP' });

        // Clean up OTP record
        await Otp.deleteOne({ _id: record._id });

        // Create or Login User
        let user = await User.findOne({ email });
        if (!user) {
            user = await User.create({ email, isEmailVerified: true });
        } else {
            user.isEmailVerified = true;
            await user.save();
        }

        const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '7d' });
        res.json({ token, user, message: 'OTP verified successfully' });
    } catch (error) {
        console.error('Error in verifyEmailOTP:', error);
        res.status(500).json({ error: 'Verification failed' });
    }
};

/**
 * 3. Firebase Phone Login
 * Route: POST /api/auth/firebase-login
 */
exports.firebaseLogin = async (req, res) => {
    const { phone, name } = req.body;
    if (!phone) return res.status(400).json({ error: 'Phone number is required' });

    try {
        let user = await User.findOne({ phone });
        if (!user) {
            user = await User.create({
                phone,
                name: name || 'New User',
                isPhoneVerified: true
            });
        } else {
            user.isPhoneVerified = true;
            if (name && !user.name) user.name = name;
            await user.save();
        }

        const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '7d' });
        res.json({ token, user, message: 'Login successful' });
    } catch (error) {
        console.error('Error in firebaseLogin:', error);
        res.status(500).json({ error: 'Authentication failed' });
    }
};

/**
 * 4. General Login (Legacy)
 * Route: POST /api/auth/login
 */
exports.login = async (req, res) => {
    // Can be used for mobile or other methods if expanded
    res.status(501).json({ error: 'Please use OTP verification routes for now' });
};
