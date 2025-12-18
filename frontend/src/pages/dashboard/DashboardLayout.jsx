import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Home, MessageCircle, MapPin, User, Coins, LogOut, Heart, Bell, Search, Settings } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import HeartCursor from '@/components/HeartCursor';

const DashboardLayout = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Home', end: true },
    { path: '/dashboard/nearby', icon: MapPin, label: 'Nearby' },
    { path: '/dashboard/chat', icon: MessageCircle, label: 'Messages' },
    { path: '/dashboard/credits', icon: Coins, label: 'Coins' },
    { path: '/dashboard/profile', icon: User, label: 'Profile' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <HeartCursor />
      
      {/* Top Navigation Bar - Instagram Style */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          {/* Logo */}
          <NavLink to="/dashboard" className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-[#0F172A] flex items-center justify-center">
              <Heart size={18} className="text-white" fill="white" />
            </div>
            <span className="text-xl font-bold text-[#0F172A] hidden sm:block">TrueBond</span>
          </NavLink>

          {/* Search Bar - Desktop */}
          <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
            <div className="relative w-full">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search people..."
                className="w-full pl-10 pr-4 py-2.5 rounded-full bg-[#F8FAFC] border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none text-sm"
              />
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2">
            {/* Coins Balance */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-[#E9D5FF]/30 rounded-full">
              <Coins size={16} className="text-[#0F172A]" />
              <span className="text-sm font-semibold text-[#0F172A]">
                {user?.credits_balance || 10}
              </span>
            </div>

            {/* Notifications */}
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative">
              <Bell size={22} className="text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full"></span>
            </button>

            {/* Profile Menu */}
            <NavLink
              to="/dashboard/profile"
              className="w-9 h-9 rounded-full bg-[#E9D5FF] flex items-center justify-center overflow-hidden border-2 border-white shadow-sm hover:shadow-md transition-all"
            >
              {user?.profile_pictures?.[0] ? (
                <img src={user.profile_pictures[0]} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <User size={18} className="text-[#0F172A]" />
              )}
            </NavLink>
          </div>
        </div>

        {/* Navigation - Desktop */}
        <nav className="hidden md:flex justify-center border-t border-gray-100 bg-white">
          <div className="flex">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                    isActive
                      ? 'text-[#0F172A] border-[#0F172A]'
                      : 'text-gray-500 border-transparent hover:text-[#0F172A]'
                  }`
                }
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            ))}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-6 py-3 text-sm font-medium text-gray-500 hover:text-rose-500 transition-colors border-b-2 border-transparent"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="pt-28 md:pt-32 pb-20 md:pb-8">
        <Outlet />
      </main>

      {/* Bottom Navigation - Mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-2 py-2 safe-area-pb z-50">
        <div className="flex justify-around">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-colors ${
                  isActive ? 'text-[#0F172A]' : 'text-gray-400'
                }`
              }
            >
              <item.icon size={22} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
};

export default DashboardLayout;
