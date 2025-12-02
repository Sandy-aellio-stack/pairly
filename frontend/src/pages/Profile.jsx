import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { MapPin, MessageSquare, Calendar } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const Profile = () => {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    try {
      const response = await api.get(`/profiles/${userId}`);
      setProfile(response.data);
    } catch (error) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <p>Loading profile...</p>
        </div>
      </MainLayout>
    );
  }

  if (!profile) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-96 space-y-4">
          <p className="text-gray-600">Profile not found</p>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row gap-8">
              {/* Profile Picture */}
              <div className="flex-shrink-0">
                <Avatar className="h-48 w-48">
                  <AvatarImage src={profile.profile_picture_url} />
                  <AvatarFallback className="text-6xl">
                    {profile.display_name?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              </div>

              {/* Profile Info */}
              <div className="flex-1 space-y-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-3xl font-bold">{profile.display_name}</h1>
                    {profile.is_online && (
                      <Badge variant="success" className="bg-green-500">Online</Badge>
                    )}
                  </div>
                  <p className="text-gray-600 text-lg">{profile.age} years old</p>
                </div>

                {profile.bio && (
                  <div>
                    <h3 className="font-semibold mb-1">About</h3>
                    <p className="text-gray-700">{profile.bio}</p>
                  </div>
                )}

                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                  {profile.location && (
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-2" />
                      <span>Location available</span>
                    </div>
                  )}
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    <span>Joined {new Date(profile.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {profile.price_per_message > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">Message Price:</span>
                    <Badge variant="secondary">{profile.price_per_message} credits</Badge>
                  </div>
                )}

                <Button
                  onClick={() => navigate(`/messages/${userId}`)}
                  className="w-full md:w-auto"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Send Message
                </Button>
              </div>
            </div>

            {/* Gallery */}
            {profile.gallery_urls && profile.gallery_urls.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold mb-4">Gallery</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {profile.gallery_urls.map((url, index) => (
                    <div key={index} className="aspect-square rounded-lg overflow-hidden">
                      <img
                        src={url}
                        alt={`Gallery ${index + 1}`}
                        className="w-full h-full object-cover hover:scale-105 transition-transform"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default Profile;