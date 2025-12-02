import React, { useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Shield, Bell, Lock } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';

const Settings = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    twoFactorEnabled: user?.twofa_enabled || false,
    emailNotifications: true,
    pushNotifications: true,
  });

  const handleToggle2FA = async () => {
    try {
      if (settings.twoFactorEnabled) {
        await api.post('/twofa/disable');
        toast.success('Two-factor authentication disabled');
      } else {
        const response = await api.post('/twofa/enable-totp');
        // In a real app, show QR code modal here
        toast.success('Two-factor authentication enabled');
      }
      setSettings({ ...settings, twoFactorEnabled: !settings.twoFactorEnabled });
    } catch (error) {
      toast.error('Failed to update 2FA settings');
    }
  };

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold">Settings</h1>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <CardTitle>Security</CardTitle>
            </div>
            <CardDescription>Manage your account security settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Two-Factor Authentication</Label>
                <p className="text-sm text-gray-500">Add an extra layer of security to your account</p>
              </div>
              <Switch
                checked={settings.twoFactorEnabled}
                onCheckedChange={handleToggle2FA}
              />
            </div>

            <Separator />

            <div>
              <Label>Change Password</Label>
              <p className="text-sm text-gray-500 mb-2">Update your password regularly for better security</p>
              <Button variant="outline" size="sm">
                Change Password
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5" />
              <CardTitle>Notifications</CardTitle>
            </div>
            <CardDescription>Manage how you receive notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Email Notifications</Label>
                <p className="text-sm text-gray-500">Receive notifications via email</p>
              </div>
              <Switch
                checked={settings.emailNotifications}
                onCheckedChange={(checked) =>
                  setSettings({ ...settings, emailNotifications: checked })
                }
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Push Notifications</Label>
                <p className="text-sm text-gray-500">Receive push notifications on your device</p>
              </div>
              <Switch
                checked={settings.pushNotifications}
                onCheckedChange={(checked) =>
                  setSettings({ ...settings, pushNotifications: checked })
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Lock className="h-5 w-5" />
              <CardTitle>Privacy</CardTitle>
            </div>
            <CardDescription>Control your privacy preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Account Visibility</Label>
              <p className="text-sm text-gray-500 mb-2">Control who can see your profile</p>
              <Button variant="outline" size="sm">
                Manage Visibility
              </Button>
            </div>

            <Separator />

            <div>
              <Label className="text-red-600">Danger Zone</Label>
              <p className="text-sm text-gray-500 mb-2">Permanently delete your account</p>
              <Button variant="destructive" size="sm">
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default Settings;