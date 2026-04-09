import React, { useState, useEffect } from 'react';
import { Mail, Shield, ArrowLeft, Loader2, Sparkles, Heart } from 'lucide-react';
import { toast } from 'sonner';
import { authAPI } from '@/services/api';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';

const EmailOTPLogin = ({ onBack }) => {
    const navigate = useNavigate();
    const { loginWithOTP } = useAuthStore();
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState('email');
    const [isLoading, setIsLoading] = useState(false);
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

    const handleSendOTP = async (e) => {
        e.preventDefault();
        if (!email || !email.includes('@')) {
            toast.error('Please enter a valid email address');
            return;
        }
        setIsLoading(true);
        try {
            await authAPI.sendOTPForLogin({ email: email.trim().toLowerCase() });
            setStep('otp');
            setTimer(60);
            toast.success('OTP sent to your email! 📧');
        } catch (error) {
            console.error('Email OTP send error:', error);
            toast.error(error.response?.data?.detail || 'Failed to send OTP. Please try again.');
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
        const deviceId = localStorage.getItem('tb_device_id') ||
            (typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2));
        localStorage.setItem('tb_device_id', deviceId);
        try {
            await loginWithOTP({ email: email.trim().toLowerCase(), otp_code: otp.trim(), device_id: deviceId });
            toast.success('Login successful! Welcome to Luveloop 💕');
            navigate('/dashboard');
        } catch (error) {
            console.error('OTP verification error:', error);
            toast.error(error.response?.data?.detail || 'Invalid OTP code. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {step === 'email' ? (
                <form onSubmit={handleSendOTP} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Enter Email Address
                        </label>
                        <div className="relative group">
                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-rose-500 transition-colors">
                                <Mail size={20} />
                            </div>
                            <input
                                type="email"
                                autoComplete="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="hello@example.com"
                                className="w-full pl-12 pr-4 py-4 rounded-2xl border border-slate-200 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 outline-none transition-all text-lg"
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <p className="mt-3 text-xs text-slate-500 flex items-center gap-2">
                            <Shield size={14} className="text-emerald-500" />
                            We'll send a secure 6-digit code to your email
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || !email.includes('@')}
                        className="w-full py-4 bg-gradient-to-r from-rose-500 to-pink-600 text-white rounded-2xl font-bold shadow-lg shadow-rose-200 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:scale-100 disabled:shadow-none"
                    >
                        {isLoading ? (
                            <Loader2 className="animate-spin" size={24} />
                        ) : (
                            <>
                                <span>Send Verification Code</span>
                                <Sparkles size={20} />
                            </>
                        )}
                    </button>

                    {onBack && (
                        <button
                            type="button"
                            onClick={onBack}
                            className="w-full py-2 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors"
                        >
                            Back to Login Options
                        </button>
                    )}
                </form>
            ) : (
                <form onSubmit={handleVerifyOTP} className="space-y-6">
                    <div className="text-center space-y-2 mb-8">
                        <div className="w-16 h-16 bg-rose-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Shield className="text-rose-500" size={32} />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-800">Verify it's you</h2>
                        <p className="text-slate-500">
                            Enter the code sent to <span className="font-bold text-slate-700">{email}</span>
                        </p>
                    </div>

                    <div className="space-y-4">
                        <div className="relative">
                            <input
                                type="text"
                                inputMode="numeric"
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
                                onClick={() => { setStep('email'); setOtp(''); }}
                                className="text-slate-500 hover:text-rose-500 font-medium flex items-center gap-1 transition-colors"
                            >
                                <ArrowLeft size={14} /> Change Email
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

export default EmailOTPLogin;
