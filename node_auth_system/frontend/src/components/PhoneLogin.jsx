import React, { useState, useEffect } from 'react';
import { auth } from '../firebase/firebaseConfig';
import { RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { authAPI } from '../services/api';
import OtpInput from './OtpInput';

const PhoneLogin = ({ onLoginSuccess }) => {
    const [phoneNumber, setPhoneNumber] = useState('');
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // 1: Phone, 2: OTP
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [confirmationResult, setConfirmationResult] = useState(null);

    useEffect(() => {
        // Initialize Recaptcha only once
        if (!window.recaptchaVerifier) {
            window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
                size: 'invisible',
                callback: () => {
                    // reCAPTCHA solved, allow signInWithPhoneNumber.
                }
            });
        }
        return () => {
            if (window.recaptchaVerifier) {
                window.recaptchaVerifier.clear();
                window.recaptchaVerifier = null;
            }
        };
    }, []);

    const handleSendOTP = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const result = await signInWithPhoneNumber(auth, phoneNumber, window.recaptchaVerifier);
            setConfirmationResult(result);
            setStep(2);
        } catch (err) {
            console.error('Firebase Auth Error:', err);
            setError(err.message || 'Failed to send OTP. Please check the number.');
            // Reset reCAPTCHA if it fails
            if (window.recaptchaVerifier) {
                window.recaptchaVerifier.clear();
                window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
                    size: 'invisible'
                });
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const result = await confirmationResult.confirm(otp);
            const user = result.user;

            // Send verified phone to backend
            const response = await authAPI.firebaseLogin({
                phone: user.phoneNumber,
                name: user.displayName || 'User'
            });

            localStorage.setItem('token', response.data.token);
            onLoginSuccess(response.data.user);
        } catch (err) {
            console.error('OTP Verification Error:', err);
            setError('Invalid OTP. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div id="recaptcha-container"></div>

            {step === 1 ? (
                <form onSubmit={handleSendOTP} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Mobile Number
                        </label>
                        <input
                            type="tel"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                            placeholder="+919994053392"
                            className="w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-400 outline-none transition-all"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={isLoading || !phoneNumber}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg active:scale-95 disabled:opacity-50 flex items-center justify-center"
                    >
                        {isLoading ? <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : 'Send OTP'}
                    </button>
                </form>
            ) : (
                <form onSubmit={handleVerifyOTP} className="space-y-6 text-center">
                    <p className="text-gray-600 mb-4 text-sm">
                        Enter the 6-digit code sent to<br />
                        <span className="font-semibold">{phoneNumber}</span>
                    </p>
                    <OtpInput value={otp} onChange={setOtp} />

                    {error && <p className="text-red-500 text-sm font-medium mt-2">{error}</p>}

                    <button
                        type="submit"
                        disabled={isLoading || otp.length < 6}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg active:scale-95 disabled:opacity-50 flex items-center justify-center mt-6"
                    >
                        {isLoading ? <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : 'Verify & Login'}
                    </button>

                    <button
                        type="button"
                        onClick={() => { setStep(1); setOtp(''); }}
                        className="text-gray-500 text-sm hover:text-gray-700 underline"
                    >
                        Change Number
                    </button>
                </form>
            )}

            {step === 1 && error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}
        </div>
    );
};

export default PhoneLogin;
