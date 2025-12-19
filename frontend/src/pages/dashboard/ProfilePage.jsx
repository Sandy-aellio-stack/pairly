import { useState, useEffect, useRef } from 'react';
import { Camera, Edit2, MapPin, Heart, Settings, Shield, LogOut, ChevronRight, Check, Loader2, Save, Upload, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { userAPI } from '@/services/api';
import { toast } from 'sonner';

const ProfilePage = () => {
  const navigate = useNavigate();
  const { user, logout, initialize } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [profileImage, setProfileImage] = useState(null);
  const fileInputRef = useRef(null);
  const [profileData, setProfileData] = useState({
    name: '',
    bio: '',
    intent: 'dating',
  });
  const [preferences, setPreferences] = useState({
    interested_in: 'female',
    min_age: 18,
    max_age: 50,
    max_distance_km: 50,
  });

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      return;
    }

    setIsUploading(true);
    try {
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfileImage(e.target.result);
      };
      reader.readAsDataURL(file);

      // Upload to backend
      const formData = new FormData();
      formData.append('file', file);
      
      await userAPI.uploadPhoto(formData);
      await initialize(); // Refresh user data
      toast.success('Profile picture updated!');
    } catch (error) {
      toast.error('Failed to upload image');
      setProfileImage(null);
    } finally {
      setIsUploading(false);
    }
  };

  // Initialize profile data from user
  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.name || '',
        bio: user.bio || '',
        intent: user.intent || 'dating',
      });
      if (user.preferences) {
        setPreferences({
          interested_in: user.preferences.interested_in || 'female',
          min_age: user.preferences.min_age || 18,
          max_age: user.preferences.max_age || 50,
          max_distance_km: user.preferences.max_distance_km || 50,
        });
      }
    }
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
    toast.success('Logged out successfully');
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Update profile
      await userAPI.updateProfile({
        name: profileData.name,
        bio: profileData.bio,
        intent: profileData.intent,
      });

      // Update preferences
      await userAPI.updatePreferences(preferences);

      // Refresh user data
      await initialize();
      
      toast.success('Profile updated!');
      setIsEditing(false);
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const intentOptions = [
    { value: 'dating', label: 'Dating' },
    { value: 'serious', label: 'Serious Relationship' },
    { value: 'casual', label: 'Casual' },
    { value: 'friendship', label: 'Friendship' },
  ];

  const genderOptions = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
  ];

  return (
    <div className="max-w-2xl mx-auto px-4">
      {/* Profile Header */}
      <div className="bg-white rounded-3xl shadow-lg overflow-hidden mb-6">
        {/* Cover */}
        <div className="h-32 bg-gradient-to-r from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE]" />
        
        {/* Profile Info */}
        <div className="px-6 pb-6">
          <div className="flex items-end gap-4 -mt-12 mb-4">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-white p-1 shadow-lg">
                <div className="w-full h-full rounded-full bg-[#E9D5FF] flex items-center justify-center overflow-hidden">
                  {profileImage || user?.profile_pictures?.[0] ? (
                    <img src={profileImage || user.profile_pictures[0]} alt="Profile" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-4xl">{profileData.name[0]?.toUpperCase() || 'U'}</span>
                  )}
                </div>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="absolute bottom-0 right-0 w-8 h-8 bg-[#0F172A] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                {isUploading ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
              </button>
            </div>
            
            <div className="flex-1 pb-2">
              {isEditing ? (
                <input
                  type="text"
                  value={profileData.name}
                  onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                  className="text-2xl font-bold text-[#0F172A] bg-transparent border-b-2 border-[#0F172A] outline-none w-full"
                />
              ) : (
                <h1 className="text-2xl font-bold text-[#0F172A]">{profileData.name}, {user?.age}</h1>
              )}
              <p className="text-gray-500 text-sm flex items-center gap-1">
                <MapPin size={14} />
                {user?.is_verified ? 'Verified' : 'Not verified'}
              </p>
            </div>
            
            <button
              onClick={() => isEditing ? handleSave() : setIsEditing(true)}
              disabled={isSaving}
              className={`px-4 py-2 rounded-full font-medium text-sm flex items-center gap-2 transition-colors ${
                isEditing
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-[#E9D5FF] text-[#0F172A] hover:bg-[#DDD6FE]'
              } ${isSaving ? 'opacity-50' : ''}`}
            >
              {isSaving ? (
                <><Loader2 size={16} className="animate-spin" /> Saving...</>
              ) : isEditing ? (
                <><Save size={16} /> Save</>
              ) : (
                <><Edit2 size={16} /> Edit</>
              )}
            </button>
          </div>

          {/* Bio */}
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-500 block mb-1">Bio</label>
            {isEditing ? (
              <textarea
                value={profileData.bio}
                onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                placeholder="Tell people about yourself..."
                className="w-full p-3 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none resize-none"
                rows={3}
              />
            ) : (
              <p className="text-gray-700">{profileData.bio || 'No bio yet. Add one to attract more matches!'}</p>
            )}
          </div>

          {/* Intent */}
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-500 block mb-2">Looking for</label>
            {isEditing ? (
              <div className="flex flex-wrap gap-2">
                {intentOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setProfileData({ ...profileData, intent: option.value })}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      profileData.intent === option.value
                        ? 'bg-[#0F172A] text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            ) : (
              <span className="px-4 py-2 bg-[#E9D5FF]/50 text-[#0F172A] rounded-full text-sm font-medium">
                {intentOptions.find(o => o.value === profileData.intent)?.label}
              </span>
            )}
          </div>

          {/* Preferences (only show when editing) */}
          {isEditing && (
            <div className="mt-6 pt-6 border-t border-gray-100">
              <h3 className="font-semibold text-[#0F172A] mb-4">Match Preferences</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">Interested in</label>
                  <div className="flex flex-wrap gap-2">
                    {genderOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setPreferences({ ...preferences, interested_in: option.value })}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                          preferences.interested_in === option.value
                            ? 'bg-[#0F172A] text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">
                    Age Range: {preferences.min_age} - {preferences.max_age}
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="18"
                      max="80"
                      value={preferences.min_age}
                      onChange={(e) => setPreferences({ ...preferences, min_age: parseInt(e.target.value) })}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0F172A]"
                    />
                    <span className="text-sm text-gray-500">to</span>
                    <input
                      type="range"
                      min="18"
                      max="100"
                      value={preferences.max_age}
                      onChange={(e) => setPreferences({ ...preferences, max_age: parseInt(e.target.value) })}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0F172A]"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-2">
                    Max Distance: {preferences.max_distance_km} km
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="500"
                    value={preferences.max_distance_km}
                    onChange={(e) => setPreferences({ ...preferences, max_distance_km: parseInt(e.target.value) })}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0F172A]"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-2xl p-4 text-center shadow-md">
          <p className="text-3xl font-bold text-[#0F172A]">{user?.credits_balance || 0}</p>
          <p className="text-xs text-gray-500">Coins</p>
        </div>
        <div className="bg-white rounded-2xl p-4 text-center shadow-md">
          <p className="text-3xl font-bold text-[#0F172A]">{user?.is_verified ? '✓' : '✗'}</p>
          <p className="text-xs text-gray-500">Verified</p>
        </div>
        <div className="bg-white rounded-2xl p-4 text-center shadow-md">
          <p className="text-3xl font-bold text-[#0F172A]">{user?.is_online ? '🟢' : '⚪'}</p>
          <p className="text-xs text-gray-500">Status</p>
        </div>
      </div>

      {/* Menu Items */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <button 
          onClick={() => navigate('/dashboard/credits')}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors border-b border-gray-100"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#E9D5FF]/50 flex items-center justify-center">
              <Heart size={18} className="text-[#0F172A]" />
            </div>
            <span className="font-medium text-[#0F172A]">Buy Coins</span>
          </div>
          <ChevronRight size={20} className="text-gray-400" />
        </button>
        
        <button className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#DBEAFE]/50 flex items-center justify-center">
              <Shield size={18} className="text-blue-600" />
            </div>
            <span className="font-medium text-[#0F172A]">Privacy & Safety</span>
          </div>
          <ChevronRight size={20} className="text-gray-400" />
        </button>
        
        <button className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
              <Settings size={18} className="text-gray-600" />
            </div>
            <span className="font-medium text-[#0F172A]">Settings</span>
          </div>
          <ChevronRight size={20} className="text-gray-400" />
        </button>
        
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-between p-4 hover:bg-red-50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
              <LogOut size={18} className="text-red-600" />
            </div>
            <span className="font-medium text-red-600">Logout</span>
          </div>
          <ChevronRight size={20} className="text-red-400" />
        </button>
      </div>
    </div>
  );
};

export default ProfilePage;
