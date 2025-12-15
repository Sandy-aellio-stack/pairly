import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronLeft, Eye, EyeOff, Heart, Plus, Trash2, Check, User, Mail, Lock, Phone, Calendar, Users, MapPin } from 'lucide-react';
import gsap from 'gsap';
import useAuthStore from '@/store/authStore';
import CustomCursor from '@/components/CustomCursor';

const SignupPage = () => {
  const navigate = useNavigate();
  const { signup } = useAuthStore();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [primaryPhoto, setPrimaryPhoto] = useState(0);
  const fileInputRef = useRef(null);
  const containerRef = useRef(null);

  const [formData, setFormData] = useState({
    name: '', email: '', password: '', mobile_number: '', age: '', gender: '',
    interested_in: '', intent: 'dating', min_age: 18, max_age: 50, max_distance_km: 50,
    address_line: '', city: '', state: '', country: 'India', pincode: '',
  });

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Floating widgets
      gsap.to('.signup-widget-1', { y: -25, x: 15, rotation: 6, duration: 4.5, ease: 'sine.inOut', yoyo: true, repeat: -1 });
      gsap.to('.signup-widget-2', { y: 20, x: -10, rotation: -4, duration: 5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 0.7 });
      gsap.to('.signup-widget-3', { y: -18, x: 12, rotation: 5, duration: 4.2, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1.2 });
      gsap.to('.signup-widget-4', { y: 22, x: -18, rotation: -7, duration: 5.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 0.3 });
      gsap.to('.signup-widget-5', { y: -20, x: 8, rotation: 3, duration: 4.8, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1.5 });

      // Blobs
      gsap.to('.signup-blob-1', { x: 50, y: -40, duration: 9, ease: 'sine.inOut', yoyo: true, repeat: -1 });
      gsap.to('.signup-blob-2', { x: -40, y: 50, duration: 11, ease: 'sine.inOut', yoyo: true, repeat: -1 });
      gsap.to('.signup-blob-3', { x: 30, y: -30, duration: 8, ease: 'sine.inOut', yoyo: true, repeat: -1 });

      // Pulsing
      gsap.to('.signup-pulse', { scale: 1.4, opacity: 0.4, duration: 2.5, ease: 'sine.inOut', yoyo: true, repeat: -1, stagger: 0.4 });

      // Card entrance
      gsap.from('.signup-card', { y: 50, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.2 });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    // Step transition animation
    gsap.from('.step-content', { x: 30, opacity: 0, duration: 0.5, ease: 'power2.out' });
  }, [step]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    const newPhotos = files.slice(0, 6 - photos.length).map((file) => ({
      file, preview: URL.createObjectURL(file),
    }));
    setPhotos((prev) => [...prev, ...newPhotos].slice(0, 6));
  };

  const removePhoto = (index) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    if (primaryPhoto === index) setPrimaryPhoto(0);
    else if (primaryPhoto > index) setPrimaryPhoto(primaryPhoto - 1);
  };

  const nextStep = () => {
    if (step === 1 && (!formData.name || !formData.email || !formData.password)) {
      setError('Please fill all fields'); return;
    }
    if (step === 2 && (!formData.age || !formData.gender || !formData.mobile_number)) {
      setError('Please fill all fields'); return;
    }
    if (step === 2 && parseInt(formData.age) < 18) {
      setError('You must be 18 or older'); return;
    }
    if (step === 3 && !formData.interested_in) {
      setError('Please select your preference'); return;
    }
    setError('');
    setStep(step + 1);
  };

  const prevStep = () => {
    setError('');
    setStep(step - 1);
  };

  const handleSubmit = async () => {
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
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const stepTitles = ['Basic Info', 'Personal Details', 'Preferences', 'Photos', 'Location'];
  const stepIcons = [User, Calendar, Users, Plus, MapPin];

  return (
    <div ref={containerRef} className="min-h-screen bg-gradient-to-br from-pink-50 via-white to-purple-50 flex items-center justify-center p-6 relative overflow-hidden">
      <CustomCursor />

      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Blobs */}
        <div className="signup-blob-1 absolute top-[5%] right-[10%] w-[450px] h-[450px] rounded-full bg-purple-200/40 blur-[90px]" />
        <div className="signup-blob-2 absolute bottom-[5%] left-[5%] w-[500px] h-[500px] rounded-full bg-pink-200/40 blur-[100px]" />
        <div className="signup-blob-3 absolute top-[40%] left-[20%] w-[300px] h-[300px] rounded-full bg-purple-100/50 blur-[80px]" />

        {/* Widgets */}
        <div className="signup-widget-1 absolute top-[12%] left-[8%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
              <Heart size={20} className="text-white" fill="white" />
            </div>
            <div>
              <div className="text-sm font-semibold">Welcome!</div>
              <div className="text-xs text-gray-500">Join TrueBond</div>
            </div>
          </div>
        </div>

        <div className="signup-widget-2 absolute top-[20%] right-[12%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-300 to-pink-300" />
            ))}
          </div>
          <div className="text-xs text-gray-500 mt-2">1000+ matches daily</div>
        </div>

        <div className="signup-widget-3 absolute bottom-[25%] left-[6%] bg-white rounded-xl p-3 shadow-lg">
          <div className="flex items-center gap-2">
            <MapPin size={18} className="text-purple-500" />
            <span className="text-sm">Find nearby</span>
          </div>
        </div>

        <div className="signup-widget-4 absolute bottom-[15%] right-[8%] bg-white rounded-2xl p-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <Check size={18} className="text-green-600" />
            </div>
            <span className="text-sm">100% Safe</span>
          </div>
        </div>

        <div className="signup-widget-5 absolute top-[50%] left-[15%] bg-white rounded-xl p-3 shadow-lg">
          <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
            <Users size={30} className="text-purple-400" />
          </div>
        </div>

        {/* Pulsing dots */}
        <div className="signup-pulse absolute top-[25%] left-[35%] w-4 h-4 rounded-full bg-purple-400" />
        <div className="signup-pulse absolute top-[35%] right-[30%] w-3 h-3 rounded-full bg-pink-400" />
        <div className="signup-pulse absolute bottom-[30%] left-[40%] w-5 h-5 rounded-full bg-purple-300" />
        <div className="signup-pulse absolute bottom-[40%] right-[35%] w-4 h-4 rounded-full bg-pink-300" />
      </div>

      {/* Signup Card */}
      <div className="signup-card relative z-10 bg-white/80 backdrop-blur-xl rounded-3xl p-8 w-full max-w-lg shadow-2xl shadow-purple-200/30">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Heart size={24} className="text-white" fill="white" />
          </div>
          <span className="text-xl font-bold text-gray-900">TrueBond</span>
        </div>

        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">{stepTitles[step - 1]}</h2>
            <span className="text-sm text-gray-500">Step {step} of 5</span>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((s) => (
              <div key={s} className={`h-2 flex-1 rounded-full transition-colors ${s <= step ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-gray-200'}`} />
            ))}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl mb-6 text-sm">
            {error}
          </div>
        )}

        <div className="step-content">
          {/* Step 1 */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                <div className="relative">
                  <User size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="text" name="name" value={formData.name} onChange={handleChange} className="input pl-12" placeholder="Your name" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <div className="relative">
                  <Mail size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="email" name="email" value={formData.email} onChange={handleChange} className="input pl-12" placeholder="hello@example.com" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <div className="relative">
                  <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type={showPassword ? 'text' : 'password'} name="password" value={formData.password} onChange={handleChange} className="input pl-12 pr-12" placeholder="Min 8 characters" minLength={8} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 2 */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number</label>
                <div className="relative">
                  <Phone size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="tel" name="mobile_number" value={formData.mobile_number} onChange={handleChange} className="input pl-12" placeholder="+91 9876543210" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
                <div className="relative">
                  <Calendar size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="number" name="age" value={formData.age} onChange={handleChange} className="input pl-12" placeholder="18+" min={18} />
                </div>
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

          {/* Step 3 */}
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

          {/* Step 4 - Photos */}
          {step === 4 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">Add up to 6 photos. Tap the star to set as primary.</p>
              <div className="grid grid-cols-3 gap-3">
                {photos.map((photo, i) => (
                  <div key={i} className="relative aspect-square group">
                    <img src={photo.preview} alt="" className="w-full h-full object-cover rounded-xl" />
                    <button onClick={() => removePhoto(i)} className="absolute top-1 right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity">
                      <Trash2 size={12} />
                    </button>
                    <button onClick={() => setPrimaryPhoto(i)} className={`absolute bottom-1 left-1 w-6 h-6 rounded-full flex items-center justify-center text-white transition-all ${primaryPhoto === i ? 'bg-green-500' : 'bg-black/50 opacity-0 group-hover:opacity-100'}`}>
                      <Check size={12} />
                    </button>
                  </div>
                ))}
                {photos.length < 6 && (
                  <button onClick={() => fileInputRef.current?.click()} className="aspect-square border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 hover:border-purple-400 hover:text-purple-500 transition-colors">
                    <Plus size={28} />
                    <span className="text-xs mt-1">Add Photo</span>
                  </button>
                )}
              </div>
              <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handlePhotoUpload} className="hidden" />
            </div>
          )}

          {/* Step 5 - Address */}
          {step === 5 && (
            <div className="space-y-4">
              <div className="bg-purple-50 p-4 rounded-xl">
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
        </div>

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
            <button type="button" onClick={handleSubmit} disabled={loading} className="btn-primary flex-1 disabled:opacity-50">
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          )}
        </div>

        <p className="text-center text-gray-500 mt-6 text-sm">
          Already have an account?{' '}
          <Link to="/login" className="text-purple-600 font-semibold hover:underline">Sign in</Link>
        </p>

        <Link to="/" className="block text-center text-gray-400 hover:text-gray-600 mt-4 text-sm">← Back to home</Link>
      </div>
    </div>
  );
};

export default SignupPage;
