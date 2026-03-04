import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles, Phone, Shield, ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import useAuthStore from '@/store/authStore';
import { authAPI } from '@/services/api';
import PhoneLogin from '@/components/auth/PhoneLogin';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, checkLoginStatus } = useAuthStore();
  const [loginType, setLoginType] = useState('password'); // 'password' | 'otp'
  const [otpMethod, setOtpMethod] = useState('mobile'); // 'mobile' | 'email'
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [otpData, setOtpData] = useState({
    mobile_number: '',
    email: '',
    otp_code: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isOtpSent, setIsOtpSent] = useState(false);

  // Single session approval state
  const [pendingSessionId, setPendingSessionId] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollingInterval = useRef(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleOtpChange = (e) => {
    setOtpData({ ...otpData, [e.target.name]: e.target.value });
  };

  const startPolling = (sessionId) => {
    setPendingSessionId(sessionId);
    setIsPolling(true);

    pollingInterval.current = setInterval(async () => {
      try {
        const result = await checkLoginStatus(sessionId);
        if (result.status === 'approved') {
          clearInterval(pollingInterval.current);
          toast.success('Login approved! 💕');
          navigate('/dashboard');
        } else if (result.status === 'denied') {
          clearInterval(pollingInterval.current);
          setIsPolling(false);
          setPendingSessionId(null);
          toast.error('Login request was denied by your other device.');
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000);
  };

  useEffect(() => {
    return () => {
      if (pollingInterval.current) clearInterval(pollingInterval.current);
    };
  }, []);

  const handleSendOtp = async () => {
    if (!otpData.mobile_number || otpData.mobile_number.length < 10) {
      toast.error('Please enter a valid mobile number');
      return;
    }
    setIsLoading(true);
    try {
      await authAPI.sendOTP(otpData.mobile_number);
      setIsOtpSent(true);
      toast.success('OTP sent successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await login(formData.email, formData.password);

      if (response.status === 'WAITING_FOR_APPROVAL') {
        startPolling(response.pending_session_id);
        return;
      }

      toast.success('Welcome back! 💕');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpLogin = async (e) => {
    e.preventDefault();
    if (!otpData.otp_code) {
      toast.error('Please enter the OTP code');
      return;
    }
    setIsLoading(true);
    try {
      const device_id = localStorage.getItem('tb_device_id') || Math.random().toString(36).substring(7);

      const loginPayload = {
        otp_code: otpData.otp_code,
        device_id
      };

      if (otpMethod === 'mobile') {
        loginPayload.mobile_number = otpData.mobile_number;
      } else {
        loginPayload.email = otpData.email;
      }

      const response = await authAPI.loginWithOTP(loginPayload);

      if (response.data.status === 'WAITING_FOR_APPROVAL') {
        startPolling(response.data.pending_session_id);
        return;
      }

      const { tokens, user_id } = response.data;
      if (tokens) {
        localStorage.setItem('tb_access_token', tokens.access_token);
        localStorage.setItem('tb_refresh_token', tokens.refresh_token);
      }

      toast.success('Welcome back! 💕');
      window.location.reload();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="min-h-screen flex">
      {/* Left Side - Romantic Background with Image */}
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
            alt="Luveloop - Find your match"
            className="w-full max-w-md object-contain mb-8 drop-shadow-2xl rounded-2xl"
          />

          {/* Tagline */}
          <div className="text-center">
            <h2 className="text-3xl font-bold text-[#0F172A] mb-3">
              Welcome Back to Luveloop
            </h2>
            <p className="text-lg text-gray-700">
              Your next meaningful connection is waiting ✨
            </p>
          </div>

          {/* Floating hearts */}
          <div className="absolute top-1/4 left-1/4 animate-pulse">
            <Heart size={24} className="text-pink-400" fill="currentColor" />
          </div>
          <div className="absolute bottom-1/3 right-1/4 animate-pulse delay-200">
            <Heart size={18} className="text-rose-400" fill="currentColor" />
          </div>
          <div className="absolute top-1/2 right-1/6 animate-pulse delay-500">
            <Heart size={20} className="text-pink-300" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
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
            <Sparkles size={20} className="text-pink-500" />
            <h1 className="text-3xl font-bold text-[#0F172A]">Welcome back</h1>
          </div>
          <p className="text-gray-600 mb-8">Sign in to continue your journey to love</p>

          {isPolling ? (
            <div className="text-center py-8 animate-in fade-in duration-500">
              <div className="w-20 h-20 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-6 relative">
                <Shield className="text-pink-600 animate-pulse" size={40} />
                <div className="absolute inset-0 border-4 border-pink-500 border-t-transparent rounded-full animate-spin"></div>
              </div>

              <h2 className="text-2xl font-bold text-[#0F172A] mb-3">Waiting for Approval</h2>
              <p className="text-gray-600 mb-8 max-w-sm mx-auto">
                We've sent a notification to your other active device.
                Please approve this login to continue.
              </p>

              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-center gap-2 text-pink-600 font-medium bg-pink-50 py-3 rounded-xl">
                  <Loader2 className="animate-spin" size={20} />
                  <span>Checking status...</span>
                </div>

                <button
                  onClick={() => {
                    if (pollingInterval.current) clearInterval(pollingInterval.current);
                    setIsPolling(false);
                    setPendingSessionId(null);
                  }}
                  className="text-gray-500 hover:text-gray-700 text-sm font-medium transition-colors"
                >
                  Cancel and try again
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Tab Toggle */}
              <div className="flex p-1 bg-gray-100 rounded-xl mb-8">
                <button
                  onClick={() => setLoginType('password')}
                  className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${loginType === 'password' ? 'bg-white text-pink-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  Password
                </button>
                <button
                  onClick={() => setLoginType('otp')}
                  className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${loginType === 'otp' ? 'bg-white text-pink-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  OTP Login
                </button>
              </div>

              {loginType === 'password' ? (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-[#0F172A] mb-2">Email</label>
                    <div className="relative">
                      <Mail size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="hello@example.com"
                        className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#0F172A] mb-2">Password</label>
                    <div className="relative">
                      <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="Your password"
                        className="w-full pl-12 pr-12 py-4 rounded-xl border border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="flex items-center cursor-pointer">
                      <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-pink-500 focus:ring-pink-200" />
                      <span className="ml-2 text-sm text-gray-600">Remember me</span>
                    </label>
                    <Link to="/forgot-password" className="text-sm text-pink-600 hover:text-pink-700 font-medium">
                      Forgot password?
                    </Link>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <span>Signing in...</span>
                    ) : (
                      <>
                        <span>Sign In</span>
                        <ArrowRight size={20} />
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <div className="space-y-6">
                  {/* OTP Method Toggle - Always visible in OTP mode */}
                  <div className="flex p-1 bg-gray-50 rounded-lg border border-gray-100 mb-6">
                    <button
                      type="button"
                      onClick={() => { setOtpMethod('mobile'); setIsOtpSent(false); }}
                      className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${otpMethod === 'mobile' ? 'bg-white text-pink-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                    >
                      <div className="flex items-center justify-center gap-1.5">
                        <Phone size={14} /> Mobile
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => { setOtpMethod('email'); setIsOtpSent(false); }}
                      className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${otpMethod === 'email' ? 'bg-white text-pink-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                    >
                      <div className="flex items-center justify-center gap-1.5">
                        <Mail size={14} /> Email
                      </div>
                    </button>
                  </div>

                  {otpMethod === 'mobile' ? (
                    <PhoneLogin onBack={() => setLoginType('password')} />
                  ) : (
                    <div className="space-y-6">
                      {/* Email OTP Flow */}
                      <div>
                        <label className="block text-sm font-medium text-[#0F172A] mb-2">Email Address</label>
                        <div className="relative">
                          <Mail size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                          <input
                            type="email"
                            name="email"
                            value={otpData.email}
                            onChange={handleOtpChange}
                            placeholder="hello@example.com"
                            className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all"
                            required
                            disabled={isOtpSent}
                          />
                        </div>
                      </div>

                      {isOtpSent && (
                        <div className="animate-in slide-in-from-top-4 duration-300">
                          <label className="block text-sm font-medium text-[#0F172A] mb-2">Verification Code</label>
                          <div className="relative">
                            <Shield size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                              type="text"
                              name="otp_code"
                              value={otpData.otp_code}
                              onChange={handleOtpChange}
                              placeholder="6-digit code"
                              maxLength={6}
                              className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all tracking-[0.5em] font-mono text-center text-lg"
                              required
                            />
                          </div>
                        </div>
                      )}

                      {!isOtpSent ? (
                        <button
                          type="button"
                          onClick={async () => {
                            if (!otpData.email) return toast.error('Please enter email');
                            setIsLoading(true);
                            try {
                              await authAPI.sendEmailOTP(otpData.email);
                              setIsOtpSent(true);
                              toast.success('OTP sent to your email!');
                            } catch (error) {
                              toast.error(error.response?.data?.detail || 'Failed to send OTP');
                            } finally {
                              setIsLoading(false);
                            }
                          }}
                          disabled={isLoading || !otpData.email}
                          className="w-full py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                          {isLoading ? <span>Sending...</span> : <span>Get Verification Code</span>}
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={async () => {
                            if (!otpData.otp_code) return toast.error('Please enter code');
                            setIsLoading(true);
                            try {
                              const response = await authAPI.verifyEmailOTP(otpData.email, otpData.otp_code);
                              if (response.data.verified) {
                                // Logic for what happens after email verification could go here 
                                // (e.g. calling login, or just redirection)
                                toast.success('Verified! Redirecting...');
                                navigate('/dashboard');
                                window.location.reload();
                              }
                            } catch (error) {
                              toast.error(error.response?.data?.detail || 'Invalid OTP');
                            } finally {
                              setIsLoading(false);
                            }
                          }}
                          disabled={isLoading || !otpData.otp_code}
                          className="w-full py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                          {isLoading ? <span>Verifying...</span> : <span>Verify & Sign In</span>}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          <div className="mt-8 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="text-pink-600 hover:text-pink-700 font-semibold">
                Sign up free
              </Link>
            </p>
          </div>

          {/* Social proof */}
          <div className="mt-8 pt-8 border-t border-gray-100">
            <div className="flex items-center justify-center gap-4">
              <div className="flex -space-x-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-400 to-rose-400 border-2 border-white" />
                ))}
              </div>
              <p className="text-sm text-gray-600">
                <span className="font-semibold text-[#0F172A]">10,000+</span> people found love
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
