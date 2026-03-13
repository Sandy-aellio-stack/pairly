import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles, Phone, Shield, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import useAuthStore from '@/store/authStore';
import { authAPI } from '@/services/api';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, loginWithOTP } = useAuthStore();
  const [activeTab, setActiveTab] = useState('password');
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // OTP state
  const [otpIdentifier, setOtpIdentifier] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [devOtp, setDevOtp] = useState('');
  const [isSendingOtp, setIsSendingOtp] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(formData.email, formData.password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendOtp = async (e) => {
    e.preventDefault();
    if (!otpIdentifier.trim()) {
      toast.error('Please enter your email or phone');
      return;
    }
    setIsSendingOtp(true);
    try {
      const isEmail = otpIdentifier.includes('@');
      let response;
      if (isEmail) {
        response = await authAPI.sendOTPForLogin({ email: otpIdentifier.trim() });
      } else {
        response = await authAPI.sendOTPForLogin({ mobile_number: otpIdentifier.trim() });
      }
      setOtpSent(true);
      if (response.data?.dev_otp) {
        setDevOtp(response.data.dev_otp);
        setOtpCode(response.data.dev_otp);
        toast.info(`Dev OTP: ${response.data.dev_otp}`, { duration: 10000 });
      } else {
        toast.success('OTP sent! Check your email or phone.');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setIsSendingOtp(false);
    }
  };

  const handleOtpLogin = async (e) => {
    e.preventDefault();
    if (!otpCode.trim()) {
      toast.error('Please enter the OTP');
      return;
    }
    setIsLoading(true);
    try {
      const device_id = localStorage.getItem('tb_device_id') ||
        (typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Math.random().toString(36).substring(2));
      localStorage.setItem('tb_device_id', device_id);

      const isEmail = otpIdentifier.includes('@');
      const payload = isEmail
        ? { email: otpIdentifier.trim(), otp_code: otpCode.trim(), device_id }
        : { mobile_number: otpIdentifier.trim(), otp_code: otpCode.trim(), device_id };

      await loginWithOTP(payload);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Romantic Background */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#E8D5E7] via-[#F5E6E8] to-[#FDE8D7]" />
        <div className="absolute top-20 left-10 w-64 h-64 bg-pink-300/30 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-80 h-80 bg-orange-200/30 rounded-full blur-3xl" />
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-12">
          <img
            src="https://customer-assets.emergentagent.com/job_truebond-notify/artifacts/8q937866_Gemini_Generated_Image_c05duoc05duoc05d.png"
            alt="Luveloop - Find your match"
            className="w-full max-w-md object-contain mb-8 drop-shadow-2xl rounded-2xl"
          />
          <div className="text-center">
            <h2 className="text-3xl font-bold text-[#0F172A] mb-3">Welcome Back to Luveloop</h2>
            <p className="text-lg text-gray-700">Your next meaningful connection is waiting ✨</p>
          </div>
          <div className="absolute top-1/4 left-1/4 animate-pulse">
            <Heart size={24} className="text-pink-400" fill="currentColor" />
          </div>
          <div className="absolute bottom-1/3 right-1/4 animate-pulse delay-200">
            <Heart size={18} className="text-rose-400" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
        <div className="w-full max-w-md">
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
          <p className="text-gray-600 mb-6">Sign in to continue your journey to love</p>

          {/* Tab Switcher */}
          <div className="flex bg-gray-100 rounded-xl p-1 mb-6">
            <button
              onClick={() => setActiveTab('password')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'password'
                  ? 'bg-white shadow-sm text-[#0F172A]'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Lock size={16} />
              Password
            </button>
            <button
              onClick={() => { setActiveTab('otp'); setOtpSent(false); setDevOtp(''); setOtpCode(''); }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'otp'
                  ? 'bg-white shadow-sm text-[#0F172A]'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Shield size={16} />
              OTP Login
            </button>
          </div>

          {activeTab === 'password' ? (
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
                  <Loader2 size={20} className="animate-spin" />
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
              {!otpSent ? (
                <form onSubmit={handleSendOtp} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-[#0F172A] mb-2">
                      Email or Phone Number
                    </label>
                    <div className="relative">
                      <Phone size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        value={otpIdentifier}
                        onChange={(e) => setOtpIdentifier(e.target.value)}
                        placeholder="email@example.com or +91xxxxxxxxxx"
                        className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all"
                        required
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={isSendingOtp}
                    className="w-full py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                  >
                    {isSendingOtp ? (
                      <Loader2 size={20} className="animate-spin" />
                    ) : (
                      <>
                        <Shield size={20} />
                        Send OTP
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleOtpLogin} className="space-y-4">
                  <div className="p-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700">
                    OTP sent to <strong>{otpIdentifier}</strong>
                    {devOtp && <span className="ml-1">(Dev mode: <strong>{devOtp}</strong>)</span>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#0F172A] mb-2">
                      Enter OTP
                    </label>
                    <div className="relative">
                      <Shield size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="6-digit OTP"
                        maxLength={6}
                        className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-pink-500 focus:ring-2 focus:ring-pink-200 outline-none transition-all tracking-widest text-center text-2xl font-bold"
                        required
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading || otpCode.length < 6}
                    className="w-full py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                  >
                    {isLoading ? (
                      <Loader2 size={20} className="animate-spin" />
                    ) : (
                      <>
                        <span>Verify & Sign In</span>
                        <ArrowRight size={20} />
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setOtpSent(false); setDevOtp(''); setOtpCode(''); }}
                    className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    Change email/phone
                  </button>
                </form>
              )}
            </div>
          )}

          <div className="mt-8 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="text-pink-600 hover:text-pink-700 font-semibold">
                Sign up free
              </Link>
            </p>
          </div>

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
