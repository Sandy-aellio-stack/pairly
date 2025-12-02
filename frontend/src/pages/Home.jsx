import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, MessageSquare, Heart, TrendingUp } from 'lucide-react';
import api from '@/services/api';

const Home = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalProfiles: 0,
    activeConversations: 0,
    creditsBalance: 0,
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [profilesRes, conversationsRes] = await Promise.all([
        api.get('/discover?limit=1'),
        api.get('/messages/conversations'),
      ]);

      setStats({
        totalProfiles: 100, // Mock data
        activeConversations: conversationsRes.data.length,
        creditsBalance: user?.credits_balance || 0,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-pink-500 to-purple-600 rounded-lg p-8 text-white">
          <h1 className="text-4xl font-bold mb-2">Welcome back, {user?.name}!</h1>
          <p className="text-lg opacity-90">Ready to make meaningful connections?</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Profiles</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalProfiles}+</div>
              <p className="text-xs text-muted-foreground">Creators available</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversations</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeConversations}</div>
              <p className="text-xs text-muted-foreground">Active chats</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Credits</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.creditsBalance}</div>
              <p className="text-xs text-muted-foreground">Available balance</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="pt-6">
              <Heart className="h-12 w-12 text-pink-500 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Discover Creators</h3>
              <p className="text-gray-600 mb-4">Browse and connect with amazing creators</p>
              <Link to="/discovery">
                <Button className="w-full">Start Exploring</Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="pt-6">
              <MessageSquare className="h-12 w-12 text-blue-500 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Messages</h3>
              <p className="text-gray-600 mb-4">Continue your conversations</p>
              <Link to="/messages">
                <Button variant="outline" className="w-full">
                  View Messages
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Creator-specific Section */}
        {user?.role === 'creator' && (
          <Card className="bg-gradient-to-r from-yellow-50 to-orange-50">
            <CardContent className="pt-6">
              <h3 className="text-xl font-semibold mb-2">Creator Dashboard</h3>
              <p className="text-gray-600 mb-4">Manage your earnings and view analytics</p>
              <Link to="/creator/dashboard">
                <Button>Go to Dashboard</Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export default Home;