import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, Eye, EyeOff, ArrowRight, User, Check } from 'lucide-react';
import { toast } from 'sonner';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';
import HeartCursor from '@/components/HeartCursor';

const SignupPage = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreeTerms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleNextStep = () => {
    if (step === 1 && !formData.name) {
      toast.error('Please enter your name');
      return;
    }
    if (step === 2 && !formData.email) {
      toast.error('Please enter your email');
      return;
    }
    setStep(step + 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (!formData.agreeTerms) {
      toast.error('Please agree to the terms and conditions');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post('/auth/signup', {
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });
      login(response.data.user, response.data.token);
      toast.success('Welcome to TrueBond! 🎉');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const steps = [
    { num: 1, label: 'Name' },
    { num: 2, label: 'Email' },
    { num: 3, label: 'Password' },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex">
      <HeartCursor />
      
      {/* Left Side - Image */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] items-center justify-center p-12">
        <div className="max-w-lg text-center">
          <div className="relative">
            <div className="w-64 h-64 mx-auto rounded-full bg-white/30 backdrop-blur-sm flex items-center justify-center">
              <Heart size={120} className="text-rose-400" fill="currentColor" />
            </div>
            <div className="absolute -top-4 -left-4 w-20 h-20 rounded-full bg-white shadow-lg flex items-center justify-center animate-float">
              <span className="text-3xl">🌟</span>
            </div>
            <div className="absolute -bottom-4 -right-4 w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center animate-float-delay-1">
              <span className="text-2xl">💝</span>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-[#0F172A] mt-8">Start Your Journey</h2>
          <p className="text-gray-600 mt-2">Create meaningful connections that last a lifetime</p>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-[#0F172A] flex items-center justify-center">
              <Heart size={24} className="text-white" fill="white" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">TrueBond</span>
          </Link>

          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-8">
            {steps.map((s, i) => (
              <div key={s.num} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                  step >= s.num ? 'bg-[#0F172A] text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  {step > s.num ? <Check size={20} /> : s.num}
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-16 h-1 mx-2 rounded transition-all ${
                    step > s.num ? 'bg-[#0F172A]' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>

          <h1 className="text-3xl font-bold text-[#0F172A] mb-2">Create Account</h1>
          <p className="text-gray-600 mb-8">Step {step} of 3: {steps[step - 1].label}</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {step === 1 && (
              <div>
                <label className="block text-sm font-medium text-[#0F172A] mb-2">Full Name</label>
                <div className="relative">
                  <User size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Your name"
                    className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
                    required
                  />
                </div>
              </div>
            )}

            {step === 2 && (
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
            )}

            {step === 3 && (
              <>
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
                      minLength={8}
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

                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">Confirm Password</label>
                  <div className="relative">
                    <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Confirm your password"
                      className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
                      required
                    />
                  </div>
                </div>

                <label className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    name="agreeTerms"
                    checked={formData.agreeTerms}
                    onChange={handleChange}
                    className="w-5 h-5 rounded border-gray-300 text-[#0F172A] focus:ring-[#E9D5FF] mt-0.5"
                  />
                  <span className="text-sm text-gray-600">
                    I agree to the{' '}
                    <Link to="/terms" className="text-[#0F172A] font-medium hover:underline">Terms of Service</Link>
                    {' '}and{' '}
                    <Link to="/privacy" className="text-[#0F172A] font-medium hover:underline">Privacy Policy</Link>
                  </span>
                </label>
              </>
            )}

            {step < 3 ? (
              <button
                type="button"
                onClick={handleNextStep}
                className="w-full py-4 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2"
              >
                Continue
                <ArrowRight size={20} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-4 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? 'Creating Account...' : 'Create Account'}
                <ArrowRight size={20} />
              </button>
            )}

            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="w-full py-3 text-gray-600 font-medium hover:text-[#0F172A] transition-all"
              >
                ← Go Back
              </button>
            )}
          </form>

          <p className="text-center mt-8 text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-[#0F172A] font-semibold hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
