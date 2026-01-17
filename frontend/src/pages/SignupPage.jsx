import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, Eye, EyeOff, ArrowRight, User, Check, Calendar, Users, MapPin, Camera, Phone } from 'lucide-react';
import { toast } from 'sonner';
import useAuthStore from '@/store/authStore';
import api from '@/services/api';
import HeartCursor from '@/components/HeartCursor';

const SignupPage = () => {
  const navigate = useNavigate();
  const { signup } = useAuthStore();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    // Step 1: Basic Info
    name: '',
    age: '',
    gender: '',
    // Step 2: Preferences
    interested_in: '',
    min_age: 18,
    max_age: 50,
    intent: 'dating',
    // Step 3: Contact
    email: '',
    mobile_number: '',
    password: '',
    confirmPassword: '',
    // Step 4: Address (Optional) & Image
    address_line: '',
    city: '',
    state: '',
    country: 'India',
    pincode: '',
    profile_image: null,
    // Terms
    agreeTerms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);

  const handleChange = (e) => {
    const { name, value, type, checked, files } = e.target;
    if (type === 'file' && files[0]) {
      setFormData({ ...formData, profile_image: files[0] });
      setImagePreview(URL.createObjectURL(files[0]));
    } else {
      setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value });
    }
  };

  const validateStep = () => {
    switch (step) {
      case 1:
        if (!formData.name || formData.name.length < 2) {
          toast.error('Please enter your name (min 2 characters)');
          return false;
        }
        if (!formData.age || formData.age < 18) {
          toast.error('You must be at least 18 years old');
          return false;
        }
        if (!formData.gender) {
          toast.error('Please select your gender');
          return false;
        }
        return true;
      case 2:
        if (!formData.interested_in) {
          toast.error('Please select who you want to meet');
          return false;
        }
        return true;
      case 3:
        if (!formData.email) {
          toast.error('Please enter your email');
          return false;
        }
        if (!formData.mobile_number || formData.mobile_number.length < 10) {
          toast.error('Please enter a valid mobile number');
          return false;
        }
        if (!formData.password || formData.password.length < 8) {
          toast.error('Password must be at least 8 characters');
          return false;
        }
        if (formData.password !== formData.confirmPassword) {
          toast.error('Passwords do not match');
          return false;
        }
        return true;
      case 4:
        if (!formData.agreeTerms) {
          toast.error('Please agree to the terms and conditions');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleNextStep = () => {
    if (validateStep()) {
      setStep(step + 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateStep()) return;

    setIsLoading(true);

    try {
      // Build signup payload with guaranteed defaults for optional fields
      const signupData = {
        // Required fields
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        mobile_number: formData.mobile_number.trim(),
        password: formData.password,
        age: parseInt(formData.age, 10),
        gender: formData.gender,  // Must be: "male" | "female" | "other"
        interested_in: formData.interested_in,  // Must be: "male" | "female" | "other"
        
        // Optional fields with safe defaults
        intent: formData.intent || 'dating',
        min_age: parseInt(formData.min_age, 10) || 18,
        max_age: parseInt(formData.max_age, 10) || 50,
        max_distance_km: 50,
        
        // Address fields - always send with defaults
        address_line: formData.address_line?.trim() || 'NA',
        city: formData.city?.trim() || 'NA',
        state: formData.state?.trim() || 'NA',
        country: formData.country?.trim() || 'India',
        pincode: formData.pincode?.trim() || '000000',
      };

      await signup(signupData);
      
      toast.success('Welcome to Luveloop! 🎉 You received 10 free coins!');
      navigate('/dashboard');
    } catch (error) {
      // Handle field-specific validation errors
      const errorDetail = error.response?.data?.detail;
      
      if (typeof errorDetail === 'string') {
        toast.error(errorDetail);
      } else if (Array.isArray(errorDetail)) {
        // Pydantic validation errors come as array
        const fieldErrors = errorDetail.map(err => {
          const field = err.loc?.slice(-1)[0] || 'field';
          return `${field}: ${err.msg}`;
        }).join(', ');
        toast.error(fieldErrors || 'Validation failed');
      } else {
        toast.error('Registration failed. Please check your details and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const steps = [
    { num: 1, label: 'Basic Info', icon: User },
    { num: 2, label: 'Preferences', icon: Heart },
    { num: 3, label: 'Account', icon: Lock },
    { num: 4, label: 'Complete', icon: Check },
  ];

  const genderOptions = [
    { value: 'male', label: 'Male', emoji: '👨' },
    { value: 'female', label: 'Female', emoji: '👩' },
    { value: 'other', label: 'Other', emoji: '🧑' },
  ];

  const intentOptions = [
    { value: 'dating', label: 'Dating', desc: 'Open to dating' },
    { value: 'serious', label: 'Serious', desc: 'Looking for long-term' },
    { value: 'casual', label: 'Casual', desc: 'Keeping it casual' },
    { value: 'friendship', label: 'Friendship', desc: 'Just friends first' },
  ];

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Romantic Image */}
      <div className="hidden lg:flex w-2/5 relative overflow-hidden sticky top-0 h-screen">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#E8D5E7] via-[#F5E6E8] to-[#FDE8D7]" />
        
        {/* Decorative blobs */}
        <div className="absolute top-10 left-10 w-64 h-64 bg-pink-300/30 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-80 h-80 bg-orange-200/30 rounded-full blur-3xl" />
        
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-8">
          {/* Hero Image */}
          <img 
            src="https://customer-assets.emergentagent.com/job_truebond-notify/artifacts/8q937866_Gemini_Generated_Image_c05duoc05duoc05d.png" 
            alt="Find your perfect match" 
            className="w-full max-w-sm object-contain drop-shadow-2xl rounded-2xl mb-6"
          />
          
          <h2 className="text-2xl font-bold text-[#0F172A]">Start Your Journey</h2>
          <p className="text-gray-700 mt-2 text-center">Create meaningful connections that last a lifetime ✨</p>
          
          {/* Signup Benefits */}
          <div className="mt-6 text-left bg-white/70 backdrop-blur-sm rounded-xl p-5 w-full max-w-xs shadow-lg">
            <p className="font-semibold text-[#0F172A] mb-3">What you get:</p>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-center gap-2">
                <Check size={16} className="text-green-500" />
                10 free conversation coins
              </li>
              <li className="flex items-center gap-2">
                <Check size={16} className="text-green-500" />
                Verified profile badge
              </li>
              <li className="flex items-center gap-2">
                <Check size={16} className="text-green-500" />
                Find people nearby
              </li>
              <li className="flex items-center gap-2">
                <Check size={16} className="text-green-500" />
                Privacy protected
              </li>
            </ul>
          </div>
          
          {/* Floating hearts */}
          <div className="absolute top-1/4 left-1/6 animate-pulse">
            <Heart size={20} className="text-pink-400" fill="currentColor" />
          </div>
          <div className="absolute bottom-1/4 right-1/6 animate-pulse delay-300">
            <Heart size={16} className="text-rose-400" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 overflow-y-auto bg-white">
        <div className="w-full max-w-lg">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center shadow-lg">
              <Heart size={24} className="text-white" fill="white" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">Luveloop</span>
          </Link>

          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-8">
            {steps.map((s, i) => (
              <div key={s.num} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold transition-all ${
                    step >= s.num ? 'bg-gradient-to-br from-pink-500 to-rose-500 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    {step > s.num ? <Check size={20} /> : <s.icon size={20} />}
                  </div>
                  <span className={`text-xs mt-1 ${step >= s.num ? 'text-pink-600' : 'text-gray-400'}`}>
                    {s.label}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-12 h-1 mx-2 rounded transition-all ${
                    step > s.num ? 'bg-gradient-to-r from-pink-500 to-rose-500' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Step 1: Basic Info */}
            {step === 1 && (
              <>
                <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Tell us about yourself</h1>
                <p className="text-gray-600 mb-6">Let's start with the basics</p>
                
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
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">Age</label>
                  <div className="relative">
                    <Calendar size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="number"
                      name="age"
                      value={formData.age}
                      onChange={handleChange}
                      placeholder="Your age (18+)"
                      min="18"
                      max="100"
                      className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">I am a</label>
                  <div className="grid grid-cols-3 gap-3">
                    {genderOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, gender: option.value })}
                        className={`p-4 rounded-xl border-2 transition-all text-center ${
                          formData.gender === option.value
                            ? 'border-[#0F172A] bg-[#E9D5FF]/30'
                            : 'border-gray-200 hover:border-[#E9D5FF]'
                        }`}
                      >
                        <span className="text-2xl block mb-1">{option.emoji}</span>
                        <span className="text-sm font-medium text-[#0F172A]">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Step 2: Preferences */}
            {step === 2 && (
              <>
                <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Who do you want to meet?</h1>
                <p className="text-gray-600 mb-6">Help us find the right people for you</p>
                
                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">I'm interested in</label>
                  <div className="grid grid-cols-3 gap-3">
                    {genderOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, interested_in: option.value })}
                        className={`p-4 rounded-xl border-2 transition-all text-center ${
                          formData.interested_in === option.value
                            ? 'border-[#0F172A] bg-[#E9D5FF]/30'
                            : 'border-gray-200 hover:border-[#E9D5FF]'
                        }`}
                      >
                        <span className="text-2xl block mb-1">{option.emoji}</span>
                        <span className="text-sm font-medium text-[#0F172A]">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">
                    Age Range: {formData.min_age} - {formData.max_age} years
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      name="min_age"
                      min="18"
                      max="80"
                      value={formData.min_age}
                      onChange={handleChange}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0F172A]"
                    />
                    <span className="text-sm text-gray-600">to</span>
                    <input
                      type="range"
                      name="max_age"
                      min="18"
                      max="100"
                      value={formData.max_age}
                      onChange={handleChange}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0F172A]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">What are you looking for?</label>
                  <div className="grid grid-cols-2 gap-3">
                    {intentOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, intent: option.value })}
                        className={`p-4 rounded-xl border-2 transition-all text-left ${
                          formData.intent === option.value
                            ? 'border-[#0F172A] bg-[#E9D5FF]/30'
                            : 'border-gray-200 hover:border-[#E9D5FF]'
                        }`}
                      >
                        <span className="font-semibold text-[#0F172A] block">{option.label}</span>
                        <span className="text-xs text-gray-500">{option.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Step 3: Account */}
            {step === 3 && (
              <>
                <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Create your account</h1>
                <p className="text-gray-600 mb-6">Secure your profile</p>

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
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">Mobile Number</label>
                  <div className="relative">
                    <Phone size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="tel"
                      name="mobile_number"
                      value={formData.mobile_number}
                      onChange={handleChange}
                      placeholder="+91 98765 43210"
                      className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">This will be kept private</p>
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
                    />
                  </div>
                </div>
              </>
            )}

            {/* Step 4: Complete (Address Optional + Image + Terms) */}
            {step === 4 && (
              <>
                <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Almost done!</h1>
                <p className="text-gray-600 mb-6">Add optional details (address is kept private)</p>

                {/* Profile Image (Optional) */}
                <div>
                  <label className="block text-sm font-medium text-[#0F172A] mb-2">Profile Photo (Optional)</label>
                  <div className="flex items-center gap-4">
                    <div className="w-20 h-20 rounded-full bg-[#E9D5FF]/50 flex items-center justify-center overflow-hidden border-2 border-dashed border-[#0F172A]/30">
                      {imagePreview ? (
                        <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                      ) : (
                        <Camera size={24} className="text-[#0F172A]/50" />
                      )}
                    </div>
                    <label className="flex-1">
                      <input
                        type="file"
                        name="profile_image"
                        accept="image/*"
                        onChange={handleChange}
                        className="hidden"
                      />
                      <span className="block px-4 py-2 bg-white border border-gray-200 rounded-lg text-center cursor-pointer hover:bg-gray-50 transition-colors">
                        Choose Photo
                      </span>
                    </label>
                  </div>
                </div>

                {/* Address Fields (Optional) */}
                <div className="bg-gray-50 rounded-xl p-4 space-y-4">
                  <p className="text-sm font-medium text-[#0F172A] flex items-center gap-2">
                    <MapPin size={16} />
                    Address (Optional - Never shown to others)
                  </p>
                  
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    placeholder="City"
                    className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-[#0F172A] outline-none transition-all text-sm"
                  />
                  
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      name="state"
                      value={formData.state}
                      onChange={handleChange}
                      placeholder="State"
                      className="px-4 py-3 rounded-lg border border-gray-200 focus:border-[#0F172A] outline-none transition-all text-sm"
                    />
                    <input
                      type="text"
                      name="pincode"
                      value={formData.pincode}
                      onChange={handleChange}
                      placeholder="Pincode"
                      className="px-4 py-3 rounded-lg border border-gray-200 focus:border-[#0F172A] outline-none transition-all text-sm"
                    />
                  </div>
                </div>

                {/* Terms */}
                <label className="flex items-start gap-3 bg-[#E9D5FF]/20 p-4 rounded-xl">
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
                    . I confirm I am at least 18 years old.
                  </span>
                </label>
              </>
            )}

            {/* Navigation Buttons */}
            <div className="flex gap-3">
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => setStep(step - 1)}
                  className="flex-1 py-4 border-2 border-gray-200 text-gray-600 rounded-xl font-semibold hover:border-[#0F172A] hover:text-[#0F172A] transition-all"
                >
                  ← Back
                </button>
              )}
              
              {step < 4 ? (
                <button
                  type="button"
                  onClick={handleNextStep}
                  className="flex-1 py-4 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2"
                >
                  Continue
                  <ArrowRight size={20} />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 py-4 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isLoading ? 'Creating Account...' : 'Create Account'}
                  <ArrowRight size={20} />
                </button>
              )}
            </div>
          </form>

          <p className="text-center mt-6 text-gray-600">
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
