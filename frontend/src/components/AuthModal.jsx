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
    
    // GSAP animation
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">\n      {/* Backdrop */}\n      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />\n      \n      {/* Modal */}\n      <div className="relative bg-white rounded-3xl p-8 w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl">\n        <button\n          onClick={onClose}\n          className="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"\n        >\n          <X size={20} />\n        </button>\n\n        {mode === 'login' ? (\n          <form onSubmit={handleLogin}>\n            <div className="text-center mb-8">\n              <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>\n              <p className="text-gray-500">Sign in to continue your journey</p>\n            </div>\n\n            {error && (\n              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl mb-6 text-sm">\n                {error}\n              </div>\n            )}\n\n            <div className="space-y-4">\n              <div>\n                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>\n                <input\n                  type="email"\n                  name="email"\n                  value={formData.email}\n                  onChange={handleChange}\n                  className="input"\n                  placeholder="hello@example.com"\n                  required\n                />\n              </div>\n              <div>\n                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>\n                <div className="relative">\n                  <input\n                    type={showPassword ? 'text' : 'password'}\n                    name="password"\n                    value={formData.password}\n                    onChange={handleChange}\n                    className="input pr-12"\n                    placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"\n                    required\n                  />\n                  <button\n                    type="button"\n                    onClick={() => setShowPassword(!showPassword)}\n                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"\n                  >\n                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}\n                  </button>\n                </div>\n              </div>\n            </div>\n\n            <button\n              type="submit"\n              disabled={loading}\n              className="btn-primary w-full mt-8 disabled:opacity-50"\n            >\n              {loading ? 'Signing in...' : 'Sign In'}\n            </button>\n\n            <p className="text-center text-gray-500 mt-6">\n              Don't have an account?{' '}\n              <button\n                type="button"\n                onClick={() => { setMode('signup'); setStep(1); setError(''); }}\n                className="text-purple-600 font-medium hover:underline"\n              >\n                Sign up\n              </button>\n            </p>\n          </form>\n        ) : (\n          <div className="step-content">\n            <div className="text-center mb-6">\n              <h2 className="text-2xl font-bold text-gray-900 mb-1">Create Account</h2>\n              <p className="text-gray-500 text-sm">Step {step} of 5</p>\n            </div>\n\n            {/* Progress */}\n            <div className="flex gap-2 mb-8">\n              {[1, 2, 3, 4, 5].map((s) => (\n                <div\n                  key={s}\n                  className={`h-1.5 flex-1 rounded-full transition-colors ${\n                    s <= step ? 'bg-purple-500' : 'bg-gray-200'\n                  }`}\n                />\n              ))}\n            </div>\n\n            {error && (\n              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl mb-6 text-sm">\n                {error}\n              </div>\n            )}\n\n            {/* Step 1: Basic Info */}\n            {step === 1 && (\n              <div className="space-y-4">\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>\n                  <input\n                    type="text"\n                    name="name"\n                    value={formData.name}\n                    onChange={handleChange}\n                    className="input"\n                    placeholder="Your name"\n                  />\n                </div>\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>\n                  <input\n                    type="email"\n                    name="email"\n                    value={formData.email}\n                    onChange={handleChange}\n                    className="input"\n                    placeholder="hello@example.com"\n                  />\n                </div>\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>\n                  <input\n                    type="password"\n                    name="password"\n                    value={formData.password}\n                    onChange={handleChange}\n                    className="input"\n                    placeholder="Min 8 characters"\n                    minLength={8}\n                  />\n                </div>\n              </div>\n            )}\n\n            {/* Step 2: Personal Details */}\n            {step === 2 && (\n              <div className="space-y-4">\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number</label>\n                  <input\n                    type="tel"\n                    name="mobile_number"\n                    value={formData.mobile_number}\n                    onChange={handleChange}\n                    className="input"\n                    placeholder="+91 9876543210"\n                  />\n                </div>\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>\n                  <input\n                    type="number"\n                    name="age"\n                    value={formData.age}\n                    onChange={handleChange}\n                    className="input"\n                    placeholder="18+"\n                    min={18}\n                  />\n                </div>\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>\n                  <select name="gender" value={formData.gender} onChange={handleChange} className="input">\n                    <option value="">Select</option>\n                    <option value="male">Male</option>\n                    <option value="female">Female</option>\n                    <option value="other">Other</option>\n                  </select>\n                </div>\n              </div>\n            )}\n\n            {/* Step 3: Preferences */}\n            {step === 3 && (\n              <div className="space-y-4">\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Interested In</label>\n                  <select name="interested_in" value={formData.interested_in} onChange={handleChange} className="input">\n                    <option value="">Select</option>\n                    <option value="male">Men</option>\n                    <option value="female">Women</option>\n                    <option value="other">Everyone</option>\n                  </select>\n                </div>\n                <div>\n                  <label className="block text-sm font-medium text-gray-700 mb-2">Looking For</label>\n                  <select name="intent" value={formData.intent} onChange={handleChange} className="input">\n                    <option value="dating">Dating</option>\n                    <option value="serious">Serious Relationship</option>\n                    <option value="casual">Casual</option>\n                    <option value="friendship">Friendship</option>\n                  </select>\n                </div>\n                <div className="grid grid-cols-2 gap-4">\n                  <div>\n                    <label className="block text-sm font-medium text-gray-700 mb-2">Min Age</label>\n                    <input type="number" name="min_age" value={formData.min_age} onChange={handleChange} className="input" min={18} />\n                  </div>\n                  <div>\n                    <label className="block text-sm font-medium text-gray-700 mb-2">Max Age</label>\n                    <input type="number" name="max_age" value={formData.max_age} onChange={handleChange} className="input" max={100} />\n                  </div>\n                </div>\n              </div>\n            )}\n\n            {/* Step 4: Photos */}\n            {step === 4 && (\n              <div className="space-y-4">\n                <p className="text-sm text-gray-600 mb-4">Add up to 6 photos. Tap to set as primary.</p>\n                <div className="grid grid-cols-3 gap-3">\n                  {photos.map((photo, i) => (\n                    <div key={i} className="relative aspect-square group">\n                      <img src={photo.preview} alt="" className="w-full h-full object-cover rounded-xl" />\n                      <button\n                        onClick={() => removePhoto(i)}\n                        className="absolute top-1 right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity"\n                      >\n                        <Trash2 size={12} />\n                      </button>\n                      <button\n                        onClick={() => setPrimaryPhoto(i)}\n                        className={`absolute bottom-1 left-1 w-6 h-6 rounded-full flex items-center justify-center text-white transition-all ${\n                          primaryPhoto === i ? 'bg-green-500' : 'bg-black/50 opacity-0 group-hover:opacity-100'\n                        }`}\n                      >\n                        <Check size={12} />\n                      </button>\n                    </div>\n                  ))}\n                  {photos.length < 6 && (\n                    <button\n                      onClick={() => fileInputRef.current?.click()}\n                      className="aspect-square border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 hover:border-purple-400 hover:text-purple-500 transition-colors"\n                    >\n                      <Plus size={24} />\n                      <span className="text-xs mt-1">Add</span>\n                    </button>\n                  )}\n                </div>\n                <input\n                  ref={fileInputRef}\n                  type="file"\n                  accept="image/*"\n                  multiple\n                  onChange={handlePhotoUpload}\n                  className="hidden"\n                />\n              </div>\n            )}\n\n            {/* Step 5: Address */}\n            {step === 5 && (\n              <div className="space-y-4">\n                <div className="bg-purple-50 p-4 rounded-xl mb-4">\n                  <p className="text-sm text-purple-700">\ud83d\udd12 Your address is private and never shown to others</p>\n                </div>\n                <input name="address_line" value={formData.address_line} onChange={handleChange} className="input" placeholder="Address Line" />\n                <div className="grid grid-cols-2 gap-4">\n                  <input name="city" value={formData.city} onChange={handleChange} className="input" placeholder="City" />\n                  <input name="state" value={formData.state} onChange={handleChange} className="input" placeholder="State" />\n                </div>\n                <div className="grid grid-cols-2 gap-4">\n                  <input name="country" value={formData.country} onChange={handleChange} className="input" placeholder="Country" />\n                  <input name="pincode" value={formData.pincode} onChange={handleChange} className="input" placeholder="Pincode" />\n                </div>\n              </div>\n            )}\n\n            {/* Navigation */}\n            <div className="flex gap-3 mt-8">\n              {step > 1 && (\n                <button type="button" onClick={prevStep} className="btn-ghost flex-1 flex items-center justify-center gap-2">\n                  <ChevronLeft size={18} /> Back\n                </button>\n              )}\n              {step < 5 ? (\n                <button type="button" onClick={nextStep} className="btn-primary flex-1 flex items-center justify-center gap-2">\n                  Next <ChevronRight size={18} />\n                </button>\n              ) : (\n                <button type="button" onClick={handleSignup} disabled={loading} className="btn-primary flex-1 disabled:opacity-50">\n                  {loading ? 'Creating...' : 'Create Account'}\n                </button>\n              )}\n            </div>\n\n            <p className="text-center text-gray-500 mt-6 text-sm">\n              Already have an account?{' '}\n              <button type="button" onClick={() => { setMode('login'); setStep(1); setError(''); }} className="text-purple-600 font-medium hover:underline">\n                Sign in\n              </button>\n            </p>\n          </div>\n        )}\n      </div>\n    </div>\n  );\n};\n\nexport default AuthModal;
