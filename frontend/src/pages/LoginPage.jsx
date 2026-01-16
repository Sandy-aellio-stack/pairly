import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';
import HeartCursor from '@/components/HeartCursor';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

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

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex">
      <HeartCursor />
      
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-[#0F172A] flex items-center justify-center">
              <Heart size={24} className="text-white" fill="white" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">Luveloop</span>
          </Link>

          <h1 className="text-3xl font-bold text-[#0F172A] mb-2">Welcome back</h1>
          <p className="text-gray-600 mb-8">Sign in to continue your journey</p>

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
                  className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
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
                  placeholder="Min 8 characters"
                  className="w-full pl-12 pr-12 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
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
              <label className="flex items-center">
                <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-[#0F172A] focus:ring-[#E9D5FF]" />
                <span className="ml-2 text-sm text-gray-600">Remember me</span>
              </label>
              <Link to="/forgot-password" className="text-sm text-[#0F172A] font-medium hover:underline">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
              <ArrowRight size={20} />
            </button>
          </form>

          <p className="text-center mt-8 text-gray-600">
            Don't have an account?{' '}
            <Link to="/signup" className="text-[#0F172A] font-semibold hover:underline">
              Create one
            </Link>
          </p>
        </div>
      </div>

      {/* Right Side - Image */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] items-center justify-center p-12">
        <div className="max-w-lg text-center">
          <div className="relative">
            <div className="w-64 h-64 mx-auto rounded-full bg-white/30 backdrop-blur-sm flex items-center justify-center">
              <Heart size={120} className="text-rose-400" fill="currentColor" />
            </div>
            <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-white shadow-lg flex items-center justify-center animate-float">
              <span className="text-3xl">💕</span>
            </div>
            <div className="absolute -bottom-4 -left-4 w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center animate-float-delay-1">
              <span className="text-2xl">✨</span>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-[#0F172A] mt-8">Find Your True Connection</h2>
          <p className="text-gray-600 mt-2">Join thousands who have found meaningful relationships</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
