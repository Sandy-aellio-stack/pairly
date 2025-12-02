import React, { useEffect, useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { MapPin, Heart, X, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { toast } from 'sonner';

const Discovery = () => {
  const [profiles, setProfiles] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    try {
      const response = await api.get('/discover?limit=20');
      setProfiles(response.data);
    } catch (error) {
      toast.error('Failed to load profiles');
    } finally {
      setLoading(false);
    }
  };

  const currentProfile = profiles[currentIndex];

  const handleNext = () => {
    if (currentIndex < profiles.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      toast.info('No more profiles. Refreshing...');
      fetchProfiles();
      setCurrentIndex(0);
    }
  };

  const handleLike = () => {
    toast.success('Profile liked!');
    handleNext();
  };

  const handleSkip = () => {
    handleNext();
  };

  const handleMessage = () => {
    if (currentProfile) {
      navigate(`/messages/${currentProfile.user_id}`);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <p>Loading profiles...</p>
        </div>
      </MainLayout>
    );
  }

  if (!currentProfile) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-96 space-y-4">
          <p className="text-gray-600">No profiles available at the moment</p>
          <Button onClick={fetchProfiles}>Refresh</Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Discover</h1>

        <Card className="overflow-hidden">
          {/* Profile Image */}
          <div className="relative h-96 bg-gradient-to-br from-pink-100 to-purple-100">
            {currentProfile.profile_picture_url ? (
              <img
                src={currentProfile.profile_picture_url}
                alt={currentProfile.display_name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Avatar className="h-48 w-48">
                  <AvatarFallback className="text-6xl">
                    {currentProfile.display_name?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              </div>
            )}
          </div>

          <CardContent className="p-6">
            {/* Profile Info */}
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold">{currentProfile.display_name}</h2>
                  <p className="text-gray-600">{currentProfile.age} years old</p>
                </div>
                {currentProfile.price_per_message > 0 && (
                  <Badge variant="secondary">{currentProfile.price_per_message} credits/message</Badge>
                )}
              </div>

              {currentProfile.bio && (
                <p className="text-gray-700">{currentProfile.bio}</p>
              )}

              {currentProfile.location && (
                <div className="flex items-center text-gray-600">
                  <MapPin className="h-4 w-4 mr-2" />
                  <span>Location available</span>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex justify-center space-x-4 mt-8">
              <Button
                size="lg"
                variant="outline"
                className="rounded-full h-16 w-16"
                onClick={handleSkip}
              >
                <X className="h-6 w-6" />
              </Button>
              <Button
                size="lg"
                className="rounded-full h-16 w-16 bg-pink-500 hover:bg-pink-600"
                onClick={handleLike}
              >
                <Heart className="h-6 w-6" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="rounded-full h-16 w-16"
                onClick={handleMessage}
              >
                <MessageSquare className="h-6 w-6" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="text-center mt-4 text-gray-600">
          Profile {currentIndex + 1} of {profiles.length}
        </div>
      </div>
    </MainLayout>
  );
};

export default Discovery;