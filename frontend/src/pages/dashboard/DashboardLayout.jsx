import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Home, MapPin, MessageCircle, User, Coins, LogOut, Menu, X } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import CustomCursor from '@/components/CustomCursor';

const DashboardLayout = () => {
  const { user, credits, logout, refreshCredits } = useAuthStore();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    refreshCredits();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Home' },
    { path: '/dashboard/nearby', icon: MapPin, label: 'Nearby' },
    { path: '/dashboard/chat', icon: MessageCircle, label: 'Chat' },
    { path: '/dashboard/profile', icon: User, label: 'Profile' },
    { path: '/dashboard/credits', icon: Coins, label: 'Credits' },
  ];

  return (
    <div className="min-h-screen bg-[#0B0B0F] flex">
      <CustomCursor />
      <div className="noise-overlay" />

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-black/50 border-r border-white/10 p-6">
        <div className="text-2xl font-bold gradient-text mb-10">TrueBond</div>

        <nav className="flex-1 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/dashboard'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Credits display */}
        <div className="mt-auto pt-6 border-t border-white/10">
          <div className="flex items-center gap-3 px-4 py-3 bg-purple-500/10 rounded-xl border border-purple-500/20">
            <Coins size={20} className="text-purple-400" />
            <div>
              <div className="text-sm text-white/60">Balance</div>
              <div className="font-bold text-purple-400">{credits} coins</div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 mt-4 w-full text-white/60 hover:text-red-400 transition-colors"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-lg border-b border-white/10">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="text-xl font-bold gradient-text">TrueBond</div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-purple-500/20 rounded-full">
              <Coins size={16} className="text-purple-400" />
              <span className="text-purple-400 font-bold text-sm">{credits}</span>
            </div>
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <nav className="px-4 py-4 space-y-2 bg-black/95">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/dashboard'}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    isActive
                      ? 'bg-purple-500/20 text-purple-400'
                      : 'text-white/60'
                  }`
                }
              >
                <item.icon size={20} />
                {item.label}
              </NavLink>
            ))}
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-3 w-full text-red-400"
            >
              <LogOut size={20} />
              Logout
            </button>
          </nav>
        )}
      </div>

      {/* Mobile Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-lg border-t border-white/10">
        <div className="flex justify-around py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/dashboard'}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-4 py-2 ${
                  isActive ? 'text-purple-400' : 'text-white/40'
                }`
              }
            >
              <item.icon size={20} />
              <span className="text-xs">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 lg:p-8 p-4 pt-20 pb-24 lg:pt-8 lg:pb-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;
