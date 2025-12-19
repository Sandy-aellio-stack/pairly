import axios from 'axios';

const API_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const adminApi = axios.create({
  baseURL: `${API_URL}/api/admin`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add admin auth token
adminApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('tb_admin_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
adminApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('tb_admin_token');
      localStorage.removeItem('tb_admin_user');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

// Admin Auth APIs
export const adminAuthAPI = {
  login: (email, password) => adminApi.post('/login', { email, password }),
  getMe: () => adminApi.get('/me'),
};

// Admin Users APIs
export const adminUsersAPI = {
  list: (params = {}) => adminApi.get('/users', { params }),
  get: (userId) => adminApi.get(`/users/${userId}`),
  suspend: (userId) => adminApi.post(`/users/${userId}/suspend`),
  reactivate: (userId) => adminApi.post(`/users/${userId}/reactivate`),
  adjustCredits: (userId, amount, reason) => 
    adminApi.post(`/users/${userId}/adjust-credits?amount=${amount}&reason=${encodeURIComponent(reason)}`),
};

// Admin Analytics APIs
export const adminAnalyticsAPI = {
  getOverview: () => adminApi.get('/analytics/overview'),
  getUserGrowth: (period = 'year') => adminApi.get(`/analytics/user-growth?period=${period}`),
  getDemographics: () => adminApi.get('/analytics/demographics'),
  getRevenue: (period = 'month') => adminApi.get(`/analytics/revenue?period=${period}`),
  getActivity: (limit = 10) => adminApi.get(`/analytics/activity?limit=${limit}`),
  getHighlights: () => adminApi.get('/analytics/highlights'),
};

// Admin Settings APIs
export const adminSettingsAPI = {
  get: () => adminApi.get('/settings'),
  update: (data) => adminApi.put('/settings', data),
  getPricing: () => axios.get(`${API_URL}/api/admin/settings/pricing`), // Public endpoint
};

// Admin Moderation APIs
export const adminModerationAPI = {
  listReports: (params = {}) => adminApi.get('/moderation/reports', { params }),
  getStats: () => adminApi.get('/moderation/stats'),
  approveReport: (reportId) => adminApi.post(`/moderation/reports/${reportId}/approve`),
  removeContent: (reportId) => adminApi.post(`/moderation/reports/${reportId}/remove`),
  banUser: (reportId) => adminApi.post(`/moderation/reports/${reportId}/ban`),
};

export default adminApi;
