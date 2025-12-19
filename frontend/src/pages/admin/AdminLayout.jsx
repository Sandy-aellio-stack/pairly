import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Shield, BarChart3, Settings, FileText, LogOut, Heart, Bell } from 'lucide-react';
import useAdminStore from '@/store/adminStore';

const AdminLayout = () => {
  const navigate = useNavigate();
  const { admin, logout } = useAdminStore();

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const navItems = [
    { path: '/admin', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { path: '/admin/users', icon: Users, label: 'User Management' },
    { path: '/admin/moderation', icon: Shield, label: 'Moderation' },
    { path: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/admin/settings', icon: Settings, label: 'Settings' },
    { path: '/admin/logs', icon: FileText, label: 'Admin Log' },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 bg-[#0F172A] text-white flex flex-col z-50">
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#E9D5FF] flex items-center justify-center">
              <Heart size={20} className="text-[#0F172A]" fill="currentColor" />
            </div>
            <div>
              <h1 className="font-bold text-lg">TrueBond</h1>
              <p className="text-xs text-white/60">Admin Panel</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-white/10 text-white font-medium'
                    : 'text-white/70 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User & Logout */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-10 h-10 rounded-full bg-[#E9D5FF] flex items-center justify-center">
              <span className="text-[#0F172A] font-bold">{admin?.name?.[0] || 'A'}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{admin?.name || 'Admin'}</p>
              <p className="text-xs text-white/60 capitalize">{admin?.role?.replace('_', ' ') || 'Administrator'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-white/70 hover:bg-white/5 hover:text-white transition-all"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        {/* Top Bar */}
        <header className="sticky top-0 bg-white border-b border-gray-100 px-8 py-4 z-40">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-[#0F172A]">Admin Dashboard</h2>
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-gray-100 rounded-full relative">
                <Bell size={20} className="text-gray-600" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full"></span>
              </button>
              <NavLink to="/dashboard" className="text-sm text-[#0F172A] hover:underline">
                Back to App →
              </NavLink>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
