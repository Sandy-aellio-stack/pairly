import { useState } from 'react';
import { Camera, Edit2, MapPin, Calendar, Heart, Settings, Shield, LogOut, ChevronRight, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const ProfilePage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || 'User',
    bio: user?.bio || 'Looking for meaningful connections...',
    age: user?.age || 25,
    intent: user?.intent || 'dating',
  });

  const handleLogout = () => {
    logout();
    navigate('/');
    toast.success('Logged out successfully');
  };

  const handleSave = () => {
    // TODO: Save to API
    setIsEditing(false);
    toast.success('Profile updated!');
  };

  const intentOptions = [
    { value: 'dating', label: 'Dating' },
    { value: 'serious', label: 'Serious Relationship' },
    { value: 'casual', label: 'Casual' },
    { value: 'friendship', label: 'Friendship' },
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
                  {user?.profile_pictures?.[0] ? (
                    <img src={user.profile_pictures[0]} alt="Profile" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-4xl">{profileData.name[0]?.toUpperCase()}</span>
                  )}
                </div>
              </div>
              <button className="absolute bottom-0 right-0 w-8 h-8 bg-[#0F172A] rounded-full flex items-center justify-center text-white shadow-lg">
                <Camera size={14} />
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
                <h1 className="text-2xl font-bold text-[#0F172A]">{profileData.name}, {profileData.age}</h1>
              )}
              <p className="text-gray-500 text-sm flex items-center gap-1">
                <MapPin size={14} />
                Bangalore, India
              </p>
            </div>
            
            <button
              onClick={() => isEditing ? handleSave() : setIsEditing(true)}
              className={`px-4 py-2 rounded-full font-medium text-sm flex items-center gap-2 transition-colors ${
                isEditing
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-[#E9D5FF] text-[#0F172A] hover:bg-[#DDD6FE]'
              }`}
            >
              {isEditing ? <><Check size={16} /> Save</> : <><Edit2 size={16} /> Edit</>}
            </button>
          </div>

          {/* Bio */}
          <div className="mb-4">
            <label className="text-xs font-medium text-gray-500 block mb-1">Bio</label>
            {isEditing ? (
              <textarea
                value={profileData.bio}
                onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                className="w-full p-3 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none resize-none"
                rows={3}
              />
            ) : (
              <p className="text-gray-700">{profileData.bio}</p>
            )}
          </div>

          {/* Intent */}
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-2">Looking for</label>
            {isEditing ? (
              <div className="flex flex-wrap gap-2">
                {intentOptions.map((option) => (
                  <button
                    key={option.value}
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
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-2xl p-4 text-center shadow-md">
          <p className="text-3xl font-bold text-[#0F172A]">{user?.credits_balance || 10}</p>
          <p className="text-xs text-gray-500">Coins</p>
        </div>
        <div className="bg-white rounded-2xl p-4 text-center shadow-md">
          <p className="text-3xl font-bold text-[#0F172A]">12</p>
          <p className="text-xs text-gray-500">Matches</p>
        </div>
        <div className="bg-white rounded-2xl p-4 text-center shadow-md">
          <p className="text-3xl font-bold text-[#0F172A]">48</p>
          <p className="text-xs text-gray-500">Likes</p>
        </div>
      </div>

      {/* Menu Items */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <button className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#E9D5FF]/50 flex items-center justify-center">
              <Heart size={18} className="text-[#0F172A]" />
            </div>
            <span className="font-medium text-[#0F172A]">Preferences</span>
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
