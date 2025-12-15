import { useState, useRef } from 'react';
import { X, ChevronRight, ChevronLeft, Eye, EyeOff, Camera, Plus, Trash2, Check } from 'lucide-react';
import gsap from 'gsap';
import useAuthStore from '@/store/authStore';

const AuthModal = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState(initialMode);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [primaryPhoto, setPrimaryPhoto] = useState(0);
  const fileInputRef = useRef(null);
  
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

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    const newPhotos = files.slice(0, 6 - photos.length).map((file) => ({
      file,
      preview: URL.createObjectURL(file),
    }));
    setPhotos((prev) => [...prev, ...newPhotos].slice(0, 6));
  };

  const removePhoto = (index) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    if (primaryPhoto === index) setPrimaryPhoto(0);
    else if (primaryPhoto > index) setPrimaryPhoto(primaryPhoto - 1);
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
        profile_pictures: photos.map((p) => p.preview),
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
    
    gsap.from('.step-content', {
      x: 50,
      opacity: 0,
      duration: 0.4,
      ease: 'power2.out',
    });
  };

  const prevStep = () => {
    setError('');
    setStep(step - 1);
    gsap.from('.step-content', {
      x: -50,
      opacity: 0,
      duration: 0.4,
      ease: 'power2.out',
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative bg-white rounded-3xl p-8 w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
        >
          <X size={20} />
        </button>

        {mode === 'login' ? (
          <form onSubmit={handleLogin}>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>
              <p className="text-gray-500">Sign in to continue your journey</p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl mb-6 text-sm">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="input"
                  placeholder="hello@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="input pr-12"
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
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-8 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            <p className="text-center text-gray-500 mt-6">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('signup'); setStep(1); setError(''); }}
                className="text-purple-600 font-medium hover:underline"
              >
                Sign up
              </button>
            </p>
          </form>
        ) : (
          <div className="step-content">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">Create Account</h2>
              <p className="text-gray-500 text-sm">Step {step} of 5</p>
            </div>

            {/* Progress */}
            <div className="flex gap-2 mb-8">
              {[1, 2, 3, 4, 5].map((s) => (
                <div
                  key={s}
                  className={`h-1.5 flex-1 rounded-full transition-colors ${
                    s <= step ? 'bg-purple-500' : 'bg-gray-200'
                  }`}
                />
              ))}
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl mb-6 text-sm">
                {error}
              </div>
            )}

            {/* Step 1: Basic Info */}
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="input"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="input"
                    placeholder="hello@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="input"
                    placeholder="Min 8 characters"
                    minLength={8}
                  />
                </div>
              </div>
            )}

            {/* Step 2: Personal Details */}
            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number</label>
                  <input
                    type="tel"
                    name="mobile_number"
                    value={formData.mobile_number}
                    onChange={handleChange}
                    className="input"
                    placeholder="+91 9876543210"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
                  <input
                    type="number"
                    name="age"
                    value={formData.age}
                    onChange={handleChange}
                    className="input"
                    placeholder="18+"
                    min={18}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
                  <select name="gender" value={formData.gender} onChange={handleChange} className="input">
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            )}

            {/* Step 3: Preferences */}
            {step === 3 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Interested In</label>
                  <select name="interested_in" value={formData.interested_in} onChange={handleChange} className="input">
                    <option value="">Select</option>
                    <option value="male">Men</option>
                    <option value="female">Women</option>
                    <option value="other">Everyone</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Looking For</label>
                  <select name="intent" value={formData.intent} onChange={handleChange} className="input">
                    <option value="dating">Dating</option>
                    <option value="serious">Serious Relationship</option>
                    <option value="casual">Casual</option>
                    <option value="friendship">Friendship</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Min Age</label>
                    <input type="number" name="min_age" value={formData.min_age} onChange={handleChange} className="input" min={18} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Max Age</label>
                    <input type="number" name="max_age" value={formData.max_age} onChange={handleChange} className="input" max={100} />
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Photos */}
            {step === 4 && (
              <div className="space-y-4">
                <p className="text-sm text-gray-600 mb-4">Add up to 6 photos. Tap to set as primary.</p>
                <div className="grid grid-cols-3 gap-3">
                  {photos.map((photo, i) => (
                    <div key={i} className="relative aspect-square group">
                      <img src={photo.preview} alt="" className="w-full h-full object-cover rounded-xl" />
                      <button
                        onClick={() => removePhoto(i)}
                        className="absolute top-1 right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 size={12} />
                      </button>
                      <button
                        onClick={() => setPrimaryPhoto(i)}
                        className={`absolute bottom-1 left-1 w-6 h-6 rounded-full flex items-center justify-center text-white transition-all ${
                          primaryPhoto === i ? 'bg-green-500' : 'bg-black/50 opacity-0 group-hover:opacity-100'
                        }`}
                      >
                        <Check size={12} />
                      </button>
                    </div>
                  ))}
                  {photos.length < 6 && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="aspect-square border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 hover:border-purple-400 hover:text-purple-500 transition-colors"
                    >
                      <Plus size={24} />
                      <span className="text-xs mt-1">Add</span>
                    </button>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handlePhotoUpload}
                  className="hidden"
                />
              </div>
            )}

            {/* Step 5: Address */}
            {step === 5 && (
              <div className="space-y-4">
                <div className="bg-purple-50 p-4 rounded-xl mb-4">
                  <p className="text-sm text-purple-700">🔒 Your address is private and never shown to others</p>
                </div>
                <input name="address_line" value={formData.address_line} onChange={handleChange} className="input" placeholder="Address Line" />
                <div className="grid grid-cols-2 gap-4">
                  <input name="city" value={formData.city} onChange={handleChange} className="input" placeholder="City" />
                  <input name="state" value={formData.state} onChange={handleChange} className="input" placeholder="State" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <input name="country" value={formData.country} onChange={handleChange} className="input" placeholder="Country" />
                  <input name="pincode" value={formData.pincode} onChange={handleChange} className="input" placeholder="Pincode" />
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex gap-3 mt-8">
              {step > 1 && (
                <button type="button" onClick={prevStep} className="btn-ghost flex-1 flex items-center justify-center gap-2">
                  <ChevronLeft size={18} /> Back
                </button>
              )}
              {step < 5 ? (
                <button type="button" onClick={nextStep} className="btn-primary flex-1 flex items-center justify-center gap-2">
                  Next <ChevronRight size={18} />
                </button>
              ) : (
                <button type="button" onClick={handleSignup} disabled={loading} className="btn-primary flex-1 disabled:opacity-50">
                  {loading ? 'Creating...' : 'Create Account'}
                </button>
              )}
            </div>

            <p className="text-center text-gray-500 mt-6 text-sm">
              Already have an account?{' '}
              <button type="button" onClick={() => { setMode('login'); setStep(1); setError(''); }} className="text-purple-600 font-medium hover:underline">
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
