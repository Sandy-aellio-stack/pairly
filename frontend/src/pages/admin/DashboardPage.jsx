import { useState, useEffect } from 'react';
import { Users, UserPlus, Activity, AlertTriangle, TrendingUp, TrendingDown, ArrowRight, MessageCircle, Heart, Coins } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalUsers: 12458,
    newUsers: 234,
    activeUsers: 8956,
    reportsPending: 23,
  });

  const [recentActivity, setRecentActivity] = useState([
    { id: 1, type: 'signup', user: 'Priya Sharma', time: '2 mins ago', avatar: 'P' },
    { id: 2, type: 'report', user: 'Rahul K.', time: '5 mins ago', avatar: 'R' },
    { id: 3, type: 'signup', user: 'Ananya M.', time: '10 mins ago', avatar: 'A' },
    { id: 4, type: 'verified', user: 'Arjun P.', time: '15 mins ago', avatar: 'A' },
    { id: 5, type: 'signup', user: 'Sneha D.', time: '20 mins ago', avatar: 'S' },
  ]);

  const statCards = [
    { label: 'Total Users', value: stats.totalUsers.toLocaleString(), icon: Users, change: '+12%', positive: true, color: 'bg-[#E9D5FF]' },
    { label: 'New Users (Today)', value: stats.newUsers.toLocaleString(), icon: UserPlus, change: '+8%', positive: true, color: 'bg-[#DBEAFE]' },
    { label: 'Active Users', value: stats.activeUsers.toLocaleString(), icon: Activity, change: '+5%', positive: true, color: 'bg-[#D1FAE5]' },
    { label: 'Reports Pending', value: stats.reportsPending.toLocaleString(), icon: AlertTriangle, change: '-3%', positive: false, color: 'bg-[#FCE7F3]' },
  ];

  const quickActions = [
    { label: 'Review Reports', description: 'Check pending moderation', onClick: () => navigate('/admin/moderation'), icon: AlertTriangle },
    { label: 'View Analytics', description: 'See growth trends', onClick: () => navigate('/admin/analytics'), icon: TrendingUp },
    { label: 'Manage Users', description: 'Search & edit users', onClick: () => navigate('/admin/users'), icon: Users },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Welcome back, Admin</h1>
        <p className="text-gray-600">Here&apos;s what&apos;s happening with TrueBond today.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, index) => (
          <div key={index} className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center`}>
                <stat.icon size={24} className="text-[#0F172A]" />
              </div>
              <div className={`flex items-center gap-1 text-sm font-medium ${
                stat.positive ? 'text-green-600' : 'text-red-500'
              }`}>
                {stat.positive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {stat.change}
              </div>
            </div>
            <p className="text-3xl font-bold text-[#0F172A] mb-1">{stat.value}</p>
            <p className="text-gray-500 text-sm">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-[#0F172A]">Recent Activity</h3>
            <button className="text-sm text-[#0F172A] hover:underline">View All</button>
          </div>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-xl transition-colors">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                  activity.type === 'signup' ? 'bg-[#E9D5FF] text-[#0F172A]' :
                  activity.type === 'report' ? 'bg-[#FCE7F3] text-rose-600' :
                  'bg-[#D1FAE5] text-green-600'
                }`}>
                  {activity.avatar}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-[#0F172A]">
                    {activity.type === 'signup' && 'New user signed up'}
                    {activity.type === 'report' && 'User reported content'}
                    {activity.type === 'verified' && 'Profile verified'}
                  </p>
                  <p className="text-sm text-gray-500">{activity.user}</p>
                </div>
                <span className="text-xs text-gray-400">{activity.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">Quick Actions</h3>
          <div className="space-y-4">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={action.onClick}
                className="w-full flex items-center gap-4 p-4 bg-gray-50 hover:bg-[#E9D5FF]/30 rounded-xl transition-colors text-left"
              >
                <div className="w-10 h-10 bg-[#E9D5FF] rounded-xl flex items-center justify-center">
                  <action.icon size={20} className="text-[#0F172A]" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-[#0F172A]">{action.label}</p>
                  <p className="text-sm text-gray-500">{action.description}</p>
                </div>
                <ArrowRight size={18} className="text-gray-400" />
              </button>
            ))}
          </div>

          {/* Platform Stats */}
          <div className="mt-6 pt-6 border-t border-gray-100">
            <h4 className="font-medium text-[#0F172A] mb-4">Today&apos;s Highlights</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 flex items-center gap-2"><MessageCircle size={16} /> Messages Sent</span>
                <span className="font-semibold text-[#0F172A]">4,521</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 flex items-center gap-2"><Heart size={16} /> New Matches</span>
                <span className="font-semibold text-[#0F172A]">892</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 flex items-center gap-2"><Coins size={16} /> Coins Purchased</span>
                <span className="font-semibold text-[#0F172A]">₹45,230</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
