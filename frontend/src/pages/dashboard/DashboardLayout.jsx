import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Home, MapPin, MessageCircle, User, Coins, LogOut, Heart, Search, Bell } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import CustomCursor from '@/components/CustomCursor';
import gsap from 'gsap';

const DashboardLayout = () => {
  const { user, credits, logout, refreshCredits } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [showSearch, setShowSearch] = useState(false);
  const [notifications] = useState(3);

  useEffect(() => {
    refreshCredits();
  }, []);

  useEffect(() => {
    gsap.from('.main-content', {
      opacity: 0,
      y: 20,
      duration: 0.4,
      ease: 'power2.out',
    });
  }, [location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Home' },
    { path: '/dashboard/nearby', icon: MapPin, label: 'Nearby' },
    { path: '/dashboard/chat', icon: MessageCircle, label: 'Messages' },
    { path: '/dashboard/credits', icon: Coins, label: 'Wallet' },
    { path: '/dashboard/profile', icon: User, label: 'Profile' },
  ];

  return (
    <div className="min-h-screen bg-[#F8F9FB]">
      <CustomCursor />

      {/* Top Navigation Bar - Instagram Style */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <NavLink to="/dashboard" className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Heart size={20} className="text-white" fill="white" />
              </div>
              <span className="text-xl font-bold text-gray-900 hidden sm:block">TrueBond</span>
            </NavLink>

            {/* Center Nav - Desktop */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/dashboard'}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                      isActive
                        ? 'bg-purple-100 text-purple-600'
                        : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                    }`
                  }
                >
                  <item.icon size={20} />
                  <span className="font-medium text-sm">{item.label}</span>
                </NavLink>
              ))}
            </nav>

            {/* Right Section */}
            <div className="flex items-center gap-3">
              {/* Search */}
              <button
                onClick={() => setShowSearch(!showSearch)}
                className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
              >
                <Search size={20} />
              </button>

              {/* Notifications */}
              <button className="relative w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors">
                <Bell size={20} />
                {notifications > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {notifications}
                  </span>
                )}
              </button>

              {/* Credits */}
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 rounded-full">
                <Coins size={16} className="text-purple-500" />
                <span className="text-sm font-bold text-purple-600">{credits}</span>
              </div>

              {/* Profile Avatar */}
              <button
                onClick={() => navigate('/dashboard/profile')}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-sm ring-2 ring-white hover:ring-purple-200 transition-all"
              >
                {user?.name?.[0]}
              </button>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="w-10 h-10 rounded-xl hover:bg-red-50 flex items-center justify-center text-gray-400 hover:text-red-500 transition-colors"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>

        {/* Search Dropdown */}
        {showSearch && (
          <div className="border-t border-gray-100 p-4">
            <div className="max-w-xl mx-auto">
              <input
                type="text"
                placeholder="Search people, messages..."
                className="input w-full"
                autoFocus
              />
            </div>
          </div>
        )}
      </header>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-t border-gray-100 px-2 py-2 safe-area-pb">
        <div className="flex justify-around">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/dashboard'}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-colors ${
                  isActive ? 'text-purple-600' : 'text-gray-400'
                }`
              }
            >
              <item.icon size={22} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="min-h-screen pt-20 pb-24 md:pb-8">
        <div className="main-content max-w-6xl mx-auto px-4">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
