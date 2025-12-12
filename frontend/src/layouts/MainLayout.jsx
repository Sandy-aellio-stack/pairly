import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Home, Search, MessageSquare, Settings, DollarSign, BarChart3, 
  Shield, Heart, Bell, Globe, Camera, User, LogOut, Crown,
  Menu, X, Sparkles, Plus, Image, Video, Send
} from 'lucide-react';

const MainLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [createPostOpen, setCreatePostOpen] = useState(false);
  const [newPost, setNewPost] = useState({ content: '', media: null });
  const [isPosting, setIsPosting] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: '/home', label: 'Home', icon: Home },
    { path: '/discovery', label: 'Discover', icon: Search },
    { path: '/map', label: 'Map', icon: Globe },
    { path: '/messages', label: 'Messages', icon: MessageSquare },
  ];

  const handleCreatePost = async () => {
    if (!newPost.content.trim()) {
      toast.error('Please add some content');
      return;
    }
    setIsPosting(true);
    // Simulate API call
    setTimeout(() => {
      toast.success('Post created successfully!');
      setNewPost({ content: '', media: null });
      setCreatePostOpen(false);
      setIsPosting(false);
    }, 1000);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      const type = file.type.startsWith('video/') ? 'video' : 'image';
      setNewPost({ ...newPost, media: { type, url, file } });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-md border-b border-slate-200 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo & Desktop Nav */}
            <div className="flex items-center space-x-8">
              <Link to="/home" className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                  <Heart className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent hidden sm:block">
                  Pairly
                </span>
              </Link>
              
              {/* Desktop Navigation */}
              <div className="hidden md:flex space-x-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                        isActive(item.path)
                          ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
                
                {/* Creator Dashboard */}
                {user?.role === 'creator' && (
                  <Link
                    to="/creator/dashboard"
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      location.pathname.startsWith('/creator')
                        ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <BarChart3 className="h-4 w-4" />
                    <span>Dashboard</span>
                  </Link>
                )}
                
                {/* Admin */}
                {user?.role === 'admin' && (
                  <Link
                    to="/admin"
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      location.pathname.startsWith('/admin')
                        ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Shield className="h-4 w-4" />
                    <span>Admin</span>
                  </Link>
                )}
              </div>
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-3">
              {/* Credits */}
              <Link to="/buy-credits">
                <Button variant="outline" size="sm" className="rounded-full gap-2 hidden sm:flex border-slate-300">
                  <DollarSign className="h-4 w-4 text-violet-600" />
                  <span className="font-semibold text-slate-700">{user?.credits_balance || 0}</span>
                </Button>
              </Link>

              {/* Notifications */}
              <Button variant="ghost" size="icon" className="relative rounded-full">
                <Bell className="h-5 w-5 text-slate-600" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-fuchsia-500 rounded-full text-xs text-white flex items-center justify-center">
                  3
                </span>
              </Button>

              {/* Creator Create/Upload Button */}
              {user?.role === 'creator' && (
                <Dialog open={createPostOpen} onOpenChange={setCreatePostOpen}>
                  <DialogTrigger asChild>
                    <Button 
                      className="rounded-full bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700 shadow-lg shadow-fuchsia-500/25 gap-2"
                    >
                      <Plus className="h-5 w-5" />
                      <span className="hidden sm:inline">Create</span>
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
                        placeholder="Share something with your fans..."
                        value={newPost.content}
                        onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                        className="min-h-32 resize-none border-slate-300"
                      />
                      {newPost.media && (
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
                      )}
                      <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                        <div className="flex gap-2">
                          <input
                            type="file"
                            id="media-upload"
                            onChange={handleFileSelect}
                            accept="image/*,video/*"
                            className="hidden"
                          />
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => document.getElementById('media-upload').click()}
                            className="border-slate-300"
                          >
                            <Image className="h-4 w-4 mr-1" />
                            Photo
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => document.getElementById('media-upload').click()}
                            className="border-slate-300"
                          >
                            <Video className="h-4 w-4 mr-1" />
                            Video
                          </Button>
                        </div>
                        <Button
                          onClick={handleCreatePost}
                          disabled={isPosting || !newPost.content.trim()}
                          className="bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700"
                        >
                          {isPosting ? 'Posting...' : 'Post'}
                          <Send className="h-4 w-4 ml-2" />
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              )}

              {/* Profile Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative rounded-full p-0">
                    <Avatar className="h-9 w-9 border-2 border-violet-200">
                      <AvatarImage src={user?.profile_picture_url || 'https://i.pravatar.cc/100?img=1'} />
                      <AvatarFallback className="bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white">
                        {user?.name?.charAt(0).toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    {user?.role === 'creator' && (
                      <span className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gradient-to-r from-fuchsia-500 to-pink-500 rounded-full flex items-center justify-center">
                        <Sparkles className="h-2.5 w-2.5 text-white" />
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-3 py-2">
                    <p className="font-semibold text-slate-900">{user?.name || 'User'}</p>
                    <p className="text-sm text-slate-500">{user?.email}</p>
                    {user?.role === 'creator' && (
                      <Badge className="mt-1 bg-gradient-to-r from-fuchsia-500 to-pink-500 text-xs">
                        <Sparkles className="h-3 w-3 mr-1" />
                        Creator
                      </Badge>
                    )}
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate(`/profile/${user?.id}`)} className="cursor-pointer">
                    <User className="h-4 w-4 mr-2" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/settings')} className="cursor-pointer">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/buy-credits')} className="cursor-pointer">
                    <Crown className="h-4 w-4 mr-2" />
                    Upgrade Plan
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer">
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Mobile Menu Button */}
              <Button 
                variant="ghost" 
                size="icon" 
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-slate-200">
            <div className="px-4 py-3 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium ${
                      isActive(item.path)
                        ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
              {user?.role === 'creator' && (
                <Link
                  to="/creator/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium ${
                    location.pathname.startsWith('/creator')
                      ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <BarChart3 className="h-5 w-5" />
                  <span>Creator Dashboard</span>
                </Link>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50">
        <div className="flex justify-around py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center py-2 px-4 ${
                  isActive(item.path)
                    ? 'text-fuchsia-600'
                    : 'text-slate-500'
                }`}
              >
                <Icon className={`h-6 w-6 ${isActive(item.path) ? 'fill-current' : ''}`} />
                <span className="text-xs mt-1">{item.label}</span>
              </Link>
            );
          })}
          {/* Creator Mobile Create Button */}
          {user?.role === 'creator' ? (
            <button
              onClick={() => setCreatePostOpen(true)}
              className="flex flex-col items-center py-2 px-4 text-fuchsia-600"
            >
              <div className="w-10 h-10 -mt-5 rounded-full bg-gradient-to-r from-fuchsia-600 to-pink-600 flex items-center justify-center shadow-lg">
                <Plus className="h-6 w-6 text-white" />
              </div>
              <span className="text-xs mt-1">Create</span>
            </button>
          ) : (
            <Link
              to={`/profile/${user?.id}`}
              className={`flex flex-col items-center py-2 px-4 ${
                location.pathname.includes('/profile')
                  ? 'text-fuchsia-600'
                  : 'text-slate-500'
              }`}
            >
              <User className="h-6 w-6" />
              <span className="text-xs mt-1">Profile</span>
            </Link>
          )}
        </div>
      </nav>
    </div>
  );
};

export default MainLayout;
