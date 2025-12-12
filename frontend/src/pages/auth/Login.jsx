import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { Heart, Mail, Lock, ArrowRight } from 'lucide-react';

const backgroundImages = [
  'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/szubcfsh_0f9404175493827.64b512011929a.jpg',
  'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/i7v9p713_3d3d2a175493827.64b51201182d8.jpg',
  'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/m35haapv_21e4fe175493827.64b572b9e145b.jpg',
  'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/vvcj2l4m_b99991175493827.64b512011a181.jpg',
  'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/r4v2oh1b_ca35f1192469755.Y3JvcCwxNjgzLDEzMTYsMCww.jpg',
];

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentBgIndex, setCurrentBgIndex] = useState(0);
  const [nextBgIndex, setNextBgIndex] = useState(1);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Background image rotation
  useEffect(() => {
    const interval = setInterval(() => {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentBgIndex(nextBgIndex);
        setNextBgIndex((nextBgIndex + 1) % backgroundImages.length);
        setIsTransitioning(false);
      }, 1000);
    }, 4000);

    return () => clearInterval(interval);
  }, [nextBgIndex]);

  // Parallax effect on mouse move
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (containerRef.current) {
        const { clientX, clientY } = e;
        const { innerWidth, innerHeight } = window;
        const x = (clientX / innerWidth - 0.5) * 20;
        const y = (clientY / innerHeight - 0.5) * 20;
        setMousePosition({ x, y });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(formData.email, formData.password);
      
      if (result.requires_2fa) {
        navigate('/2fa', { state: { email: formData.email, tempToken: result.temp_token } });
      } else {
        toast.success('Welcome back!');
        navigate('/home');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={containerRef} className="min-h-screen relative overflow-hidden flex flex-col">
      {/* Animated Background Images */}
      <div className="absolute inset-0">
        {/* Current background */}
        <div
          className="absolute inset-0 transition-opacity duration-1000"
          style={{
            opacity: isTransitioning ? 0 : 1,
            transform: `translate(${mousePosition.x}px, ${mousePosition.y}px) scale(1.1)`,
            transition: 'opacity 1s ease-in-out, transform 0.3s ease-out',
          }}
        >
          <img
            src={backgroundImages[currentBgIndex]}
            alt="Background"
            className="w-full h-full object-cover"
          />
        </div>
        
        {/* Next background (for crossfade) */}
        <div
          className="absolute inset-0 transition-opacity duration-1000"
          style={{
            opacity: isTransitioning ? 1 : 0,
            transform: `translate(${mousePosition.x}px, ${mousePosition.y}px) scale(1.1)`,
            transition: 'opacity 1s ease-in-out, transform 0.3s ease-out',
          }}
        >
          <img
            src={backgroundImages[nextBgIndex]}
            alt="Background Next"
            className="w-full h-full object-cover"
          />
        </div>

        {/* Gradient overlay for readability */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/80 via-violet-900/60 to-fuchsia-900/70" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-transparent to-slate-900/40" />
      </div>

      {/* Header */}
      <div className="relative z-10 p-4">
        <Link to="/" className="flex items-center gap-2 w-fit">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/30">
            <Heart className="h-5 w-5 text-white" />
          </div>
          <span className="text-2xl font-bold text-white drop-shadow-lg">
            Pairly
          </span>
        </Link>
      </div>

      {/* Login Form */}
      <div className="relative z-10 flex-1 flex items-center justify-center px-4 py-8">
        <Card className="w-full max-w-md shadow-2xl border-white/10 bg-white/95 backdrop-blur-xl">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-3xl font-bold text-slate-900">Welcome back</CardTitle>
            <CardDescription className="text-slate-600">Sign in to continue to Pairly</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="pl-10 rounded-xl py-6 border-slate-300"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor="password" className="text-slate-700">Password</Label>
                  <a href="#" className="text-sm text-violet-600 hover:underline">
                    Forgot password?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="pl-10 rounded-xl py-6 border-slate-300"
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 rounded-xl py-6 text-lg shadow-lg shadow-violet-500/25" 
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="bg-white px-4 text-slate-500">or continue with</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Button variant="outline" type="button" className="rounded-xl py-6 border-slate-300">
                  <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google
                </Button>
                <Button variant="outline" type="button" className="rounded-xl py-6 border-slate-300">
                  <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.341-3.369-1.341-.454-1.155-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
                  </svg>
                  GitHub
                </Button>
              </div>

              <p className="text-center text-sm text-slate-600 mt-6">
                Don't have an account?{' '}
                <Link to="/signup" className="text-violet-600 hover:underline font-medium">
                  Sign up
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Background image indicators */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 flex gap-2">
        {backgroundImages.map((_, index) => (
          <div
            key={index}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index === currentBgIndex 
                ? 'w-6 bg-white' 
                : 'w-1.5 bg-white/40'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default Login;
