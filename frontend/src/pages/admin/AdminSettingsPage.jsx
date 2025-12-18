import { useState } from 'react';
import { Settings, Globe, CreditCard, Bell, Shield, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const AdminSettingsPage = () => {
  const [isSaving, setIsSaving] = useState(false);
  const [settings, setSettings] = useState({
    // General
    appName: 'TrueBond',
    tagline: 'Real connections, meaningful bonds',
    maintenanceMode: false,

    // Matching
    defaultSearchRadius: 50,
    maxSearchRadius: 500,
    minAge: 18,
    maxAge: 100,

    // Credits
    signupBonus: 10,
    messageCost: 1,
    audioCallCost: 5,
    videoCallCost: 10,

    // Subscriptions
    starterCoins: 100,
    starterPrice: 100,
    popularCoins: 500,
    popularPrice: 450,
    premiumCoins: 1000,
    premiumPrice: 800,

    // Safety
    autoModeration: true,
    profanityFilter: true,
    photoVerification: true,
  });

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    toast.success('Settings saved successfully!');
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
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A] mb-2">App Settings</h1>
          <p className="text-gray-600">Configure global app settings and parameters.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-3 bg-[#0F172A] text-white rounded-xl font-medium hover:bg-gray-800 transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          {isSaving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
          Save Changes
        </button>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* General Settings */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-[#E9D5FF] rounded-xl flex items-center justify-center">
              <Globe size={20} className="text-[#0F172A]" />
            </div>
            <h2 className="text-lg font-bold text-[#0F172A]">General</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">App Name</label>
              <input
                type="text"
                value={settings.appName}
                onChange={(e) => setSettings({ ...settings, appName: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">Tagline</label>
              <input
                type="text"
                value={settings.tagline}
                onChange={(e) => setSettings({ ...settings, tagline: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
              />
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-[#0F172A]">Maintenance Mode</p>
                <p className="text-sm text-gray-500">Temporarily disable the app</p>
              </div>
              <ToggleSwitch
                enabled={settings.maintenanceMode}
                onChange={() => setSettings({ ...settings, maintenanceMode: !settings.maintenanceMode })}
              />
            </div>
          </div>
        </div>

        {/* Matching Settings */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-[#FCE7F3] rounded-xl flex items-center justify-center">
              <Settings size={20} className="text-[#0F172A]" />
            </div>
            <h2 className="text-lg font-bold text-[#0F172A]">Matching</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">Default Search Radius (km)</label>
              <input
                type="number"
                value={settings.defaultSearchRadius}
                onChange={(e) => setSettings({ ...settings, defaultSearchRadius: parseInt(e.target.value) })}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">Max Search Radius (km)</label>
              <input
                type="number"
                value={settings.maxSearchRadius}
                onChange={(e) => setSettings({ ...settings, maxSearchRadius: parseInt(e.target.value) })}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">Min Age</label>
                <input
                  type="number"
                  value={settings.minAge}
                  onChange={(e) => setSettings({ ...settings, minAge: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">Max Age</label>
                <input
                  type="number"
                  value={settings.maxAge}
                  onChange={(e) => setSettings({ ...settings, maxAge: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Credits Settings */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-[#DBEAFE] rounded-xl flex items-center justify-center">
              <CreditCard size={20} className="text-blue-600" />
            </div>
            <h2 className="text-lg font-bold text-[#0F172A]">Credits & Pricing</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">Signup Bonus (coins)</label>
              <input
                type="number"
                value={settings.signupBonus}
                onChange={(e) => setSettings({ ...settings, signupBonus: parseInt(e.target.value) })}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">Message Cost</label>
                <input
                  type="number"
                  value={settings.messageCost}
                  onChange={(e) => setSettings({ ...settings, messageCost: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">Audio/min</label>
                <input
                  type="number"
                  value={settings.audioCallCost}
                  onChange={(e) => setSettings({ ...settings, audioCallCost: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">Video/min</label>
                <input
                  type="number"
                  value={settings.videoCallCost}
                  onChange={(e) => setSettings({ ...settings, videoCallCost: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Safety Settings */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <Shield size={20} className="text-green-600" />
            </div>
            <h2 className="text-lg font-bold text-[#0F172A]">Safety & Moderation</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-[#0F172A]">Auto Moderation</p>
                <p className="text-sm text-gray-500">AI-powered content screening</p>
              </div>
              <ToggleSwitch
                enabled={settings.autoModeration}
                onChange={() => setSettings({ ...settings, autoModeration: !settings.autoModeration })}
              />
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-[#0F172A]">Profanity Filter</p>
                <p className="text-sm text-gray-500">Block offensive language</p>
              </div>
              <ToggleSwitch
                enabled={settings.profanityFilter}
                onChange={() => setSettings({ ...settings, profanityFilter: !settings.profanityFilter })}
              />
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-[#0F172A]">Photo Verification</p>
                <p className="text-sm text-gray-500">Require selfie verification</p>
              </div>
              <ToggleSwitch
                enabled={settings.photoVerification}
                onChange={() => setSettings({ ...settings, photoVerification: !settings.photoVerification })}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSettingsPage;
