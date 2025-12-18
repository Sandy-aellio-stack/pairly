import { useState } from 'react';
import { TrendingUp, Users, Calendar, Activity } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const userGrowthData = [
  { month: 'Jan', users: 2400 },
  { month: 'Feb', users: 3200 },
  { month: 'Mar', users: 4100 },
  { month: 'Apr', users: 5300 },
  { month: 'May', users: 6800 },
  { month: 'Jun', users: 8200 },
  { month: 'Jul', users: 9600 },
  { month: 'Aug', users: 10800 },
  { month: 'Sep', users: 11500 },
  { month: 'Oct', users: 12100 },
  { month: 'Nov', users: 12800 },
  { month: 'Dec', users: 13500 },
];

const dauMauData = [
  { day: 'Mon', dau: 4200, mau: 8500 },
  { day: 'Tue', dau: 4500, mau: 8700 },
  { day: 'Wed', dau: 4800, mau: 8900 },
  { day: 'Thu', dau: 5100, mau: 9100 },
  { day: 'Fri', dau: 5500, mau: 9400 },
  { day: 'Sat', dau: 6200, mau: 9800 },
  { day: 'Sun', dau: 5800, mau: 9600 },
];

const demographicsData = [
  { name: '18-24', value: 35, color: '#E9D5FF' },
  { name: '25-34', value: 40, color: '#0F172A' },
  { name: '35-44', value: 18, color: '#DBEAFE' },
  { name: '45+', value: 7, color: '#FCE7F3' },
];

const genderData = [
  { name: 'Male', value: 48, color: '#DBEAFE' },
  { name: 'Female', value: 49, color: '#FCE7F3' },
  { name: 'Other', value: 3, color: '#E9D5FF' },
];

const revenueData = [
  { month: 'Jan', revenue: 12000 },
  { month: 'Feb', revenue: 15000 },
  { month: 'Mar', revenue: 18000 },
  { month: 'Apr', revenue: 22000 },
  { month: 'May', revenue: 28000 },
  { month: 'Jun', revenue: 35000 },
];

const AnalyticsPage = () => {
  const [timeRange, setTimeRange] = useState('year');

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
          <p className="text-2xl font-bold text-[#0F172A]">13.5K</p>
          <p className="text-sm text-gray-500">Total Users</p>
          <p className="text-xs text-green-600 mt-1">+12% from last month</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#DBEAFE] rounded-xl flex items-center justify-center">
              <Activity size={20} className="text-blue-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A]">5.2K</p>
          <p className="text-sm text-gray-500">Daily Active</p>
          <p className="text-xs text-green-600 mt-1">+8% from last week</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#D1FAE5] rounded-xl flex items-center justify-center">
              <TrendingUp size={20} className="text-green-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A]">₹35K</p>
          <p className="text-sm text-gray-500">Revenue (Month)</p>
          <p className="text-xs text-green-600 mt-1">+25% from last month</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-[#FCE7F3] rounded-xl flex items-center justify-center">
              <Calendar size={20} className="text-rose-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-[#0F172A]">38%</p>
          <p className="text-sm text-gray-500">DAU/MAU Ratio</p>
          <p className="text-xs text-green-600 mt-1">+3% from last month</p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* User Growth */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">User Growth</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={userGrowthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip />
              <Area type="monotone" dataKey="users" stroke="#0F172A" fill="#E9D5FF" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* DAU/MAU */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">DAU vs MAU</h3>
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
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={demographicsData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {demographicsData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {demographicsData.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-sm text-gray-600">{item.name}: {item.value}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Gender Distribution */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">Gender Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={genderData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {genderData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {genderData.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-sm text-gray-600">{item.name}: {item.value}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Revenue Trend */}
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-[#0F172A] mb-6">Revenue Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip formatter={(value) => [`₹${value}`, 'Revenue']} />
              <Line type="monotone" dataKey="revenue" stroke="#0F172A" strokeWidth={2} dot={{ fill: '#0F172A' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
