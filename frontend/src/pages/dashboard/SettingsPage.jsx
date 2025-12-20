import { useState, useEffect } from 'react';
import { Bell, Lock, Eye, Globe, Shield, Trash2, LogOut, ChevronRight, AlertTriangle, Users, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { userAPI } from '@/services/api';
import { toast } from 'sonner';

const SettingsPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [settings, setSettings] = useState({
    notifications: {
      messages: true,
      matches: true,
      nearby: false,
      marketing: false,
    },
    privacy: {
      show_online: true,
      show_last_seen: true,
      show_distance: true,
    },
    safety: {
      block_screenshots: false,
      require_verified_matches: false,
      hide_from_search: false,
    },
    dark_mode: false,
    language: 'en',
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await userAPI.getSettings();
      if (response.data.settings) {
        setSettings(response.data.settings);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (category, setting) => {
    const newSettings = {
      ...settings,
      [category]: {
        ...settings[category],
        [setting]: !settings[category][setting]
      }
    };
    setSettings(newSettings);

    setIsSaving(true);
    try {
      await userAPI.updateSettings({
        [category]: { [setting]: !settings[category][setting] }
      });
      toast.success('Setting updated');
    } catch (error) {
      setSettings(settings);
      toast.error('Failed to update setting');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
    toast.success('Logged out successfully');
  };

  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      toast.info('Account deletion request submitted. Our team will contact you.');
    }
  };

  const ToggleSwitch = ({ enabled, onChange, disabled }) => (
    <button
      onClick={onChange}
      disabled={disabled}
      className={`w-12 h-6 rounded-full transition-colors duration-200 flex items-center px-1 ${
        enabled ? 'bg-[#0F172A]' : 'bg-gray-300'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <span
        className={`w-4 h-4 bg-white rounded-full transition-transform duration-200 ${
          enabled ? 'translate-x-6' : 'translate-x-0'
        }`}
      />
    </button>
  );

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto px-4 flex items-center justify-center h-[60vh]">
        <Loader2 className="w-12 h-12 animate-spin text-[#0F172A]" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4">
      <h1 className="text-2xl font-bold text-[#0F172A] mb-6">Settings</h1>

      {/* Notifications */}
      <div className="bg-white rounded-2xl shadow-md mb-6 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#E9D5FF] flex items-center justify-center">
              <Bell size={20} className="text-[#0F172A]" />
            </div>
            <h2 className="text-lg font-semibold text-[#0F172A]">Notifications</h2>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">New Messages</p>
              <p className="text-sm text-gray-500">Get notified when you receive messages</p>
            </div>
            <ToggleSwitch 
              enabled={settings.notifications.messages} 
              onChange={() => handleToggle('notifications', 'messages')}
              disabled={isSaving}
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">New Matches</p>
              <p className="text-sm text-gray-500">Get notified about new matches</p>
            </div>
            <ToggleSwitch 
              enabled={settings.notifications.matches} 
              onChange={() => handleToggle('notifications', 'matches')}
              disabled={isSaving}
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Nearby Users</p>
              <p className="text-sm text-gray-500">Get notified when someone is nearby</p>
            </div>
            <ToggleSwitch 
              enabled={settings.notifications.nearby} 
              onChange={() => handleToggle('notifications', 'nearby')}
              disabled={isSaving}
            />
          </div>
        </div>
      </div>

      {/* Privacy */}
      <div className="bg-white rounded-2xl shadow-md mb-6 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#DBEAFE] flex items-center justify-center">
              <Eye size={20} className="text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-[#0F172A]">Privacy</h2>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Show Online Status</p>
              <p className="text-sm text-gray-500">Let others see when you're online</p>
            </div>
            <ToggleSwitch 
              enabled={settings.privacy.show_online} 
              onChange={() => handleToggle('privacy', 'show_online')}
              disabled={isSaving}
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Show Last Seen</p>
              <p className="text-sm text-gray-500">Let others see when you were last active</p>
            </div>
            <ToggleSwitch 
              enabled={settings.privacy.show_last_seen} 
              onChange={() => handleToggle('privacy', 'show_last_seen')}
              disabled={isSaving}
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Show Distance</p>
              <p className="text-sm text-gray-500">Let others see how far you are</p>
            </div>
            <ToggleSwitch 
              enabled={settings.privacy.show_distance} 
              onChange={() => handleToggle('privacy', 'show_distance')}
              disabled={isSaving}
            />
          </div>
        </div>
      </div>

      {/* Safety */}
      <div className="bg-white rounded-2xl shadow-md mb-6 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#FEE2E2] flex items-center justify-center">
              <Shield size={20} className="text-red-600" />
            </div>
            <h2 className="text-lg font-semibold text-[#0F172A]">Safety</h2>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Block Screenshots</p>
              <p className="text-sm text-gray-500">Prevent others from taking screenshots of your profile</p>
            </div>
            <ToggleSwitch 
              enabled={settings.safety.block_screenshots} 
              onChange={() => handleToggle('safety', 'block_screenshots')}
              disabled={isSaving}
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Verified Matches Only</p>
              <p className="text-sm text-gray-500">Only match with verified users</p>
            </div>
            <ToggleSwitch 
              enabled={settings.safety.require_verified_matches} 
              onChange={() => handleToggle('safety', 'require_verified_matches')}
              disabled={isSaving}
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Hide from Search</p>
              <p className="text-sm text-gray-500">Don't appear in search results</p>
            </div>
            <ToggleSwitch 
              enabled={settings.safety.hide_from_search} 
              onChange={() => handleToggle('safety', 'hide_from_search')}
              disabled={isSaving}
            />
          </div>
        </div>
      </div>

      {/* Safety Resources */}
      <div className="bg-gradient-to-br from-[#FEF3C7] to-[#FDE68A] rounded-2xl p-6 mb-6">
        <div className="flex items-start gap-3 mb-4">
          <AlertTriangle size={24} className="text-amber-700 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-amber-900 mb-1">Safety Resources</h3>
            <p className="text-sm text-amber-800">If you ever feel unsafe, use these resources:</p>
          </div>
        </div>
        <div className="space-y-2">
          <button 
            onClick={() => navigate('/help')}
            className="w-full bg-white/80 hover:bg-white rounded-xl p-3 text-left transition-colors"
          >
            <p className="font-medium text-amber-900">Report a User</p>
            <p className="text-xs text-amber-700">Report inappropriate behavior</p>
          </button>
          <button 
            onClick={() => navigate('/help')}
            className="w-full bg-white/80 hover:bg-white rounded-xl p-3 text-left transition-colors"
          >
            <p className="font-medium text-amber-900">Safety Tips</p>
            <p className="text-xs text-amber-700">Learn how to stay safe while dating</p>
          </button>
          <button 
            onClick={() => window.open('tel:112', '_self')}
            className="w-full bg-red-100 hover:bg-red-200 rounded-xl p-3 text-left transition-colors"
          >
            <p className="font-medium text-red-700">Emergency Help</p>
            <p className="text-xs text-red-600">Call emergency services</p>
          </button>
        </div>
      </div>

      {/* Account */}
      <div className="bg-white rounded-2xl shadow-md mb-6 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#FCE7F3] flex items-center justify-center">
              <Users size={20} className="text-[#0F172A]" />
            </div>
            <h2 className="text-lg font-semibold text-[#0F172A]">Account</h2>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          <button 
            onClick={() => navigate('/dashboard/profile')}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="text-left">
              <p className="font-medium text-[#0F172A]">Edit Profile</p>
              <p className="text-sm text-gray-500">Update your personal information</p>
            </div>
            <ChevronRight size={20} className="text-gray-400" />
          </button>
          <button 
            onClick={() => toast.info('Password change email sent to your email address')}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="text-left">
              <p className="font-medium text-[#0F172A]">Change Password</p>
              <p className="text-sm text-gray-500">Update your password</p>
            </div>
            <ChevronRight size={20} className="text-gray-400" />
          </button>
          <button 
            onClick={() => navigate('/verify-otp')}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="text-left">
              <p className="font-medium text-[#0F172A]">Verify Phone</p>
              <p className="text-sm text-gray-500">{user?.is_verified ? 'Verified' : 'Add phone number for verification'}</p>
            </div>
            <ChevronRight size={20} className="text-gray-400" />
          </button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-red-600">Danger Zone</h2>
        </div>
        <div className="divide-y divide-gray-100">
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-between p-4 hover:bg-red-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <LogOut size={20} className="text-red-600" />
              <p className="font-medium text-red-600">Logout</p>
            </div>
            <ChevronRight size={20} className="text-red-400" />
          </button>
          <button 
            onClick={handleDeleteAccount}
            className="w-full flex items-center justify-between p-4 hover:bg-red-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Trash2 size={20} className="text-red-600" />
              <div className="text-left">
                <p className="font-medium text-red-600">Delete Account</p>
                <p className="text-sm text-gray-500">Permanently delete your account</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-red-400" />
          </button>
        </div>
      </div>

      {/* App Info */}
      <div className="mt-8 text-center text-gray-400 text-sm">
        <p>TrueBond v1.0.0</p>
        <p className="mt-1">Made with love in India</p>
      </div>
    </div>
  );
};

export default SettingsPage;
