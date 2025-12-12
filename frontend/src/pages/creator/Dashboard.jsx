import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { useAuth } from '@/context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { 
  Plus, Image, Video, DollarSign, Users, TrendingUp, Eye,
  Heart, MessageSquare, BarChart3, Calendar, Upload, X,
  Camera, Sparkles, ArrowUp, ArrowDown, Clock, Send
} from 'lucide-react';
import { toast } from 'sonner';

const CreatorDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [createPostOpen, setCreatePostOpen] = useState(false);
  const [newPost, setNewPost] = useState({ content: '', media: null });
  const [isPosting, setIsPosting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Mock stats
  const stats = [
    { label: 'Total Earnings', value: '$2,450', change: '+12%', up: true, icon: DollarSign, color: 'emerald' },
    { label: 'Followers', value: '12.5K', change: '+8%', up: true, icon: Users, color: 'violet' },
    { label: 'Post Views', value: '45.2K', change: '+24%', up: true, icon: Eye, color: 'blue' },
    { label: 'Engagement', value: '8.4%', change: '-2%', up: false, icon: Heart, color: 'pink' },
  ];

  // Mock recent posts
  const recentPosts = [
    { id: 1, image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop', likes: 234, comments: 45, views: 1200, date: '2 hours ago' },
    { id: 2, image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&h=200&fit=crop', likes: 567, comments: 89, views: 3400, date: '1 day ago' },
    { id: 3, image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200&h=200&fit=crop', likes: 890, comments: 120, views: 5600, date: '2 days ago' },
  ];

  // Mock earnings data
  const earningsData = [
    { label: 'Tips', amount: '$1,200', percentage: 49 },
    { label: 'Subscriptions', amount: '$850', percentage: 35 },
    { label: 'Messages', amount: '$400', percentage: 16 },
  ];

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      const type = file.type.startsWith('video/') ? 'video' : 'image';
      setNewPost({ ...newPost, media: { type, url, file } });
    }
  };

  const handleCreatePost = async () => {
    if (!newPost.content.trim() && !newPost.media) {
      toast.error('Please add content or media');
      return;
    }
    
    setIsPosting(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
    
    setTimeout(() => {
      clearInterval(interval);
      setUploadProgress(100);
      toast.success('Post published successfully!');
      setNewPost({ content: '', media: null });
      setCreatePostOpen(false);
      setIsPosting(false);
      setUploadProgress(0);
    }, 2500);
  };

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto space-y-6 pb-20 md:pb-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Creator Dashboard</h1>
            <p className="text-slate-600 mt-1">Welcome back, {user?.name || 'Creator'}!</p>
          </div>
          
          {/* Create Post Button */}
          <Dialog open={createPostOpen} onOpenChange={setCreatePostOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700 rounded-full shadow-lg shadow-fuchsia-500/25">
                <Plus className="h-5 w-5 mr-2" />
                Create New Post
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 text-slate-900">
                  <Camera className="h-5 w-5 text-fuchsia-600" />
                  Create New Post
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <Textarea
                  placeholder="What's on your mind? Share with your fans..."
                  value={newPost.content}
                  onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                  className="min-h-32 resize-none border-slate-300"
                />
                
                {newPost.media ? (
                  <div className="relative rounded-lg overflow-hidden">
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
                ) : (
                  <div 
                    className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:border-fuchsia-400 hover:bg-fuchsia-50 transition"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="h-10 w-10 text-slate-400 mx-auto mb-3" />
                    <p className="text-slate-600 font-medium">Click to upload media</p>
                    <p className="text-sm text-slate-400 mt-1">JPG, PNG, GIF, MP4 up to 100MB</p>
                  </div>
                )}
                
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept="image/*,video/*"
                  className="hidden"
                />
                
                {isPosting && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Uploading...</span>
                      <span className="text-fuchsia-600 font-medium">{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </div>
                )}
                
                <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => fileInputRef.current?.click()}
                      className="border-slate-300"
                    >
                      <Image className="h-4 w-4 mr-1" />
                      Photo
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => fileInputRef.current?.click()}
                      className="border-slate-300"
                    >
                      <Video className="h-4 w-4 mr-1" />
                      Video
                    </Button>
                  </div>
                  <Button
                    onClick={handleCreatePost}
                    disabled={isPosting || (!newPost.content.trim() && !newPost.media)}
                    className="bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700"
                  >
                    {isPosting ? 'Publishing...' : 'Publish'}
                    <Send className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="border-slate-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`w-12 h-12 rounded-xl bg-${stat.color}-100 flex items-center justify-center`}>
                      <Icon className={`h-6 w-6 text-${stat.color}-600`} />
                    </div>
                    <Badge 
                      variant="outline" 
                      className={stat.up ? 'text-emerald-600 border-emerald-200 bg-emerald-50' : 'text-red-600 border-red-200 bg-red-50'}
                    >
                      {stat.up ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
                      {stat.change}
                    </Badge>
                  </div>
                  <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
                  <p className="text-sm text-slate-500">{stat.label}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Posts */}
          <Card className="lg:col-span-2 border-slate-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-slate-900">Recent Posts</CardTitle>
                <Button variant="outline" size="sm" className="rounded-full border-slate-300">
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentPosts.map((post) => (
                  <div key={post.id} className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition cursor-pointer">
                    <img 
                      src={post.image} 
                      alt="Post" 
                      className="w-16 h-16 rounded-lg object-cover"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-4 text-sm">
                        <span className="flex items-center gap-1 text-slate-600">
                          <Heart className="h-4 w-4 text-pink-500" />
                          {post.likes}
                        </span>
                        <span className="flex items-center gap-1 text-slate-600">
                          <MessageSquare className="h-4 w-4 text-blue-500" />
                          {post.comments}
                        </span>
                        <span className="flex items-center gap-1 text-slate-600">
                          <Eye className="h-4 w-4 text-violet-500" />
                          {post.views}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-1 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {post.date}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Earnings Breakdown */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Earnings Breakdown</CardTitle>
              <CardDescription>This month's revenue sources</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {earningsData.map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">{item.label}</span>
                      <span className="font-semibold text-slate-900">{item.amount}</span>
                    </div>
                    <Progress value={item.percentage} className="h-2" />
                  </div>
                ))}
              </div>
              
              <div className="mt-6 pt-4 border-t border-slate-200">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Total This Month</span>
                  <span className="text-2xl font-bold text-emerald-600">$2,450</span>
                </div>
              </div>
              
              <Button 
                className="w-full mt-4 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
                onClick={() => navigate('/creator/payouts')}
              >
                Request Payout
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button 
                variant="outline" 
                className="h-auto py-6 flex-col gap-2 border-slate-300 hover:border-violet-400 hover:bg-violet-50"
                onClick={() => setCreatePostOpen(true)}
              >
                <Camera className="h-6 w-6 text-violet-600" />
                <span>New Post</span>
              </Button>
              <Button 
                variant="outline" 
                className="h-auto py-6 flex-col gap-2 border-slate-300 hover:border-fuchsia-400 hover:bg-fuchsia-50"
                onClick={() => navigate('/creator/earnings')}
              >
                <BarChart3 className="h-6 w-6 text-fuchsia-600" />
                <span>Analytics</span>
              </Button>
              <Button 
                variant="outline" 
                className="h-auto py-6 flex-col gap-2 border-slate-300 hover:border-emerald-400 hover:bg-emerald-50"
                onClick={() => navigate('/creator/payouts')}
              >
                <DollarSign className="h-6 w-6 text-emerald-600" />
                <span>Payouts</span>
              </Button>
              <Button 
                variant="outline" 
                className="h-auto py-6 flex-col gap-2 border-slate-300 hover:border-blue-400 hover:bg-blue-50"
                onClick={() => navigate('/messages')}
              >
                <MessageSquare className="h-6 w-6 text-blue-600" />
                <span>Messages</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default CreatorDashboard;
