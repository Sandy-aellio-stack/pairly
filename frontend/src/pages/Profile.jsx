import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { useAuth } from '@/context/AuthContext';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  MapPin, MessageSquare, Calendar, Heart, Settings, Edit,
  Grid, Bookmark, Camera, Sparkles, Users, Crown, Share2,
  MoreHorizontal, Link as LinkIcon, Instagram, Twitter
} from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';

const Profile = () => {
  const { userId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isOwnProfile, setIsOwnProfile] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');

  // Mock posts data
  const [posts] = useState([
    { id: 1, image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop', likes: 234 },
    { id: 2, image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=300&h=300&fit=crop', likes: 567 },
    { id: 3, image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&h=300&fit=crop', likes: 123 },
    { id: 4, image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=300&h=300&fit=crop', likes: 890 },
    { id: 5, image: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=300&h=300&fit=crop', likes: 456 },
    { id: 6, image: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=300&h=300&fit=crop', likes: 321 },
  ]);

  useEffect(() => {
    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    try {
      // Check if viewing own profile
      if (userId === user?.id || userId === 'me') {
        setIsOwnProfile(true);
        setProfile({
          id: user?.id,
          display_name: user?.name || 'Your Name',
          email: user?.email,
          bio: user?.bio || 'Add a bio to tell people about yourself',
          age: user?.age || 25,
          role: user?.role || 'fan',
          profile_picture_url: user?.profile_picture_url || 'https://i.pravatar.cc/200?img=1',
          is_online: true,
          followers: 1234,
          following: 567,
          posts_count: posts.length,
          is_verified: true,
          created_at: new Date().toISOString(),
          location: 'New York, NY',
        });
      } else {
        const response = await api.get(`/profiles/${userId}`);
        setProfile(response.data);
        setIsOwnProfile(user?.id === response.data.user_id);
      }
    } catch (error) {
      // Use mock data on error
      setProfile({
        id: userId,
        display_name: 'Sample User',
        bio: 'This is a sample profile',
        age: 25,
        role: 'creator',
        profile_picture_url: 'https://i.pravatar.cc/200?img=5',
        is_online: true,
        followers: 2345,
        following: 890,
        posts_count: 45,
        is_verified: true,
        created_at: new Date().toISOString(),
        location: 'Los Angeles, CA',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center mx-auto mb-4 animate-pulse">
              <Heart className="h-8 w-8 text-white" />
            </div>
            <p className="text-slate-600">Loading profile...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (!profile) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-96 space-y-4">
          <p className="text-slate-600">Profile not found</p>
          <Button onClick={() => navigate('/home')} className="rounded-full">Go Home</Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto pb-20 md:pb-8">
        {/* Profile Header */}
        <Card className="overflow-hidden border-slate-200">
          {/* Cover Photo */}
          <div className="h-48 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 relative">
            {isOwnProfile && (
              <Button 
                size="icon" 
                variant="secondary" 
                className="absolute top-4 right-4 rounded-full bg-white/20 hover:bg-white/30"
              >
                <Camera className="h-4 w-4 text-white" />
              </Button>
            )}
          </div>
          
          <CardContent className="relative pt-0 pb-6 px-6">
            {/* Avatar */}
            <div className="flex flex-col md:flex-row md:items-end gap-4 -mt-16 md:-mt-12">
              <div className="relative">
                <Avatar className="h-32 w-32 border-4 border-white shadow-lg">
                  <AvatarImage src={profile.profile_picture_url} />
                  <AvatarFallback className="text-4xl bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white">
                    {profile.display_name?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                {profile.is_online && (
                  <div className="absolute bottom-2 right-2 w-5 h-5 bg-emerald-500 rounded-full border-3 border-white" />
                )}
                {isOwnProfile && (
                  <Button 
                    size="icon" 
                    className="absolute bottom-0 right-0 h-8 w-8 rounded-full bg-violet-600 hover:bg-violet-700"
                  >
                    <Camera className="h-4 w-4" />
                  </Button>
                )}
              </div>
              
              {/* Profile Info */}
              <div className="flex-1 md:pb-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h1 className="text-2xl font-bold text-slate-900">{profile.display_name}</h1>
                      {profile.is_verified && (
                        <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                        </svg>
                      )}
                      {profile.role === 'creator' && (
                        <Badge className="bg-gradient-to-r from-fuchsia-500 to-pink-500">
                          <Sparkles className="h-3 w-3 mr-1" />
                          Creator
                        </Badge>
                      )}
                    </div>
                    {profile.location && (
                      <div className="flex items-center text-slate-500 text-sm mt-1">
                        <MapPin className="h-4 w-4 mr-1" />
                        {profile.location}
                      </div>
                    )}
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    {isOwnProfile ? (
                      <>
                        <Button 
                          variant="outline" 
                          className="rounded-full border-slate-300"
                          onClick={() => navigate('/profile/edit')}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit Profile
                        </Button>
                        <Button 
                          variant="outline" 
                          size="icon"
                          className="rounded-full border-slate-300"
                          onClick={() => navigate('/settings')}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button className="rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700">
                          <Users className="h-4 w-4 mr-2" />
                          Follow
                        </Button>
                        <Button 
                          variant="outline" 
                          className="rounded-full border-slate-300"
                          onClick={() => navigate(`/messages/${userId}`)}
                        >
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Message
                        </Button>
                        <Button variant="outline" size="icon" className="rounded-full border-slate-300">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Stats */}
            <div className="flex gap-6 mt-6 pt-4 border-t border-slate-200">
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{profile.posts_count || 0}</p>
                <p className="text-sm text-slate-500">Posts</p>
              </div>
              <div className="text-center cursor-pointer hover:text-violet-600">
                <p className="text-2xl font-bold text-slate-900">{profile.followers?.toLocaleString() || 0}</p>
                <p className="text-sm text-slate-500">Followers</p>
              </div>
              <div className="text-center cursor-pointer hover:text-violet-600">
                <p className="text-2xl font-bold text-slate-900">{profile.following?.toLocaleString() || 0}</p>
                <p className="text-sm text-slate-500">Following</p>
              </div>
            </div>
            
            {/* Bio */}
            {profile.bio && (
              <p className="mt-4 text-slate-700">{profile.bio}</p>
            )}
            
            {/* Social Links */}
            <div className="flex gap-3 mt-4">
              <Button variant="outline" size="sm" className="rounded-full border-slate-300">
                <Instagram className="h-4 w-4 mr-1" />
                Instagram
              </Button>
              <Button variant="outline" size="sm" className="rounded-full border-slate-300">
                <Twitter className="h-4 w-4 mr-1" />
                Twitter
              </Button>
              <Button variant="outline" size="sm" className="rounded-full border-slate-300">
                <LinkIcon className="h-4 w-4 mr-1" />
                Website
              </Button>
            </div>
          </CardContent>
        </Card>
        
        {/* Content Tabs */}
        <Tabs defaultValue="posts" className="mt-6">
          <TabsList className="w-full justify-start bg-transparent border-b border-slate-200 rounded-none p-0">
            <TabsTrigger 
              value="posts" 
              className="data-[state=active]:border-b-2 data-[state=active]:border-violet-600 data-[state=active]:text-violet-600 rounded-none"
            >
              <Grid className="h-4 w-4 mr-2" />
              Posts
            </TabsTrigger>
            <TabsTrigger 
              value="saved" 
              className="data-[state=active]:border-b-2 data-[state=active]:border-violet-600 data-[state=active]:text-violet-600 rounded-none"
            >
              <Bookmark className="h-4 w-4 mr-2" />
              Saved
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="posts" className="mt-6">
            <div className="grid grid-cols-3 gap-1 md:gap-4">
              {posts.map((post) => (
                <div key={post.id} className="aspect-square relative group cursor-pointer overflow-hidden rounded-lg">
                  <img 
                    src={post.image} 
                    alt="Post"
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-slate-900/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="flex items-center gap-1 text-white">
                      <Heart className="h-5 w-5 fill-white" />
                      <span className="font-semibold">{post.likes}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="saved" className="mt-6">
            <div className="text-center py-12">
              <Bookmark className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No saved posts yet</p>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
};

export default Profile;
