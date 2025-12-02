import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Upload, X } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';

const EditProfile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    bio: '',
    age: '',
    price_per_message: 0,
    location: { lat: 0, lng: 0 },
  });
  const [profilePicture, setProfilePicture] = useState(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get(`/profiles/${user.id}`);
      setFormData({
        display_name: response.data.display_name || '',
        bio: response.data.bio || '',
        age: response.data.age || '',
        price_per_message: response.data.price_per_message || 0,
        location: response.data.location || { lat: 0, lng: 0 },
      });
      setProfilePicture(response.data.profile_picture_url);
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/media/upload-profile-picture', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setProfilePicture(response.data.url);
      toast.success('Profile picture updated!');
    } catch (error) {
      toast.error('Failed to upload image');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.put(`/profiles/${user.id}`, formData);
      toast.success('Profile updated successfully!');
      navigate(`/profile/${user.id}`);
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Edit Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Profile Picture */}
              <div className="flex flex-col items-center space-y-4">
                <Avatar className="h-32 w-32">
                  <AvatarImage src={profilePicture} />
                  <AvatarFallback className="text-4xl">
                    {formData.display_name?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <Label htmlFor="profile-picture" className="cursor-pointer">
                  <div className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700">
                    <Upload className="h-4 w-4" />
                    <span>Upload Photo</span>
                  </div>
                  <Input
                    id="profile-picture"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </Label>
              </div>

              {/* Display Name */}
              <div className="space-y-2">
                <Label htmlFor="display_name">Display Name</Label>
                <Input
                  id="display_name"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleChange}
                  required
                />
              </div>

              {/* Bio */}
              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  name="bio"
                  value={formData.bio}
                  onChange={handleChange}
                  rows={4}
                  placeholder="Tell others about yourself..."
                />
              </div>

              {/* Age */}
              <div className="space-y-2">
                <Label htmlFor="age">Age</Label>
                <Input
                  id="age"
                  name="age"
                  type="number"
                  value={formData.age}
                  onChange={handleChange}
                  required
                />
              </div>

              {/* Price per message (Creator only) */}
              {user?.role === 'creator' && (
                <div className="space-y-2">
                  <Label htmlFor="price_per_message">Price per Message (Credits)</Label>
                  <Input
                    id="price_per_message"
                    name="price_per_message"
                    type="number"
                    value={formData.price_per_message}
                    onChange={handleChange}
                    min="0"
                  />
                  <p className="text-sm text-gray-500">
                    Set to 0 for free messages. Fans will pay this amount per message.
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-4">
                <Button type="submit" className="flex-1" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate(`/profile/${user.id}`)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default EditProfile;