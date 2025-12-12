import React, { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  Heart, MessageSquare, Share2, Bookmark, MoreHorizontal,
  Plus, Image, Video, MapPin, TrendingUp, Users, Sparkles,
  Globe, Camera, X, Send, Play
} from 'lucide-react';
import api from '@/services/api';

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [stories, setStories] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newPost, setNewPost] = useState({ content: '', media: null });
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  // Mock data for demonstration
  useEffect(() => {
    // Mock stories
    setStories([
      { id: 1, name: 'Your Story', image: user?.avatar || 'https://i.pravatar.cc/100?img=1', isOwn: true, hasNew: false },
      { id: 2, name: 'Emma', image: 'https://i.pravatar.cc/100?img=5', hasNew: true },
      { id: 3, name: 'Jake', image: 'https://i.pravatar.cc/100?img=8', hasNew: true },
      { id: 4, name: 'Sophia', image: 'https://i.pravatar.cc/100?img=9', hasNew: true },
      { id: 5, name: 'Lucas', image: 'https://i.pravatar.cc/100?img=12', hasNew: false },
      { id: 6, name: 'Mia', image: 'https://i.pravatar.cc/100?img=16', hasNew: true },
    ]);

    // Mock posts
    setPosts([
      {
        id: 1,
        author: { name: 'Sarah Johnson', username: 'sarahj', avatar: 'https://i.pravatar.cc/100?img=5', isCreator: true, verified: true },
        content: 'Just had the most amazing sunset walk! 🌅 Life is beautiful when you take time to appreciate the little things.',
        media: { type: 'image', url: 'https://images.unsplash.com/photo-1507400492013-162706c8c05e?w=600&h=400&fit=crop' },
        likes: 234,
        comments: 45,
        timestamp: '2h ago',
        liked: false,
        saved: false,
      },
      {
        id: 2,
        author: { name: 'Mike Chen', username: 'mikechen', avatar: 'https://i.pravatar.cc/100?img=8', isCreator: true, verified: true },
        content: 'New content dropping tomorrow! 🔥 Who\'s excited?',
        media: { type: 'image', url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&h=400&fit=crop' },
        likes: 567,
        comments: 89,
        timestamp: '4h ago',
        liked: true,
        saved: false,
      },
      {
        id: 3,
        author: { name: 'Alex Rivera', username: 'alexr', avatar: 'https://i.pravatar.cc/100?img=12', isCreator: false, verified: false },
        content: 'Coffee and good vibes ☕️ Anyone else working from their favorite café today?',
        media: { type: 'image', url: 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=400&fit=crop' },
        likes: 123,
        comments: 28,
        timestamp: '6h ago',
        liked: false,
        saved: true,
      },
    ]);
  }, [user]);

  const handleLike = (postId) => {
    setPosts(posts.map(post => 
      post.id === postId 
        ? { ...post, liked: !post.liked, likes: post.liked ? post.likes - 1 : post.likes + 1 }
        : post
    ));
  };

  const handleSave = (postId) => {
    setPosts(posts.map(post => 
      post.id === postId 
        ? { ...post, saved: !post.saved }
        : post
    ));
  };

  const handleCreatePost = async () => {
    if (!newPost.content.trim()) {
      toast.error('Please add some content');
      return;
    }
    
    setLoading(true);
    try {
      // Mock post creation
      const newPostData = {
        id: Date.now(),
        author: { name: user?.name || 'You', username: user?.email?.split('@')[0] || 'user', avatar: 'https://i.pravatar.cc/100?img=1', isCreator: user?.role === 'creator', verified: false },
        content: newPost.content,
        media: newPost.media,
        likes: 0,
        comments: 0,
        timestamp: 'Just now',
        liked: false,
        saved: false,
      };
      setPosts([newPostData, ...posts]);
      setNewPost({ content: '', media: null });
      setIsCreateOpen(false);
      toast.success('Post created!');
    } catch (error) {
      toast.error('Failed to create post');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      const type = file.type.startsWith('video/') ? 'video' : 'image';
      setNewPost({ ...newPost, media: { type, url } });
    }
  };

  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Stories Section */}
        <Card className="overflow-hidden">
          <CardContent className="p-4">
            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
              {stories.map((story) => (
                <div key={story.id} className="flex flex-col items-center gap-1 flex-shrink-0 cursor-pointer">
                  <div className={`relative p-0.5 rounded-full ${story.hasNew ? 'bg-gradient-to-br from-amber-500 via-pink-500 to-purple-500' : story.isOwn ? 'bg-gray-200' : 'bg-gray-300'}`}>
                    <div className="bg-white p-0.5 rounded-full">
                      <Avatar className="h-16 w-16">
                        <AvatarImage src={story.image} />
                        <AvatarFallback>{story.name[0]}</AvatarFallback>
                      </Avatar>
                    </div>
                    {story.isOwn && (
                      <div className="absolute bottom-0 right-0 bg-gradient-to-r from-amber-500 to-pink-500 rounded-full p-1">
                        <Plus className="h-3 w-3 text-white" />
                      </div>
                    )}
                  </div>
                  <span className="text-xs font-medium truncate w-16 text-center">{story.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Create Post (Creators Only) */}
        {user?.role === 'creator' && (
          <Card className="bg-gradient-to-r from-amber-50 to-pink-50">
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <Avatar>
                  <AvatarImage src="https://i.pravatar.cc/100?img=1" />
                  <AvatarFallback>{user?.name?.[0] || 'U'}</AvatarFallback>
                </Avatar>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="flex-1 justify-start text-gray-500 rounded-full">
                      What's on your mind?
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                      <DialogTitle>Create Post</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Textarea
                        placeholder="Share something with your fans..."
                        value={newPost.content}
                        onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                        className="min-h-32 resize-none"
                      />
                      {newPost.media && (
                        <div className="relative">
                          {newPost.media.type === 'image' ? (
                            <img src={newPost.media.url} alt="Preview" className="w-full rounded-lg" />
                          ) : (
                            <video src={newPost.media.url} controls className="w-full rounded-lg" />
                          )}
                          <Button
                            variant="destructive"
                            size="icon"
                            className="absolute top-2 right-2 h-8 w-8 rounded-full"
                            onClick={() => setNewPost({ ...newPost, media: null })}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            accept="image/*,video/*"
                            className="hidden"
                          />
                          <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()}>
                            <Image className="h-5 w-5 mr-1" />
                            Photo
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()}>
                            <Video className="h-5 w-5 mr-1" />
                            Video
                          </Button>
                        </div>
                        <Button
                          onClick={handleCreatePost}
                          disabled={loading || !newPost.content.trim()}
                          className="bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-600 hover:to-pink-600"
                        >
                          {loading ? 'Posting...' : 'Post'}
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                  <DialogTrigger asChild>
                    <Button size="icon" className="bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-600 hover:to-pink-600 rounded-full">
                      <Camera className="h-5 w-5" />
                    </Button>
                  </DialogTrigger>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <div className="flex gap-3">
          <Button
            variant="outline"
            className="flex-1 rounded-full"
            onClick={() => navigate('/map')}
          >
            <Globe className="h-4 w-4 mr-2" />
            Snap Map
          </Button>
          <Button
            variant="outline"
            className="flex-1 rounded-full"
            onClick={() => navigate('/discovery')}
          >
            <Users className="h-4 w-4 mr-2" />
            Discover
          </Button>
          <Button
            variant="outline"
            className="flex-1 rounded-full"
            onClick={() => navigate('/messages')}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Messages
          </Button>
        </div>

        {/* Feed */}
        <div className="space-y-6">
          {posts.map((post) => (
            <Card key={post.id} className="overflow-hidden">
              <CardContent className="p-0">
                {/* Post Header */}
                <div className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarImage src={post.author.avatar} />
                      <AvatarFallback>{post.author.name[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-1">
                        <span className="font-semibold">{post.author.name}</span>
                        {post.author.verified && (
                          <svg className="h-4 w-4 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                          </svg>
                        )}
                        {post.author.isCreator && (
                          <Badge className="ml-1 bg-gradient-to-r from-amber-500 to-pink-500 text-xs py-0">
                            Creator
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">{post.timestamp}</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-5 w-5" />
                  </Button>
                </div>

                {/* Post Content */}
                <p className="px-4 pb-3">{post.content}</p>

                {/* Post Media */}
                {post.media && (
                  <div className="relative">
                    {post.media.type === 'image' ? (
                      <img 
                        src={post.media.url} 
                        alt="Post" 
                        className="w-full aspect-video object-cover"
                      />
                    ) : (
                      <div className="relative">
                        <video src={post.media.url} className="w-full aspect-video object-cover" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="bg-black/50 rounded-full p-4">
                            <Play className="h-8 w-8 text-white" />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Post Actions */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-4">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className={`gap-1 ${post.liked ? 'text-red-500' : ''}`}
                        onClick={() => handleLike(post.id)}
                      >
                        <Heart className={`h-5 w-5 ${post.liked ? 'fill-current' : ''}`} />
                        {post.likes}
                      </Button>
                      <Button variant="ghost" size="sm" className="gap-1">
                        <MessageSquare className="h-5 w-5" />
                        {post.comments}
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Share2 className="h-5 w-5" />
                      </Button>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleSave(post.id)}
                    >
                      <Bookmark className={`h-5 w-5 ${post.saved ? 'fill-current' : ''}`} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </MainLayout>
  );
};

export default Home;
