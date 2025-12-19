import { create } from 'zustand';
import { adminAuthAPI, adminAnalyticsAPI, adminUsersAPI, adminSettingsAPI, adminModerationAPI } from '../services/adminApi';

const useAdminStore = create((set, get) => ({
  admin: null,
  isAuthenticated: false,
  isLoading: true,
  
  // Dashboard data
  stats: null,
  recentActivity: [],
  highlights: null,

  initialize: async () => {
    const token = localStorage.getItem('tb_admin_token');
    if (token) {
      try {
        const response = await adminAuthAPI.getMe();
        set({ 
          admin: response.data, 
          isAuthenticated: true, 
          isLoading: false 
        });
      } catch (error) {
        localStorage.removeItem('tb_admin_token');
        localStorage.removeItem('tb_admin_user');
        set({ admin: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  login: async (email, password) => {
    const response = await adminAuthAPI.login(email, password);
    const { access_token, admin_name, admin_role } = response.data;
    localStorage.setItem('tb_admin_token', access_token);
    localStorage.setItem('tb_admin_user', JSON.stringify({ name: admin_name, role: admin_role, email }));
    set({ 
      admin: { name: admin_name, role: admin_role, email }, 
      isAuthenticated: true 
    });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('tb_admin_token');
    localStorage.removeItem('tb_admin_user');
    set({ admin: null, isAuthenticated: false });
  },

  // Fetch dashboard stats
  fetchDashboardStats: async () => {
    try {
      const [statsRes, activityRes, highlightsRes] = await Promise.all([
        adminAnalyticsAPI.getOverview(),
        adminAnalyticsAPI.getActivity(5),
        adminAnalyticsAPI.getHighlights()
      ]);
      set({ 
        stats: statsRes.data,
        recentActivity: activityRes.data.activities,
        highlights: highlightsRes.data
      });
    } catch (e) {
      console.error('Failed to fetch dashboard stats', e);
    }
  },
}));

export default useAdminStore;
