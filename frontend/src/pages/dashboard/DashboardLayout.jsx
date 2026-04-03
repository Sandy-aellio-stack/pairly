import { useEffect, useState, useCallback } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Home, MessageCircle, MapPin, User, Coins, LogOut, Heart, Bell, Search, Settings, Phone } from 'lucide-react';
import { locationAPI, notificationsAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import IncomingCallModal from '@/components/IncomingCallModal';
import { toast } from 'sonner';
import { getSocket } from '@/services/socket';

const DashboardLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, refreshUser } = useAuthStore();
  const [unreadCount, setUnreadCount] = useState(0);

  // Sync user data with backend on load
  useEffect(() => {
    if (user) {
      refreshUser().catch(err => {
        console.error('[DashboardLayout] Failed to refresh user:', err);
      });
    }
  }, []);

  // Fetch unread notification count on mount
  const fetchUnreadCount = useCallback(async () => {
    if (!user) return;
    try {
      const res = await notificationsAPI.getUnreadCount();
      setUnreadCount(res.data?.count ?? res.data?.unread_count ?? 0);
    } catch {
      // Fail silently — don't block the UI
    }
  }, [user]);

  useEffect(() => {
    fetchUnreadCount();
  }, [fetchUnreadCount]);

  // Clear badge when on notifications page
  useEffect(() => {
    if (location.pathname === '/dashboard/notifications') {
      setUnreadCount(0);
    }
  }, [location.pathname]);

  // Global socket events
  useEffect(() => {
    if (!user) return;

    const handleNewMatch = (data) => {
      toast.success(`You matched with ${data.name || 'someone'}! 💕`, { duration: 5000 });
    };

    const handleNearbyUser = (data) => {
      toast.info(`${data.name || 'Someone'} is nearby!`, { duration: 4000 });
    };

    const handleNewNotification = () => {
      setUnreadCount(prev => prev + 1);
    };

    const s = getSocket();
    if (s) {
      s.on('new_match', handleNewMatch);
      s.on('nearby_user', handleNearbyUser);
      s.on('new_notification', handleNewNotification);
    }

    // Also listen for the custom DOM event dispatched by socket.js
    window.addEventListener('Luveloop:new_notification', handleNewNotification);

    return () => {
      const s2 = getSocket();
      if (s2) {
        s2.off('new_match', handleNewMatch);
        s2.off('nearby_user', handleNearbyUser);
        s2.off('new_notification', handleNewNotification);
      }
      window.removeEventListener('Luveloop:new_notification', handleNewNotification);
    };
  }, [user]);

  // Auto-update location every 30 seconds
  useEffect(() => {
    if (!user) return;

    const updateLocation = async () => {
      if (!navigator.geolocation) return;
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const { latitude, longitude } = position.coords;
            await locationAPI.update(latitude, longitude);
          } catch (error) {
            console.error('Failed to auto-update location:', error);
          }
        },
        (error) => {
          console.error('Geolocation error during auto-update:', error);
        },
        { enableHighAccuracy: false, timeout: 5000 }
      );
    };

    updateLocation();
    const interval = setInterval(updateLocation, 60000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Home', end: true },
    { path: '/dashboard/nearby', icon: MapPin, label: 'Nearby' },
    { path: '/dashboard/chat', icon: MessageCircle, label: 'Messages' },
    { path: '/dashboard/call-history', icon: Phone, label: 'Call History' },
    { path: '/dashboard/credits', icon: Coins, label: 'Coins' },
    { path: '/dashboard/profile', icon: User, label: 'Profile' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <IncomingCallModal />
      
      {/* Top Navigation Bar */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          {/* Logo */}
          <NavLink to="/dashboard" className="flex items-center gap-2">
            <img src="/logo.png" alt="Luveloop" className="w-9 h-9 object-contain" />
            <span className="text-xl font-bold text-[#0F172A] hidden sm:block">Luveloop</span>
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
                {user?.coins || 0}
              </span>
            </div>

            {/* Notifications Bell with real unread count */}
            <NavLink
              to="/dashboard/notifications"
              className="p-2 hover:bg-gray-100 rounded-full transition-colors relative"
            >
              <Bell size={22} className="text-gray-600" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[8px] h-[8px] bg-rose-500 rounded-full flex items-center justify-center">
                  {unreadCount > 9 && (
                    <span className="text-[8px] text-white font-bold px-0.5">{unreadCount > 99 ? '99+' : unreadCount}</span>
                  )}
                </span>
              )}
            </NavLink>

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
