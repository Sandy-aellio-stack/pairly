import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Heart, ArrowRight, Mail, RefreshCw, CheckCircle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { authAPI } from '@/services/api';

const VerifyOTPPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const inputRefs = useRef([]);

  // Get email/mobile from location state or localStorage
  const email = location.state?.email || localStorage.getItem('verify_email') || '';
  const mobile = location.state?.mobile_number || localStorage.getItem('verify_mobile') || '';
  const verificationType = email ? 'email' : 'mobile';

  useEffect(() => {
    // Save for page refresh
    if (email) localStorage.setItem('verify_email', email);
    if (mobile) localStorage.setItem('verify_mobile', mobile);

    // Focus first input
    inputRefs.current[0]?.focus();

    // Countdown timer
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          setCanResend(true);
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    for (let i = 0; i < pastedData.length; i++) {
      newOtp[i] = pastedData[i];
    }
    setOtp(newOtp);
    inputRefs.current[Math.min(pastedData.length, 5)]?.focus();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const otpCode = otp.join('');
    
    if (otpCode.length !== 6) {
      toast.error('Please enter the complete 6-digit code');
      return;
    }

    setIsLoading(true);
    try {
      if (verificationType === 'email') {
        await authAPI.verifyEmailOTP(email, otpCode);
      } else {
        await authAPI.verifyOTP(mobile, otpCode);
      }
      
      toast.success('Verification successful! 🎉');
      localStorage.removeItem('verify_email');
      localStorage.removeItem('verify_mobile');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    try {
      if (verificationType === 'email') {
        await authAPI.sendEmailOTP(email);
        toast.success('New code sent to your email!');
      } else {
        await authAPI.sendOTP(mobile);
        toast.success('New code sent to your phone!');
      }
      setCountdown(60);
      setCanResend(false);
    } catch (error) {
      toast.error('Failed to resend code');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Romantic Background */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#E8D5E7] via-[#F5E6E8] to-[#FDE8D7]" />
        
        {/* Decorative blobs */}
        <div className="absolute top-20 left-10 w-64 h-64 bg-pink-300/30 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-80 h-80 bg-orange-200/30 rounded-full blur-3xl" />
        
        {/* Main Content */}
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-12">
          {/* Hero Image */}
          <img 
            src="https://customer-assets.emergentagent.com/job_truebond-notify/artifacts/8q937866_Gemini_Generated_Image_c05duoc05duoc05d.png" 
            alt="Almost there!" 
            className="w-full max-w-md object-contain mb-8 drop-shadow-2xl rounded-2xl"
          />
          
          {/* Tagline */}
          <div className="text-center">
            <h2 className="text-3xl font-bold text-[#0F172A] mb-3">
              Almost There! 🎉
            </h2>
            <p className="text-lg text-gray-700">
              Verify your {verificationType} to start meeting amazing people
            </p>
          </div>
          
          {/* Floating hearts */}
          <div className="absolute top-1/4 left-1/4 animate-pulse">
            <Heart size={24} className="text-pink-400" fill="currentColor" />
          </div>
          <div className="absolute bottom-1/3 right-1/4 animate-pulse delay-200">
            <Heart size={18} className="text-rose-400" fill="currentColor" />
          </div>
        </div>
      </div>
      
      {/* Right Side - OTP Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
        <div className="w-full max-w-md">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center shadow-lg">
              <Heart size={24} className="text-white" fill="white" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">Luveloop</span>
          </Link>

          <div className="flex items-center gap-2 mb-2">
            <CheckCircle size={24} className="text-pink-500" />
            <h1 className="text-3xl font-bold text-[#0F172A]">Verify Your {verificationType === 'email' ? 'Email' : 'Phone'}</h1>
          </div>
          <p className="text-gray-600 mb-8">
            We sent a 6-digit code to{' '}
            <span className="font-semibold text-[#0F172A]">
              {verificationType === 'email' ? email : mobile}
            </span>
          </p>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* OTP Input */}
            <div>
              <label className="block text-sm font-medium text-[#0F172A] mb-4 text-center">
                Enter verification code
              </label>
              <div className="flex justify-center gap-3" onPaste={handlePaste}>
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
                    className="w-14 h-16 text-center text-2xl font-bold rounded-xl border-2 border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all"
                    required
                  />
                ))}
              </div>
            </div>

            {/* Resend Code */}
            <div className="text-center">
              {canResend ? (
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={isResending}
                  className="text-pink-600 hover:text-pink-700 font-medium flex items-center justify-center gap-2 mx-auto"
                >
                  <RefreshCw size={18} className={isResending ? 'animate-spin' : ''} />
                  {isResending ? 'Sending...' : 'Resend Code'}
                </button>
              ) : (
                <p className="text-gray-500">
                  Resend code in <span className="font-semibold text-pink-600">{countdown}s</span>
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || otp.join('').length !== 6}
              className="w-full py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span>Verifying...</span>
              ) : (
                <>
                  <span>Verify & Continue</span>
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-gray-500 text-sm">
              Didn't receive the code? Check your {verificationType === 'email' ? 'spam folder' : 'messages'}
            </p>
          </div>
          
          {/* Back to login */}
          <div className="mt-6 text-center">
            <Link to="/login" className="text-pink-600 hover:text-pink-700 font-medium">
              ← Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyOTPPage;
