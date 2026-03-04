const mongoose = require('mongoose');

const otpSchema = new mongoose.Schema({
    identifier: {
        type: String, // email or phone
        required: true,
        index: true
    },
    otp: {
        type: String,
        required: true
    },
    createdAt: {
        type: Date,
        default: Date.now,
        expires: 300 // 5 minutes TTL
    }
});

module.exports = mongoose.model('Otp', otpSchema);
