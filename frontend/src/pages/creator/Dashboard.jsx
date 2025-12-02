import React, { useEffect, useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DollarSign, Users, MessageSquare, TrendingUp } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import api from '@/services/api';

const CreatorDashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalEarnings: 0,
    creditsBalance: 0,
    messagesSent: 0,
    profileViews: 0,
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [creditsRes, profileRes] = await Promise.all([
        api.get('/credits/balance'),
        api.get(`/profiles/${user.id}`),
      ]);

      setStats({
        totalEarnings: profileRes.data.total_earnings || 0,
        creditsBalance: creditsRes.data.credits_balance || 0,
        messagesSent: 0, // Mock data
        profileViews: profileRes.data.view_count || 0,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Creator Dashboard</h1>
          <p className="text-gray-600">Track your performance and earnings</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Earnings</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalEarnings} credits</div>
              <p className="text-xs text-muted-foreground">${(stats.totalEarnings / 100).toFixed(2)} USD</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Credits Balance</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.creditsBalance}</div>
              <p className="text-xs text-muted-foreground">Available for payout</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Profile Views</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.profileViews}</div>
              <p className="text-xs text-muted-foreground">Total views</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Messages</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.messagesSent}</div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500 text-sm">No recent activity</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Earnings This Month</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">+{stats.creditsBalance}</div>
              <p className="text-sm text-gray-500 mt-1">Credits earned</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
};

export default CreatorDashboard;