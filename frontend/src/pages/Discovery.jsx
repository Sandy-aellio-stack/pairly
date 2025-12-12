import React, { useEffect, useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  MapPin, Heart, X, MessageSquare, Sparkles, Star, 
  Search, Filter, RefreshCw, ChevronLeft, ChevronRight,
  Zap, Crown
} from 'lucide-react';
import api from '@/services/api';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { toast } from 'sonner';

const Discovery = () => {
  const [profiles, setProfiles] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [swipeDirection, setSwipeDirection] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const response = await api.get('/discover?limit=20');
      if (response.data && response.data.length > 0) {
        setProfiles(response.data);
      } else {
        // Mock data for demo
        setProfiles([
          {
            user_id: '1',
            display_name: 'Emma Wilson',
            age: 26,
            bio: 'Adventure seeker 🌍 | Coffee addict ☕ | Dog mom 🐕 | Let\'s explore the world together!',
            profile_picture_url: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&h=800&fit=crop',
            price_per_message: 5,
            location: 'New York, NY',
            interests: ['Travel', 'Photography', 'Hiking'],
            isVerified: true,
            isCreator: true,
          },
          {
            user_id: '2',
            display_name: 'Jake Thompson',
            age: 28,
            bio: 'Fitness enthusiast 💪 | Tech lover | Always up for a good conversation',
            profile_picture_url: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=600&h=800&fit=crop',
            price_per_message: 3,
            location: 'Los Angeles, CA',
            interests: ['Fitness', 'Tech', 'Music'],
            isVerified: true,
            isCreator: false,
          },
          {
            user_id: '3',
            display_name: 'Sophia Chen',
            age: 24,
            bio: 'Art & design 🎨 | Yoga lover | Foodie at heart | Looking for genuine connections',
            profile_picture_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&h=800&fit=crop',
            price_per_message: 4,
            location: 'San Francisco, CA',
            interests: ['Art', 'Yoga', 'Food'],
            isVerified: true,
            isCreator: true,
          },
          {
            user_id: '4',
            display_name: 'Lucas Brown',
            age: 29,
            bio: 'Music producer 🎵 | Night owl | Coffee runs through my veins',
            profile_picture_url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop',
            price_per_message: 2,
            location: 'Austin, TX',
            interests: ['Music', 'Coffee', 'Gaming'],
            isVerified: false,
            isCreator: false,
          },
        ]);
      }
    } catch (error) {
      // Use mock data on error
      setProfiles([
        {
          user_id: '1',
          display_name: 'Emma Wilson',
          age: 26,
          bio: 'Adventure seeker 🌍 | Coffee addict ☕ | Dog mom 🐕',
          profile_picture_url: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&h=800&fit=crop',
          price_per_message: 5,
          location: 'New York, NY',
          interests: ['Travel', 'Photography', 'Hiking'],
          isVerified: true,
          isCreator: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const currentProfile = profiles[currentIndex];

  const handleSwipe = (direction) => {
    setSwipeDirection(direction);
    setTimeout(() => {
      setSwipeDirection(null);
      if (direction === 'right') {
        toast.success('💕 It\'s a match!', { description: `You liked ${currentProfile?.display_name}` });
      }
      handleNext();
    }, 300);
  };

  const handleNext = () => {
    if (currentIndex < profiles.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      toast.info('No more profiles. Refreshing...');
      fetchProfiles();
      setCurrentIndex(0);
    }
  };

  const handleLike = () => handleSwipe('right');
  const handleSkip = () => handleSwipe('left');
  const handleSuperLike = () => {
    toast.success('⭐ Super Like sent!', { description: `${currentProfile?.display_name} will see this first!` });
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
        <div className="flex items-center justify-center h-[70vh]">
          <div className="text-center">
            <RefreshCw className="h-12 w-12 text-pink-500 mx-auto mb-4 animate-spin" />
            <p className="text-gray-600">Finding amazing people for you...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (!currentProfile) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-[70vh] space-y-6">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-400 to-pink-500 flex items-center justify-center">
            <Heart className="h-12 w-12 text-white" />
          </div>
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">No more profiles</h2>
            <p className="text-gray-600 mb-6">Check back later for new matches!</p>
          </div>
          <Button onClick={fetchProfiles} className="rounded-full px-8">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Discover</h1>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" className="rounded-full">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Card */}
        <div className="relative">
          <Card 
            className={`overflow-hidden shadow-2xl transition-transform duration-300 ${
              swipeDirection === 'left' ? '-translate-x-full rotate-[-20deg] opacity-0' :
              swipeDirection === 'right' ? 'translate-x-full rotate-[20deg] opacity-0' : ''
            }`}
          >
            {/* Profile Image */}
            <div className="relative h-[500px] bg-gradient-to-br from-amber-100 to-pink-100">
              {currentProfile.profile_picture_url ? (
                <img
                  src={currentProfile.profile_picture_url}
                  alt={currentProfile.display_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Avatar className="h-48 w-48">
                    <AvatarFallback className="text-6xl bg-gradient-to-br from-amber-400 to-pink-500 text-white">
                      {currentProfile.display_name?.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </div>
              )}
              
              {/* Gradient Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
              
              {/* Profile Info Overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <h2 className="text-3xl font-bold">{currentProfile.display_name}</h2>
                  <span className="text-2xl">{currentProfile.age}</span>
                  {currentProfile.isVerified && (
                    <svg className="h-6 w-6 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                    </svg>
                  )}
                </div>
                
                {currentProfile.isCreator && (
                  <Badge className="mb-3 bg-gradient-to-r from-amber-500 to-pink-500 border-0">
                    <Sparkles className="h-3 w-3 mr-1" />
                    Creator
                  </Badge>
                )}
                
                {currentProfile.location && (
                  <div className="flex items-center text-white/80 mb-3">
                    <MapPin className="h-4 w-4 mr-1" />
                    <span className="text-sm">{currentProfile.location}</span>
                  </div>
                )}
                
                {currentProfile.bio && (
                  <p className="text-white/90 text-sm line-clamp-2">{currentProfile.bio}</p>
                )}
                
                {currentProfile.interests && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {currentProfile.interests.slice(0, 3).map((interest, i) => (
                      <Badge key={i} variant="secondary" className="bg-white/20 text-white border-0">
                        {interest}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {/* Price Badge */}
              {currentProfile.price_per_message > 0 && (
                <div className="absolute top-4 right-4">
                  <Badge className="bg-white/90 text-gray-800 shadow-lg">
                    <Crown className="h-3 w-3 mr-1 text-amber-500" />
                    {currentProfile.price_per_message} credits/msg
                  </Badge>
                </div>
              )}
            </div>
          </Card>

          {/* Swipe Indicators */}
          {swipeDirection && (
            <div className={`absolute top-1/2 -translate-y-1/2 ${
              swipeDirection === 'left' ? 'left-8' : 'right-8'
            }`}>
              <div className={`text-6xl font-bold ${
                swipeDirection === 'left' ? 'text-red-500' : 'text-green-500'
              }`}>
                {swipeDirection === 'left' ? 'NOPE' : 'LIKE'}
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center items-center gap-4 mt-6">
          <Button
            size="lg"
            variant="outline"
            className="rounded-full h-14 w-14 border-2 border-red-200 hover:border-red-400 hover:bg-red-50"
            onClick={handleSkip}
          >
            <X className="h-7 w-7 text-red-500" />
          </Button>
          
          <Button
            size="lg"
            variant="outline"
            className="rounded-full h-12 w-12 border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50"
            onClick={handleSuperLike}
          >
            <Star className="h-5 w-5 text-blue-500" />
          </Button>
          
          <Button
            size="lg"
            className="rounded-full h-16 w-16 bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-600 hover:to-pink-600 shadow-lg"
            onClick={handleLike}
          >
            <Heart className="h-8 w-8 text-white" />
          </Button>
          
          <Button
            size="lg"
            variant="outline"
            className="rounded-full h-12 w-12 border-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50"
            onClick={() => navigate('/buy-credits')}
          >
            <Zap className="h-5 w-5 text-purple-500" />
          </Button>
          
          <Button
            size="lg"
            variant="outline"
            className="rounded-full h-14 w-14 border-2 border-green-200 hover:border-green-400 hover:bg-green-50"
            onClick={handleMessage}
          >
            <MessageSquare className="h-7 w-7 text-green-500" />
          </Button>
        </div>

        {/* Progress */}
        <div className="flex justify-center items-center gap-2 mt-6">
          {profiles.map((_, i) => (
            <div 
              key={i} 
              className={`h-1 rounded-full transition-all ${
                i === currentIndex 
                  ? 'w-8 bg-gradient-to-r from-amber-500 to-pink-500' 
                  : i < currentIndex 
                    ? 'w-4 bg-gray-300' 
                    : 'w-4 bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>
    </MainLayout>
  );
};

export default Discovery;
