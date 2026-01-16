import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Heart, ArrowLeft, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { authAPI } from '@/services/api';
import HeartCursor from '@/components/HeartCursor';

const VerifyOTPPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const inputRefs = useRef([]);

  const mobileNumber = location.state?.mobileNumber || '';

  useEffect(() => {
    if (!mobileNumber) {
      toast.error('Please sign up first');
      navigate('/signup');
      return;
    }
    inputRefs.current[0]?.focus();
  }, [mobileNumber, navigate]);

  useEffect(() => {
    if (countdown > 0 && !canResend) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (countdown === 0) {
      setCanResend(true);
    }
  }, [countdown, canResend]);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (newOtp.every(digit => digit) && index === 5) {
      handleVerify(newOtp.join(''));
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    if (!/^\d+$/.test(pastedData)) return;

    const newOtp = [...otp];
    pastedData.split('').forEach((digit, index) => {
      if (index < 6) newOtp[index] = digit;
    });
    setOtp(newOtp);

    if (pastedData.length === 6) {
      handleVerify(pastedData);
    }
  };

  const handleVerify = async (otpCode) => {
    setIsLoading(true);
    try {
      await authAPI.verifyOTP(mobileNumber, otpCode);
      toast.success('Phone number verified successfully!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP');
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (!canResend) return;
    
    setIsResending(true);
    try {
      await authAPI.sendOTP(mobileNumber);
      toast.success('New OTP sent!');
      setCountdown(60);
      setCanResend(false);
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to resend OTP');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] flex items-center justify-center p-6">
      <HeartCursor />
      
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-[#0F172A] flex items-center justify-center">
            <Heart size={24} className="text-white" fill="white" />
          </div>
          <span className="text-2xl font-bold text-[#0F172A]">Luveloop</span>
        </div>

        <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Verify Your Phone</h1>
        <p className="text-gray-600 mb-8">
          We sent a 6-digit code to <span className="font-medium">{mobileNumber}</span>
        </p>

        <div className="flex gap-3 justify-center mb-8" onPaste={handlePaste}>
          {otp.map((digit, index) => (
            <input
              key={index}
              ref={(el) => (inputRefs.current[index] = el)}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className="w-12 h-14 text-center text-xl font-bold border-2 border-gray-200 rounded-xl focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
              disabled={isLoading}
            />
          ))}
        </div>

        <button
          onClick={() => handleVerify(otp.join(''))}
          disabled={isLoading || otp.some(d => !d)}
          className="w-full py-4 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all disabled:opacity-50 mb-6"
        >
          {isLoading ? 'Verifying...' : 'Verify'}
        </button>

        <div className="text-center">
          {canResend ? (
            <button
              onClick={handleResend}
              disabled={isResending}
              className="flex items-center gap-2 mx-auto text-[#0F172A] font-medium hover:underline"
            >
              <RefreshCw size={16} className={isResending ? 'animate-spin' : ''} />
              Resend Code
            </button>
          ) : (
            <p className="text-gray-600">
              Resend code in <span className="font-medium text-[#0F172A]">{countdown}s</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyOTPPage;
