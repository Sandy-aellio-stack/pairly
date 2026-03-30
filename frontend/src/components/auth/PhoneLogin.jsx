import React, { useState, useEffect } from 'react';
import { RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { auth } from '@/firebase/firebaseConfig';
import { Phone, Shield, ArrowLeft, Loader2, Sparkles, Heart } from 'lucide-react';
import { toast } from 'sonner';
import { authAPI } from '@/services/api';
import { useNavigate } from 'react-router-dom';

const PhoneLogin = ({ onBack }) => {
    const navigate = useNavigate();
    const [phoneNumber, setPhoneNumber] = useState('');
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState('phone'); // 'phone' | 'otp'
    const [isLoading, setIsLoading] = useState(false);
    const [confirmationResult, setConfirmationResult] = useState(null);
    const [timer, setTimer] = useState(0);

    useEffect(() => {
        let interval;
        if (timer > 0) {
            interval = setInterval(() => {
                setTimer((prev) => prev - 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [timer]);

    const setupRecaptcha = () => {
        if (!window.recaptchaVerifier) {
            window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
                'size': 'invisible',
                'callback': (response) => {
                    // reCAPTCHA solved, allow signInWithPhoneNumber.
                }
            });
        }
    };

    const handleSendOTP = async (e) => {
        e.preventDefault();
        if (!phoneNumber || phoneNumber.length < 10) {
            toast.error('Please enter a valid phone number');
            return;
        }

        const formattedPhone = phoneNumber.startsWith('+') ? phoneNumber : `+91${phoneNumber}`;

        setIsLoading(true);
        try {
            setupRecaptcha();
            const appVerifier = window.recaptchaVerifier;
            const confirmation = await signInWithPhoneNumber(auth, formattedPhone, appVerifier);
            setConfirmationResult(confirmation);
            setStep('otp');
            setTimer(60);
            toast.success('OTP sent successfully! 📱');
        } catch (error) {
            console.error('Firebase Auth Error:', error);
            toast.error(error.message || 'Failed to send OTP. Please try again.');
            if (window.recaptchaVerifier) {
                window.recaptchaVerifier.clear();
                window.recaptchaVerifier = null;
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        if (!otp || otp.length !== 6) {
            toast.error('Please enter a 6-digit OTP');
            return;
        }

        setIsLoading(true);
        try {
            const result = await confirmationResult.confirm(otp);
            const user = result.user;

            // Call backend to verify and get JWT
            const response = await authAPI.firebaseLogin({
                phone: user.phoneNumber,
                device_id: localStorage.getItem('pairly_device_id') || Math.random().toString(36).substring(7)
            });

            if (response.data.success || response.data.token) {
                const { access_token, refresh_token, token } = response.data;
                const finalToken = token || access_token;

                if (finalToken) localStorage.setItem('access_token', finalToken);
                if (refresh_token) localStorage.setItem('refresh_token', refresh_token);

                toast.success('Login successful! Welcome to Pairly 💕');
                navigate('/dashboard');
                window.location.reload();
            } else {
                toast.error(response.data.message || 'Backend login failed');
            }
        } catch (error) {
            console.error('Verification Error:', error);
            toast.error('Invalid OTP code. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div id="recaptcha-container"></div>

            {step === 'phone' ? (
                <form onSubmit={handleSendOTP} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Enter Mobile Number
                        </label>
                        <div className="relative group">
                            <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2 text-slate-400 group-focus-within:text-rose-500 transition-colors">
                                <Phone size={20} />
                                <span className="font-medium border-r border-slate-200 pr-2">+91</span>
                            </div>
                            <input
                                type="tel"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, '').slice(0, 10))}
                                placeholder="99940 53392"
                                className="w-full pl-24 pr-4 py-4 rounded-2xl border border-slate-200 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 outline-none transition-all text-lg tracking-wider"
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <p className="mt-3 text-xs text-slate-500 flex items-center gap-2">
                            <Shield size={14} className="text-emerald-500" />
                            We'll send a secure 6-digit code via SMS
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || phoneNumber.length < 10}
                        className="w-full py-4 bg-gradient-to-r from-rose-500 to-pink-600 text-white rounded-2xl font-bold shadow-lg shadow-rose-200 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:scale-100 disabled:shadow-none"
                    >
                        {isLoading ? (
                            <Loader2 className="animate-spin" size={24} />
                        ) : (
                            <>
                                <span>Get Verification Code</span>
                                <Sparkles size={20} />
                            </>
                        )}
                    </button>

                    <button
                        type="button"
                        onClick={onBack}
                        className="w-full py-2 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors"
                    >
                        Back to Login Options
                    </button>
                </form>
            ) : (
                <form onSubmit={handleVerifyOTP} className="space-y-6">
                    <div className="text-center space-y-2 mb-8">
                        <div className="w-16 h-16 bg-rose-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Shield className="text-rose-500" size={32} />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-800">Verify it's you</h2>
                        <p className="text-slate-500">
                            Enter the code sent to <span className="font-bold text-slate-700">+91 {phoneNumber}</span>
                        </p>
                    </div>

                    <div className="space-y-4">
                        <div className="relative">
                            <input
                                type="text"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                placeholder="0 0 0 0 0 0"
                                className="w-full px-4 py-5 rounded-2xl border border-slate-200 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 outline-none transition-all text-3xl tracking-[0.5em] font-bold text-center text-slate-800 placeholder:text-slate-200"
                                required
                                maxLength={6}
                                disabled={isLoading}
                                autoFocus
                            />
                        </div>

                        <div className="flex items-center justify-between text-sm px-2">
                            <button
                                type="button"
                                onClick={() => setStep('phone')}
                                className="text-slate-500 hover:text-rose-500 font-medium flex items-center gap-1 transition-colors"
                            >
                                <ArrowLeft size={14} /> Change Number
                            </button>
                            {timer > 0 ? (
                                <span className="text-slate-400">Resend in {timer}s</span>
                            ) : (
                                <button
                                    type="button"
                                    onClick={handleSendOTP}
                                    className="text-rose-600 hover:text-rose-700 font-bold"
                                >
                                    Resend Code
                                </button>
                            )}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || otp.length !== 6}
                        className="w-full py-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-2xl font-bold shadow-lg shadow-emerald-200 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:scale-100"
                    >
                        {isLoading ? (
                            <Loader2 className="animate-spin" size={24} />
                        ) : (
                            <>
                                <span>Verify & Continue</span>
                                <ArrowLeft className="rotate-180" size={20} />
                            </>
                        )}
                    </button>
                </form>
            )}

            {/* Premium Trust Badge */}
            <div className="pt-8 flex items-center justify-center gap-6 border-t border-slate-100">
                <div className="flex flex-col items-center gap-1">
                    <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center">
                        <Heart size={18} className="text-rose-400" fill="currentColor" />
                    </div>
                    <span className="text-[10px] uppercase tracking-widest font-bold text-slate-400">Secure</span>
                </div>
                <div className="flex flex-col items-center gap-1">
                    <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center">
                        <Sparkles size={18} className="text-amber-400" />
                    </div>
                    <span className="text-[10px] uppercase tracking-widest font-bold text-slate-400">Private</span>
                </div>
            </div>
        </div>
    );
};

export default PhoneLogin;
