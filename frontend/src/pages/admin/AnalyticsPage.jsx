import { useState, useEffect } from 'react';
import { TrendingUp, Users, Calendar, Activity, Loader2 } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { adminAnalyticsAPI } from '@/services/adminApi';

const AnalyticsPage = () => {
  const [timeRange, setTimeRange] = useState('year');
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({ totalUsers: 0, activeUsers: 0, revenue: 0, dauMauRatio: 0 });
  const [userGrowthData, setUserGrowthData] = useState([]);
  const [demographics, setDemographics] = useState({ ageDistribution: [], genderDistribution: [] });
  const [revenueData, setRevenueData] = useState([]);

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [overviewRes, growthRes, demoRes, revenueRes] = await Promise.all([
        adminAnalyticsAPI.getOverview(),
        adminAnalyticsAPI.getUserGrowth(timeRange),
        adminAnalyticsAPI.getDemographics(),
        adminAnalyticsAPI.getRevenue(timeRange)
      ]);
      
      setStats({
        totalUsers: overviewRes.data.totalUsers,
        activeUsers: overviewRes.data.activeUsers,
        revenue: revenueRes.data.totalRevenue,
        dauMauRatio: Math.round((overviewRes.data.activeUsers / Math.max(overviewRes.data.totalUsers, 1)) * 100)
      });
      setUserGrowthData(growthRes.data.data);
      setDemographics(demoRes.data);
      setRevenueData(revenueRes.data.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Static DAU/MAU data for visualization
  const dauMauData = [
    { day: 'Mon', dau: 4200, mau: 8500 },
    { day: 'Tue', dau: 4500, mau: 8700 },
    { day: 'Wed', dau: 4800, mau: 8900 },
    { day: 'Thu', dau: 5100, mau: 9100 },
    { day: 'Fri', dau: 5500, mau: 9400 },
    { day: 'Sat', dau: 6200, mau: 9800 },
    { day: 'Sun', dau: 5800, mau: 9600 },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Analytics</h1>
          <p className="text-gray-600">Track growth, engagement, and demographics.</p>
        </div>
        <div className="flex gap-2">
          {['week', 'month', 'year'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-[#0F172A] text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100 shadow-sm'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#E9D5FF] rounded-xl flex items-center justify-center">
              <Users size={20} className="text-[#0F172A]" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A]">{stats.totalUsers.toLocaleString()}</p>
          <p className="text-sm text-gray-500">Total Users</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#DBEAFE] rounded-xl flex items-center justify-center">
              <Activity size={20} className="text-blue-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A]">{stats.activeUsers.toLocaleString()}</p>
          <p className="text-sm text-gray-500">Active Users (7d)</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#D1FAE5] rounded-xl flex items-center justify-center">
              <TrendingUp size={20} className="text-green-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A">₹{stats.revenue.toLocaleString()}</p>
          <p className="text-sm text-gray-500">Revenue ({timeRange})</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#FCE7F3] rounded-xl flex items-center justify-center">
              <Calendar size={20} className="text-rose-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A]">{stats.dauMauRatio}%</p>
          <p className="text-sm text-gray-500">Active/Total Ratio</p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* User Growth */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">User Growth</h3>
          {userGrowthData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={userGrowthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Area type="monotone" dataKey="users" stroke="#0F172A" fill="#E9D5FF" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No growth data available
            </div>
          )}
        </div>

        {/* DAU/MAU */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">DAU vs MAU (Sample)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dauMauData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="dau" fill="#0F172A" name="Daily Active" radius={[4, 4, 0, 0]} />
              <Bar dataKey="mau" fill="#E9D5FF" name="Monthly Active" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Age Demographics */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">Age Distribution</h3>
          {demographics.ageDistribution.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={demographics.ageDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {demographics.ageDistribution.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap justify-center gap-4 mt-4">
                {demographics.ageDistribution.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-gray-600">{item.name}: {item.value}%</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Gender Distribution */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">Gender Distribution</h3>
          {demographics.genderDistribution.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={demographics.genderDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {demographics.genderDistribution.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap justify-center gap-4 mt-4">
                {demographics.genderDistribution.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-gray-600">{item.name}: {item.value}%</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Revenue Trend */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">Revenue Trend</h3>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip formatter={(value) => [`₹${value}`, 'Revenue']} />
                <Line type="monotone" dataKey="revenue" stroke="#0F172A" strokeWidth={2} dot={{ fill: '#0F172A' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-500">
              No revenue data
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
