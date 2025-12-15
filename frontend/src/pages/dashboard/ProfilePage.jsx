import { useState, useEffect } from 'react';
import { User, Heart, MapPin, Save, Camera, Check } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { userAPI } from '@/services/api';
import { toast } from 'sonner';

const ProfilePage = () => {
  const { user, initialize } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');

  const [profile, setProfile] = useState({
    name: '',
    bio: '',
    intent: 'dating',
  });

  const [preferences, setPreferences] = useState({
    interested_in: '',
    min_age: 18,
    max_age: 50,
    max_distance_km: 50,
  });

  useEffect(() => {
    if (user) {
      setProfile({
        name: user.name || '',
        bio: user.bio || '',
        intent: user.intent || 'dating',
      });
      setPreferences({
        interested_in: user.preferences?.interested_in || '',
        min_age: user.preferences?.min_age || 18,
        max_age: user.preferences?.max_age || 50,
        max_distance_km: user.preferences?.max_distance_km || 50,
      });
    }
  }, [user]);

  const handleProfileSave = async () => {
    setLoading(true);
    try {
      await userAPI.updateProfile(profile);
      toast.success('Profile updated!');
      await initialize();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePreferencesSave = async () => {
    setLoading(true);
    try {
      await userAPI.updatePreferences(preferences);
      toast.success('Preferences updated!');
      await initialize();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Profile Header */}
      <div className="card mb-6">
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white text-3xl font-bold">
              {user?.name?.[0]}
            </div>
            <button className="absolute bottom-0 right-0 w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center shadow-lg hover:bg-purple-600 transition-colors">
              <Camera size={16} />
            </button>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{user?.name}</h1>
            <p className="text-gray-500">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              {user?.is_verified ? (
                <span className="inline-flex items-center gap-1 text-green-600 text-sm bg-green-50 px-2 py-1 rounded-full">
                  <Check size={14} /> Verified
                </span>
              ) : (
                <span className="text-yellow-600 text-sm bg-yellow-50 px-2 py-1 rounded-full">Pending Verification</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-6 py-3 rounded-xl font-medium transition-all ${
            activeTab === 'profile'
              ? 'bg-purple-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <User size={18} className="inline mr-2" />
          Profile
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`px-6 py-3 rounded-xl font-medium transition-all ${
            activeTab === 'preferences'
              ? 'bg-purple-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Heart size={18} className="inline mr-2" />
          Preferences
        </button>
      </div>

      {activeTab === 'profile' ? (
        <div className="card">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Bio</label>
              <textarea
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                className="input min-h-[120px] resize-none"
                placeholder="Tell others about yourself..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Looking for</label>
              <select
                value={profile.intent}
                onChange={(e) => setProfile({ ...profile, intent: e.target.value })}
                className="input"
              >
                <option value="dating">Dating</option>
                <option value="serious">Serious Relationship</option>
                <option value="casual">Casual</option>
                <option value="friendship">Friendship</option>
              </select>
            </div>

            <button
              onClick={handleProfileSave}
              disabled={loading}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Save size={18} />
              Save Profile
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Interested In</label>
              <select
                value={preferences.interested_in}
                onChange={(e) => setPreferences({ ...preferences, interested_in: e.target.value })}
                className="input"
              >
                <option value="male">Men</option>
                <option value="female">Women</option>
                <option value="other">Everyone</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Min Age</label>
                <input
                  type="number"
                  value={preferences.min_age}
                  onChange={(e) => setPreferences({ ...preferences, min_age: parseInt(e.target.value) })}
                  className="input"
                  min={18}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Age</label>
                <input
                  type="number"
                  value={preferences.max_age}
                  onChange={(e) => setPreferences({ ...preferences, max_age: parseInt(e.target.value) })}
                  className="input"
                  max={100}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin size={14} className="inline mr-1" />
                Max Distance (km)
              </label>
              <input
                type="range"
                value={preferences.max_distance_km}
                onChange={(e) => setPreferences({ ...preferences, max_distance_km: parseInt(e.target.value) })}
                className="w-full accent-purple-500"
                min={1}
                max={500}
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>1 km</span>
                <span className="font-medium text-purple-600">{preferences.max_distance_km} km</span>
                <span>500 km</span>
              </div>
            </div>

            <button
              onClick={handlePreferencesSave}
              disabled={loading}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Save size={18} />
              Save Preferences
            </button>
          </div>
        </div>
      )}

      {/* Account Info */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Info</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Email</span>
            <span className="text-gray-900">{user?.email}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Mobile</span>
            <span className="text-gray-900">{user?.mobile_number || 'Not set'}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Age</span>
            <span className="text-gray-900">{user?.age}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Member since</span>
            <span className="text-gray-900">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
