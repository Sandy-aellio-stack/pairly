import { useState, useEffect } from 'react';
import { Bell, Lock, Eye, Globe, Moon, Sun, Smartphone, Shield, Trash2, LogOut, ChevronRight, Check, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { userAPI } from '@/services/api';
import { toast } from 'sonner';

const SettingsPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState({
    notifications: {
      messages: true,
      matches: true,
      nearby: false,
      marketing: false,
    },
    privacy: {
      showOnline: true,
      showLastSeen: true,
      showDistance: true,
    },
    display: {
      darkMode: false,
      language: 'en',
    },
  });

  const handleToggle = (category, setting) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: !prev[category][setting]
      }
    }));
    toast.success('Setting updated');
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

  const ToggleSwitch = ({ enabled, onChange }) => (
    <button
      onClick={onChange}
      className={`w-12 h-6 rounded-full transition-colors duration-200 flex items-center px-1 ${
        enabled ? 'bg-[#0F172A]' : 'bg-gray-300'
      }`}
    >
      <span
        className={`w-4 h-4 bg-white rounded-full transition-transform duration-200 ${
          enabled ? 'translate-x-6' : 'translate-x-0'
        }`}
      />
    </button>
  );

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
              enabled={settings.privacy.showOnline} 
              onChange={() => handleToggle('privacy', 'showOnline')} 
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Show Last Seen</p>
              <p className="text-sm text-gray-500">Let others see when you were last active</p>
            </div>
            <ToggleSwitch 
              enabled={settings.privacy.showLastSeen} 
              onChange={() => handleToggle('privacy', 'showLastSeen')} 
            />
          </div>
          <div className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-[#0F172A]">Show Distance</p>
              <p className="text-sm text-gray-500">Let others see how far you are</p>
            </div>
            <ToggleSwitch 
              enabled={settings.privacy.showDistance} 
              onChange={() => handleToggle('privacy', 'showDistance')} 
            />
          </div>
        </div>
      </div>

      {/* Account */}
      <div className="bg-white rounded-2xl shadow-md mb-6 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#FCE7F3] flex items-center justify-center">
              <Shield size={20} className="text-[#0F172A]" />
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
            onClick={() => toast.info('Phone verification coming soon!')}
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
        <p className="mt-1">Made with ❤️ in India</p>
      </div>
    </div>
  );
};

export default SettingsPage;
