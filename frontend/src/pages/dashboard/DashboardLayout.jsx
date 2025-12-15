import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Home, MapPin, MessageCircle, User, Coins, LogOut, Heart, Menu, X } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import CustomCursor from '@/components/CustomCursor';
import gsap from 'gsap';

const DashboardLayout = () => {
  const { user, credits, logout, refreshCredits } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    { path: '/dashboard/profile', icon: User, label: 'Profile' },
    { path: '/dashboard/credits', icon: Coins, label: 'Wallet' },
  ];

  return (
    <div className="min-h-screen bg-[#F8F9FB] flex">
      <CustomCursor />

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-72 bg-white border-r border-gray-100 p-6 fixed h-full">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Heart size={24} className="text-white" fill="white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">TrueBond</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/dashboard'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Credits Display */}
        <div className="mt-auto">
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm">
                <Coins size={24} className="text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Balance</p>
                <p className="text-xl font-bold text-purple-600">{credits} coins</p>
              </div>
            </div>
          </div>

          {/* User Profile */}
          <div className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold">
              {user?.name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">{user?.name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full mt-4 flex items-center gap-3 px-4 py-3 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-b border-gray-100">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Heart size={16} className="text-white" fill="white" />
            </div>
            <span className="font-bold text-gray-900">TrueBond</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 px-3 py-1.5 bg-purple-50 rounded-full">
              <Coins size={14} className="text-purple-500" />
              <span className="text-sm font-bold text-purple-600">{credits}</span>
            </div>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-gray-600"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="bg-white border-b border-gray-100 px-4 py-4 space-y-2">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/dashboard'}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                    isActive ? 'bg-purple-500 text-white' : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                <item.icon size={20} />
                {item.label}
              </NavLink>
            ))}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 text-red-500 hover:bg-red-50 rounded-xl"
            >
              <LogOut size={20} />
              Logout
            </button>
          </div>
        )}
      </header>

      {/* Mobile Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 mobile-nav px-4 py-2 safe-area-pb">
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
      <main className="flex-1 lg:ml-72 min-h-screen">
        <div className="main-content p-4 lg:p-8 pt-20 pb-24 lg:pt-8 lg:pb-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
