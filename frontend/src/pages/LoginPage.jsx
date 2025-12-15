import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Heart, Mail, Lock } from 'lucide-react';
import gsap from 'gsap';
import useAuthStore from '@/store/authStore';
import CustomCursor from '@/components/CustomCursor';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Floating widgets animation
      gsap.to('.widget-1', { y: -30, x: 10, rotation: 5, duration: 4, ease: 'sine.inOut', yoyo: true, repeat: -1 });
      gsap.to('.widget-2', { y: 20, x: -15, rotation: -3, duration: 5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 0.5 });
      gsap.to('.widget-3', { y: -20, x: 20, rotation: 8, duration: 4.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1 });
      gsap.to('.widget-4', { y: 25, x: -10, rotation: -5, duration: 5.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1.5 });
      gsap.to('.widget-5', { y: -15, x: 15, rotation: 4, duration: 4.2, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 0.8 });
      gsap.to('.widget-6', { y: 18, x: -20, rotation: -6, duration: 5.2, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1.2 });

      // Gradient blobs
      gsap.to('.blob-login-1', { x: 40, y: -30, duration: 8, ease: 'sine.inOut', yoyo: true, repeat: -1 });
      gsap.to('.blob-login-2', { x: -30, y: 40, duration: 10, ease: 'sine.inOut', yoyo: true, repeat: -1 });

      // Pulsing dots
      gsap.to('.pulse-dot', { scale: 1.5, opacity: 0.3, duration: 2, ease: 'sine.inOut', yoyo: true, repeat: -1, stagger: 0.3 });

      // Form entrance
      gsap.from('.login-card', { y: 60, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.3 });
      gsap.from('.login-title', { y: 30, opacity: 0, duration: 0.8, ease: 'power3.out', delay: 0.5 });
      gsap.from('.login-field', { y: 20, opacity: 0, duration: 0.6, stagger: 0.1, ease: 'power3.out', delay: 0.7 });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(formData.email, formData.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={containerRef} className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center p-6 relative overflow-hidden">
      <CustomCursor />

      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Blobs */}
        <div className="blob-login-1 absolute top-[10%] left-[10%] w-[400px] h-[400px] rounded-full bg-purple-200/50 blur-[80px]" />
        <div className="blob-login-2 absolute bottom-[10%] right-[10%] w-[500px] h-[500px] rounded-full bg-pink-200/50 blur-[100px]" />

        {/* Floating Widget Cards */}
        <div className="widget-1 absolute top-[15%] left-[10%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400" />
            <div className="w-20 h-3 bg-gray-200 rounded" />
          </div>
        </div>

        <div className="widget-2 absolute top-[25%] right-[15%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex items-center gap-2">
            <Heart size={20} className="text-pink-500" fill="currentColor" />
            <span className="text-sm font-medium text-gray-700">New match!</span>
          </div>
        </div>

        <div className="widget-3 absolute bottom-[30%] left-[8%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-green-500" />
            </div>
            <span className="text-sm text-gray-600">5 online nearby</span>
          </div>
        </div>

        <div className="widget-4 absolute bottom-[20%] right-[10%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex gap-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-300 to-pink-300" />
            ))}
          </div>
        </div>

        <div className="widget-5 absolute top-[45%] left-[20%] bg-white rounded-xl p-3 shadow-lg">
          <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-purple-100 to-pink-100" />
        </div>

        <div className="widget-6 absolute top-[60%] right-[20%] bg-white rounded-xl p-3 shadow-lg">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-purple-500" />
            <div className="w-12 h-2 bg-gray-200 rounded" />
          </div>
        </div>

        {/* Pulsing Dots */}
        <div className="pulse-dot absolute top-[20%] left-[30%] w-4 h-4 rounded-full bg-purple-400" />
        <div className="pulse-dot absolute top-[40%] right-[25%] w-3 h-3 rounded-full bg-pink-400" />
        <div className="pulse-dot absolute bottom-[35%] left-[25%] w-5 h-5 rounded-full bg-purple-300" />
        <div className="pulse-dot absolute bottom-[25%] right-[30%] w-4 h-4 rounded-full bg-pink-300" />
      </div>

      {/* Login Card */}
      <div className="login-card relative z-10 bg-white/80 backdrop-blur-xl rounded-3xl p-10 w-full max-w-md shadow-2xl shadow-purple-200/30">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Heart size={28} className="text-white" fill="white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">TrueBond</span>
        </div>

        <div className="login-title text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
          <p className="text-gray-500">Sign in to continue your journey</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl mb-6 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="login-field">
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <div className="relative">
              <Mail size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="input pl-12"
                placeholder="hello@example.com"
                required
              />
            </div>
          </div>

          <div className="login-field">
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="input pl-12 pr-12"
                placeholder="••••••••"
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

          <button
            type="submit"
            disabled={loading}
            className="login-field btn-primary w-full py-4 text-lg disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-gray-500 mt-8">
          Don't have an account?{' '}
          <Link to="/signup" className="text-purple-600 font-semibold hover:underline">
            Sign up
          </Link>
        </p>

        <Link to="/" className="block text-center text-gray-400 hover:text-gray-600 mt-4 text-sm">
          ← Back to home
        </Link>
      </div>
    </div>
  );
};

export default LoginPage;
