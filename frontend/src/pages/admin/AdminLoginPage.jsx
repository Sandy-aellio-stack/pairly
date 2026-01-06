import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import useAdminStore from '@/store/adminStore';
import HeartCursor from '@/components/HeartCursor';

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAdminStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome to Admin Dashboard!');
      navigate('/admin');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F172A] flex items-center justify-center p-4 lg:cursor-none">
      <HeartCursor />
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-[#E9D5FF] flex items-center justify-center mx-auto mb-4">
            <Heart size={32} className="text-[#0F172A]" fill="currentColor" />
          </div>
          <h1 className="text-2xl font-bold text-white">TrueBond Admin</h1>
          <p className="text-white/60 mt-2">Sign in to manage your platform</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-8 shadow-xl">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@truebond.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                  required
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-6 py-3 bg-[#0F172A] text-white rounded-xl font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isLoading ? (
              <><Loader2 size={18} className="animate-spin" /> Signing in...</>
            ) : (
              'Sign In'
            )}
          </button>

          {/* Demo Credentials */}
          <div className="mt-6 p-4 bg-gray-50 rounded-xl">
            <p className="text-sm font-medium text-gray-700 mb-2">Demo Credentials:</p>
            <p className="text-xs text-gray-500">Super Admin: admin@truebond.com / admin123</p>
            <p className="text-xs text-gray-500">Moderator: moderator@truebond.com / mod123</p>
          </div>
        </form>

        {/* Back Link */}
        <div className="text-center mt-6">
          <a href="/" className="text-white/60 hover:text-white text-sm">
            ← Back to TrueBond
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
