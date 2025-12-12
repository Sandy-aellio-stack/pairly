import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, Bell, Lock, User, Camera, Globe, Eye, Moon, 
  Smartphone, CreditCard, HelpCircle, LogOut, ChevronRight,
  Sparkles, MapPin, Mail, Key
} from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';

const Settings = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    twoFactorEnabled: user?.twofa_enabled || false,
    emailNotifications: true,
    pushNotifications: true,
    messageNotifications: true,
    matchNotifications: true,
    locationSharing: true,
    privateProfile: false,
    darkMode: false,
  });

  const handleToggle2FA = async () => {
    try {
      if (settings.twoFactorEnabled) {
        await api.post('/twofa/disable');
        toast.success('Two-factor authentication disabled');
      } else {
        const response = await api.post('/twofa/enable-totp');
        toast.success('Two-factor authentication enabled');
      }
      setSettings({ ...settings, twoFactorEnabled: !settings.twoFactorEnabled });
    } catch (error) {
      toast.error('Failed to update 2FA settings');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const settingSections = [
    {
      title: 'Account',
      icon: User,
      items: [
        { label: 'Edit Profile', icon: User, action: () => navigate('/profile/edit') },
        { label: 'Change Email', icon: Mail, action: () => toast.info('Coming soon') },
        { label: 'Change Password', icon: Key, action: () => toast.info('Coming soon') },
      ],
    },
    {
      title: 'Privacy',
      icon: Lock,
      items: [
        { label: 'Private Profile', icon: Eye, toggle: true, key: 'privateProfile' },
        { label: 'Location Sharing', icon: MapPin, toggle: true, key: 'locationSharing' },
        { label: 'Blocked Users', icon: Lock, action: () => toast.info('Coming soon') },
      ],
    },
    {
      title: 'Notifications',
      icon: Bell,
      items: [
        { label: 'Push Notifications', icon: Smartphone, toggle: true, key: 'pushNotifications' },
        { label: 'Email Notifications', icon: Mail, toggle: true, key: 'emailNotifications' },
        { label: 'Match Notifications', icon: Bell, toggle: true, key: 'matchNotifications' },
        { label: 'Message Notifications', icon: Bell, toggle: true, key: 'messageNotifications' },
      ],
    },
    {
      title: 'Appearance',
      icon: Moon,
      items: [
        { label: 'Dark Mode', icon: Moon, toggle: true, key: 'darkMode' },
      ],
    },
  ];

  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto space-y-6 pb-20 md:pb-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
        </div>

        {/* Profile Card */}
        <Card className="border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="relative">
                <Avatar className="h-20 w-20 border-2 border-violet-100">
                  <AvatarImage src={user?.profile_picture_url || 'https://i.pravatar.cc/100?img=1'} />
                  <AvatarFallback className="bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white text-2xl">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <Button 
                  size="icon" 
                  className="absolute -bottom-1 -right-1 h-8 w-8 rounded-full bg-violet-600 hover:bg-violet-700"
                >
                  <Camera className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-slate-900">{user?.name || 'User'}</h2>
                  {user?.role === 'creator' && (
                    <Badge className="bg-gradient-to-r from-fuchsia-500 to-pink-500">
                      <Sparkles className="h-3 w-3 mr-1" />
                      Creator
                    </Badge>
                  )}
                </div>
                <p className="text-slate-500">{user?.email}</p>
              </div>
              <Button 
                variant="outline" 
                className="rounded-full border-slate-300"
                onClick={() => navigate('/profile/edit')}
              >
                Edit
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Security Card */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                <Shield className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <CardTitle className="text-lg text-slate-900">Security</CardTitle>
                <CardDescription>Protect your account</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50">
              <div className="space-y-0.5">
                <Label className="text-slate-900">Two-Factor Authentication</Label>
                <p className="text-sm text-slate-500">Add an extra layer of security</p>
              </div>
              <Switch
                checked={settings.twoFactorEnabled}
                onCheckedChange={handleToggle2FA}
              />
            </div>
          </CardContent>
        </Card>

        {/* Settings Sections */}
        {settingSections.map((section, sectionIndex) => {
          const SectionIcon = section.icon;
          return (
            <Card key={sectionIndex} className="border-slate-200">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                    <SectionIcon className="h-5 w-5 text-violet-600" />
                  </div>
                  <CardTitle className="text-lg text-slate-900">{section.title}</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {section.items.map((item, itemIndex) => {
                  const ItemIcon = item.icon;
                  return (
                    <div key={itemIndex}>
                      {item.toggle ? (
                        <div className="flex items-center justify-between p-4 rounded-xl hover:bg-slate-50 transition">
                          <div className="flex items-center gap-3">
                            <ItemIcon className="h-5 w-5 text-slate-500" />
                            <span className="text-slate-700">{item.label}</span>
                          </div>
                          <Switch
                            checked={settings[item.key]}
                            onCheckedChange={(checked) =>
                              setSettings({ ...settings, [item.key]: checked })
                            }
                          />
                        </div>
                      ) : (
                        <button
                          onClick={item.action}
                          className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-slate-50 transition"
                        >
                          <div className="flex items-center gap-3">
                            <ItemIcon className="h-5 w-5 text-slate-500" />
                            <span className="text-slate-700">{item.label}</span>
                          </div>
                          <ChevronRight className="h-5 w-5 text-slate-400" />
                        </button>
                      )}
                      {itemIndex < section.items.length - 1 && <Separator className="my-1" />}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          );
        })}

        {/* Subscription Card */}
        <Card className="border-slate-200 overflow-hidden">
          <div className="bg-gradient-to-r from-violet-600 to-fuchsia-600 p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold">Upgrade to Premium</h3>
                <p className="text-white/80 mt-1">Unlock all features and get more matches</p>
              </div>
              <Button className="bg-white text-violet-600 hover:bg-slate-100 rounded-full">
                Upgrade
              </Button>
            </div>
          </div>
        </Card>

        {/* Support & Help */}
        <Card className="border-slate-200">
          <CardContent className="p-0">
            <button
              onClick={() => navigate('/support')}
              className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition"
            >
              <div className="flex items-center gap-3">
                <HelpCircle className="h-5 w-5 text-slate-500" />
                <span className="text-slate-700">Help & Support</span>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-400" />
            </button>
          </CardContent>
        </Card>

        {/* Logout Button */}
        <Button
          variant="outline"
          className="w-full rounded-xl py-6 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700"
          onClick={handleLogout}
        >
          <LogOut className="h-5 w-5 mr-2" />
          Log Out
        </Button>

        {/* App Info */}
        <div className="text-center text-sm text-slate-400 space-y-1">
          <p>Pairly v1.0.0</p>
          <p>Made with ❤️ for meaningful connections</p>
        </div>
      </div>
    </MainLayout>
  );
};

export default Settings;
