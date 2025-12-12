import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { Heart, Camera, Users, Sparkles, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';

const Signup = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleSelect = (role) => {
    setFormData({ ...formData, role });
    setStep(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      await signup(formData.email, formData.password, formData.name, formData.role);
      toast.success('Account created successfully!');
      navigate('/home');
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50 to-fuchsia-50">
      {/* Header */}
      <div className="p-4">
        <Link to="/" className="flex items-center gap-2 w-fit">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <Heart className="h-5 w-5 text-white" />
          </div>
          <span className="text-2xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
            Pairly
          </span>
        </Link>
      </div>

      <div className="flex items-center justify-center px-4 py-8">
        {step === 1 ? (
          /* Step 1: Role Selection */
          <div className="w-full max-w-4xl">
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold mb-4 text-slate-900">Join Pairly</h1>
              <p className="text-xl text-slate-600">How do you want to use Pairly?</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Fan Card */}
              <Card 
                className="cursor-pointer border-2 border-slate-200 hover:border-violet-400 hover:shadow-xl transition-all group"
                onClick={() => handleRoleSelect('fan')}
              >
                <CardContent className="p-8">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Users className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold mb-3 text-slate-900">I'm a Fan</h2>
                  <p className="text-slate-600 mb-6">
                    Discover amazing creators, make meaningful connections, and find your perfect match.
                  </p>
                  <ul className="space-y-2 mb-6">
                    {['Browse & discover creators', 'Send messages & connect', 'See nearby users on map', 'Attend IRL events'].map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                  <Button className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 rounded-full">
                    Continue as Fan
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>

              {/* Creator Card */}
              <Card 
                className="cursor-pointer border-2 border-slate-200 hover:border-fuchsia-400 hover:shadow-xl transition-all group relative overflow-hidden"
                onClick={() => handleRoleSelect('creator')}
              >
                <div className="absolute top-4 right-4">
                  <span className="bg-gradient-to-r from-fuchsia-500 to-pink-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    <Sparkles className="h-3 w-3 inline mr-1" />
                    Earn Money
                  </span>
                </div>
                <CardContent className="p-8">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-fuchsia-500 to-pink-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Camera className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold mb-3 text-slate-900">I'm a Creator</h2>
                  <p className="text-slate-600 mb-6">
                    Share your content, grow your audience, and earn money from your passion.
                  </p>
                  <ul className="space-y-2 mb-6">
                    {['Post photos & videos', 'Earn from tips & subscriptions', 'Analytics dashboard', 'Build your fanbase'].map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                  <Button className="w-full bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700 rounded-full">
                    Continue as Creator
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            </div>

            <p className="text-center mt-8 text-slate-600">
              Already have an account?{' '}
              <Link to="/login" className="text-violet-600 hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </div>
        ) : (
          /* Step 2: Account Details */
          <Card className="w-full max-w-md shadow-xl border-slate-200">
            <CardHeader className="space-y-1">
              <div className="flex items-center gap-2 mb-2">
                <Button variant="ghost" size="sm" onClick={() => setStep(1)} className="-ml-2">
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  Back
                </Button>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  formData.role === 'creator' 
                    ? 'bg-gradient-to-br from-fuchsia-500 to-pink-600' 
                    : 'bg-gradient-to-br from-violet-500 to-indigo-600'
                }`}>
                  {formData.role === 'creator' ? (
                    <Camera className="h-6 w-6 text-white" />
                  ) : (
                    <Users className="h-6 w-6 text-white" />
                  )}
                </div>
                <div>
                  <CardTitle className="text-2xl text-slate-900">Create Account</CardTitle>
                  <CardDescription className="text-slate-600">
                    Signing up as a {formData.role === 'creator' ? 'Creator' : 'Fan'}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="name" className="text-slate-700">Full Name</Label>
                  <Input
                    id="name"
                    name="name"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="rounded-xl border-slate-300"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-slate-700">Email</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="rounded-xl border-slate-300"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-slate-700">Password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="rounded-xl border-slate-300"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-slate-700">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    className="rounded-xl border-slate-300"
                  />
                </div>

                <Button 
                  type="submit" 
                  className={`w-full rounded-xl py-6 ${
                    formData.role === 'creator'
                      ? 'bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700'
                      : 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700'
                  }`}
                  disabled={loading}
                >
                  {loading ? 'Creating account...' : 'Create Account'}
                </Button>

                <p className="text-center text-sm text-slate-600">
                  By signing up, you agree to our{' '}
                  <a href="#" className="text-violet-600 hover:underline">Terms</a>
                  {' '}and{' '}
                  <a href="#" className="text-violet-600 hover:underline">Privacy Policy</a>
                </p>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Signup;
