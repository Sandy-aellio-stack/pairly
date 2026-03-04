import React, { useState } from 'react';
import { authAPI } from '../services/api';
import OtpInput from '../components/OtpInput';
import PhoneLogin from '../components/PhoneLogin';

const Login = () => {
    const [method, setMethod] = useState('email'); // 'email' | 'phone'
    const [identifier, setIdentifier] = useState(''); // email address
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // 1: input id, 2: input otp
    const [isLoading, setIsLoading] = useState(false);
    const [timer, setTimer] = useState(0);
    const [error, setError] = useState('');

    const handleSendEmailOTP = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            await authAPI.sendEmailOTP(identifier);
            setStep(2);
            setTimer(300); // 5 minutes
            const interval = setInterval(() => {
                setTimer((prev) => {
                    if (prev <= 1) {
                        clearInterval(interval);
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to send OTP');
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyEmailOTP = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const verifyRes = await authAPI.verifyEmailOTP(identifier, otp);
            localStorage.setItem('token', verifyRes.data.token);
            window.location.href = '/dashboard';
        } catch (err) {
            setError(err.response?.data?.error || 'Invalid OTP. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleLoginSuccess = (user) => {
        window.location.href = '/dashboard';
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
                <h2 className="text-3xl font-bold text-center mb-8 text-gray-800">
                    {step === 1 ? 'Welcome Back' : 'Verify Identity'}
                </h2>

                {step === 1 && (
                    <div className="flex bg-gray-100 p-1 rounded-xl mb-8">
                        <button
                            onClick={() => setMethod('email')}
                            className={`flex-1 py-2 rounded-lg font-medium transition-all ${method === 'email' ? 'bg-white shadow text-blue-600' : 'text-gray-500'}`}
                        >
                            Email
                        </button>
                        <button
                            onClick={() => setMethod('phone')}
                            className={`flex-1 py-2 rounded-lg font-medium transition-all ${method === 'phone' ? 'bg-white shadow text-blue-600' : 'text-gray-500'}`}
                        >
                            Mobile
                        </button>
                    </div>
                )}

                {method === 'email' ? (
                    <form onSubmit={step === 1 ? handleSendEmailOTP : handleVerifyEmailOTP} className="space-y-6">
                        {step === 1 ? (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    value={identifier}
                                    onChange={(e) => setIdentifier(e.target.value)}
                                    placeholder="john@example.com"
                                    className="w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-400 outline-none transition-all"
                                    required
                                />
                            </div>
                        ) : (
                            <div className="text-center">
                                <p className="text-gray-600 mb-4">
                                    Enter the 6-digit code sent to<br />
                                    <span className="font-semibold">{identifier}</span>
                                </p>
                                <OtpInput value={otp} onChange={setOtp} />

                                <div className="mt-6">
                                    {timer > 0 ? (
                                        <p className="text-sm text-gray-500">
                                            Resend code in <span className="font-mono">{Math.floor(timer / 60)}:{String(timer % 60).padStart(2, '0')}</span>
                                        </p>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={handleSendEmailOTP}
                                            className="text-blue-600 hover:underline font-medium"
                                        >
                                            Resend OTP
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}

                        {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                        >
                            {isLoading ? (
                                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            ) : (
                                step === 1 ? 'Get Started' : 'Verify & Login'
                            )}
                        </button>

                        {step === 2 && (
                            <button
                                type="button"
                                onClick={() => { setStep(1); setOtp(''); }}
                                className="w-full text-gray-500 text-sm font-medium hover:text-gray-700"
                            >
                                Change Email
                            </button>
                        )}
                    </form>
                ) : (
                    <PhoneLogin onLoginSuccess={handleLoginSuccess} />
                )}
            </div>
        </div>
    );
};

export default Login;
