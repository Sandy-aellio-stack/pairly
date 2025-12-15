import { useState } from 'react';
import { X, ChevronRight, ChevronLeft, Eye, EyeOff } from 'lucide-react';
import gsap from 'gsap';
import useAuthStore from '@/store/authStore';

const AuthModal = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState(initialMode);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const { login, signup } = useAuthStore();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    mobile_number: '',
    password: '',
    age: '',
    gender: '',
    interested_in: '',
    intent: 'dating',
    min_age: 18,
    max_age: 50,
    max_distance_km: 50,
    address_line: '',
    city: '',
    state: '',
    country: 'India',
    pincode: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(formData.email, formData.password);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async () => {
    setLoading(true);
    setError('');
    try {
      const data = {
        ...formData,
        age: parseInt(formData.age),
        min_age: parseInt(formData.min_age),
        max_age: parseInt(formData.max_age),
        max_distance_km: parseInt(formData.max_distance_km),
      };
      await signup(data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (step === 1 && (!formData.name || !formData.email || !formData.password)) {
      setError('Please fill all fields');
      return;
    }
    if (step === 2 && (!formData.age || !formData.gender || !formData.mobile_number)) {
      setError('Please fill all fields');
      return;
    }
    if (step === 2 && parseInt(formData.age) < 18) {
      setError('You must be 18 or older');
      return;
    }
    if (step === 3 && !formData.interested_in) {
      setError('Please select your preference');
      return;
    }
    setError('');
    setStep(step + 1);
  };

  const prevStep = () => {
    setError('');
    setStep(step - 1);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-[#0B0B0F] border border-white/10 rounded-3xl p-8 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
        >
          <X size={24} />
        </button>

        {mode === 'login' ? (
          /* Login Form */
          <form onSubmit={handleLogin}>
            <h2 className="text-3xl font-bold mb-2 gradient-text">Welcome Back</h2>
            <p className="text-white/60 mb-8">Sign in to continue</p>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleChange}
                className="input-dark"
                required
              />
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  className="input-dark pr-12"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-8 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            <p className="text-center text-white/60 mt-6">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('signup'); setStep(1); setError(''); }}
                className="text-purple-400 hover:text-purple-300"
              >
                Create one
              </button>
            </p>
          </form>
        ) : (
          /* Signup Form */
          <div>
            <h2 className="text-3xl font-bold mb-2 gradient-text">Create Account</h2>
            <p className="text-white/60 mb-8">Step {step} of 4</p>

            {/* Progress bar */}
            <div className="h-1 bg-white/10 rounded-full mb-8">
              <div 
                className="h-full bg-purple-500 rounded-full transition-all duration-500"
                style={{ width: `${(step / 4) * 100}%` }}
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6">
                {error}
              </div>
            )}

            {/* Step 1: Basic Info */}
            {step === 1 && (
              <div className="space-y-4">
                <input
                  type="text"
                  name="name"
                  placeholder="Full Name"
                  value={formData.name}
                  onChange={handleChange}
                  className="input-dark"
                />
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleChange}
                  className="input-dark"
                />
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    placeholder="Password (min 8 characters)"
                    value={formData.password}
                    onChange={handleChange}
                    className="input-dark pr-12"
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Personal Details */}
            {step === 2 && (
              <div className="space-y-4">
                <input
                  type="tel"
                  name="mobile_number"
                  placeholder="Mobile Number (+91...)"
                  value={formData.mobile_number}
                  onChange={handleChange}
                  className="input-dark"
                />
                <input
                  type="number"
                  name="age"
                  placeholder="Age (18+)"
                  value={formData.age}
                  onChange={handleChange}
                  className="input-dark"
                  min={18}
                  max={100}
                />
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="input-dark"
                >
                  <option value="">Select Gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            )}

            {/* Step 3: Preferences */}
            {step === 3 && (
              <div className="space-y-4">
                <select
                  name="interested_in"
                  value={formData.interested_in}
                  onChange={handleChange}
                  className="input-dark"
                >
                  <option value="">Interested In</option>
                  <option value="male">Men</option>
                  <option value="female">Women</option>
                  <option value="other">Everyone</option>
                </select>
                <select
                  name="intent"
                  value={formData.intent}
                  onChange={handleChange}
                  className="input-dark"
                >
                  <option value="dating">Dating</option>
                  <option value="serious">Serious Relationship</option>
                  <option value="casual">Casual</option>
                  <option value="friendship">Friendship</option>
                </select>
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="number"
                    name="min_age"
                    placeholder="Min Age"
                    value={formData.min_age}
                    onChange={handleChange}
                    className="input-dark"
                    min={18}
                  />
                  <input
                    type="number"
                    name="max_age"
                    placeholder="Max Age"
                    value={formData.max_age}
                    onChange={handleChange}
                    className="input-dark"
                    max={100}
                  />
                </div>
                <input
                  type="number"
                  name="max_distance_km"
                  placeholder="Max Distance (km)"
                  value={formData.max_distance_km}
                  onChange={handleChange}
                  className="input-dark"
                  min={1}
                  max={500}
                />
              </div>
            )}

            {/* Step 4: Address (Private) */}
            {step === 4 && (
              <div className="space-y-4">
                <p className="text-white/60 text-sm mb-4">
                  🔒 Your address is private and will never be shown to others
                </p>
                <input
                  type="text"
                  name="address_line"
                  placeholder="Address Line"
                  value={formData.address_line}
                  onChange={handleChange}
                  className="input-dark"
                />
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    name="city"
                    placeholder="City"
                    value={formData.city}
                    onChange={handleChange}
                    className="input-dark"
                  />
                  <input
                    type="text"
                    name="state"
                    placeholder="State"
                    value={formData.state}
                    onChange={handleChange}
                    className="input-dark"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    name="country"
                    placeholder="Country"
                    value={formData.country}
                    onChange={handleChange}
                    className="input-dark"
                  />
                  <input
                    type="text"
                    name="pincode"
                    placeholder="Pincode"
                    value={formData.pincode}
                    onChange={handleChange}
                    className="input-dark"
                  />
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex gap-4 mt-8">
              {step > 1 && (
                <button
                  type="button"
                  onClick={prevStep}
                  className="btn-secondary flex-1 flex items-center justify-center gap-2"
                >
                  <ChevronLeft size={20} /> Back
                </button>
              )}
              {step < 4 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  Next <ChevronRight size={20} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSignup}
                  disabled={loading}
                  className="btn-primary flex-1 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Account'}
                </button>
              )}
            </div>

            <p className="text-center text-white/60 mt-6">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('login'); setStep(1); setError(''); }}
                className="text-purple-400 hover:text-purple-300"
              >
                Sign in
              </button>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthModal;
