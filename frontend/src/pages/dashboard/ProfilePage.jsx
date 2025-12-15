import { useState, useEffect } from 'react';
import { User, Heart, MapPin, Save } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { userAPI } from '@/services/api';

const ProfilePage = () => {
  const { user, initialize } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

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
    setError('');
    setSuccess('');
    try {
      await userAPI.updateProfile(profile);
      setSuccess('Profile updated!');
      await initialize();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePreferencesSave = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await userAPI.updatePreferences(preferences);
      setSuccess('Preferences updated!');
      await initialize();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Profile</h1>

      {success && (
        <div className="bg-green-500/10 border border-green-500/30 text-green-400 px-4 py-3 rounded-xl mb-6">
          {success}
        </div>
      )}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6">
          {error}
        </div>
      )}

      {/* Profile Section */}
      <div className="card-dark mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
            <User size={20} className="text-purple-400" />
          </div>
          <h2 className="text-lg font-semibold">Basic Info</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Name</label>
            <input
              type="text"
              value={profile.name}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              className="input-dark"
            />
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-2">Bio</label>
            <textarea
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              className="input-dark min-h-[100px] resize-none"
              placeholder="Tell others about yourself..."
            />
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-2">Looking for</label>
            <select
              value={profile.intent}
              onChange={(e) => setProfile({ ...profile, intent: e.target.value })}
              className="input-dark"
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

      {/* Preferences Section */}
      <div className="card-dark mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center">
            <Heart size={20} className="text-pink-400" />
          </div>
          <h2 className="text-lg font-semibold">Preferences</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Interested In</label>
            <select
              value={preferences.interested_in}
              onChange={(e) => setPreferences({ ...preferences, interested_in: e.target.value })}
              className="input-dark"
            >
              <option value="male">Men</option>
              <option value="female">Women</option>
              <option value="other">Everyone</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-white/60 mb-2">Min Age</label>
              <input
                type="number"
                value={preferences.min_age}
                onChange={(e) => setPreferences({ ...preferences, min_age: parseInt(e.target.value) })}
                className="input-dark"
                min={18}
              />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-2">Max Age</label>
              <input
                type="number"
                value={preferences.max_age}
                onChange={(e) => setPreferences({ ...preferences, max_age: parseInt(e.target.value) })}
                className="input-dark"
                max={100}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-2">
              <MapPin size={14} className="inline mr-1" />
              Max Distance (km)
            </label>
            <input
              type="number"
              value={preferences.max_distance_km}
              onChange={(e) => setPreferences({ ...preferences, max_distance_km: parseInt(e.target.value) })}
              className="input-dark"
              min={1}
              max={500}
            />
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

      {/* Account Info */}
      <div className="card-dark">
        <h2 className="text-lg font-semibold mb-4">Account</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-white/60">Email</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60">Mobile</span>
            <span>{user?.mobile_number}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60">Age</span>
            <span>{user?.age}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60">Verified</span>
            <span className={user?.is_verified ? 'text-green-400' : 'text-yellow-400'}>
              {user?.is_verified ? 'Yes' : 'Pending'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
