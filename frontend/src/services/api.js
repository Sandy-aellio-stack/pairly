import axios from 'axios';

import { API_BASE_URL } from '../config/api';

// Empty base URL = relative paths. Vite proxies /api → localhost:8000 in dev;
// in production the same-origin server handles /api directly.
const defaultApiUrl = import.meta.env.VITE_API_URL || "";

const api = axios.create({
  baseURL: defaultApiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptors to both instances
const addRequestInterceptor = (axiosInstance) => {
  axiosInstance.interceptors.request.use(
    (config) => {
      const accessToken = localStorage.getItem('access_token');
      console.log(`[AXIOS DEBUG] Request: ${config.method?.toUpperCase()} ${config.url} - Auth: ${accessToken ? 'PRESENT' : 'MISSING'}`);
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      return config;
    },
    (error) => {
      console.log(`[AXIOS DEBUG] Request Error: ${error.message}`);
      return Promise.reject(error);
    }
  );
};

const addResponseInterceptor = (axiosInstance) => {
  axiosInstance.interceptors.response.use(
    (response) => {
      console.log(`[AXIOS DEBUG] Response: ${response.status} ${response.config.url}`);
      return response;
    },
    async (error) => {
      console.log(`[AXIOS DEBUG] Response Error: ${error.response?.status || error.code} for ${error.config?.url}`);
      const originalRequest = error.config;

      // Handle 401 errors - try to refresh token
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        const url = originalRequest?.url || '';
        // Don't try refresh on login/signup endpoints
        const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/signup') || url.includes('/auth/otp');

        if (!isAuthEndpoint) {
          const refreshToken = localStorage.getItem('refresh_token');

          if (refreshToken) {
            try {
              const response = await axios.post(`${api.defaults.baseURL}/api/auth/refresh`, {
                refresh_token: refreshToken
              });

              const { access_token, refresh_token } = response.data;
              localStorage.setItem('access_token', access_token);
              localStorage.setItem('refresh_token', refresh_token);

              // Retry the original request with new token
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return axiosInstance(originalRequest);
            } catch (refreshError) {
              // Refresh failed - clear tokens and redirect to login
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('tb_user');
              window.location.href = '/';
              return Promise.reject(refreshError);
            }
          } else {
            // No refresh token - clear and redirect
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('tb_user');
            window.location.href = '/';
          }
        }
      }
      return Promise.reject(error);
    }
  );
};

addRequestInterceptor(api);
addResponseInterceptor(api);

// Auth APIs
export const authAPI = {
  signup: (data) => api.post('/api/auth/signup', data),
  login: (data) => api.post('/api/auth/login', data),
  logout: () => api.post('/api/auth/logout'),
  getMe: () => api.get('/api/auth/me'),
  // Mobile OTP
  sendOTP: (mobile_number) => api.post('/api/auth/otp/send', { mobile_number }),
  verifyOTP: (mobile_number, otp) => api.post('/api/auth/otp/verify', { mobile_number, otp }),
  // Email OTP
  sendEmailOTP: (email) => api.post('/api/auth/email/send-otp', { email }),
  verifyEmailOTP: (email, otp) => api.post('/api/auth/email/verify-otp', { email, otp }),
  // Dual-mode OTP (New)
  sendOTPForLogin: (data) => api.post('/api/auth/otp/send-for-login', data),
  sendOTPForSignup: (data) => api.post('/api/auth/otp/send-for-signup', data),
  loginWithOTP: (data) => api.post('/api/auth/login-with-otp', data),
  signupWithOTP: (data) => api.post('/api/auth/signup-with-otp', data),
  // Password Reset
  forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
  resetPassword: (token, new_password) => api.post('/api/auth/reset-password', { token, new_password }),
  validateResetToken: (token) => api.get(`/api/auth/validate-reset-token?token=${token}`),
  // Login Approval
  approveLogin: (pending_session_id) => api.post('/api/auth/login/approve', { pending_session_id }),
  denyLogin: (pending_session_id) => api.post('/api/auth/login/deny', { pending_session_id }),
  checkLoginStatus: (pending_session_id) => api.get(`/api/auth/login/status/${pending_session_id}`),
};

// User APIs
export const userAPI = {
  getDashboardStats: () => api.get('/api/users/dashboard-stats'),
  getNearby: (limit = 20) => api.get(`/api/users/nearby?limit=${limit}`),
  getSuggestions: (limit = 3) => api.get(`/api/users/suggestions?limit=${limit}`),
  getStreak: () => api.get('/api/users/streak'),
  getProfile: (userId) => api.get(`/api/users/profile/${userId}`),
  updateProfile: (data) => api.put('/api/users/profile', data),
  updatePreferences: (data) => api.put('/api/users/preferences', data),
  // User Search & Feed
  search: (query, page = 1, limit = 20) => api.get(`/api/users/search?q=${encodeURIComponent(query)}&page=${page}&limit=${limit}`),
  getFeed: (page = 1, limit = 20) => api.get(`/api/users/feed?page=${page}&limit=${limit}`),
  // Block/Report
  blockUser: (userId, reason) => api.post(`/api/users/block/${userId}`, { reason }),
  unblockUser: (userId) => api.delete(`/api/users/block/${userId}`),
  getBlockedUsers: () => api.get('/api/users/blocked'),
  reportUser: (userId, reason, report_type = 'profile') => api.post(`/api/users/report/${userId}`, { reason, report_type }),
  // FCM Token Management
  registerFCMToken: (token) => api.post('/api/users/fcm-token', { token }),
  unregisterFCMToken: (token) => api.delete('/api/users/fcm-token', { data: { token } }),
  unregisterAllFCMTokens: () => api.delete('/api/users/fcm-tokens/all'),
  // Fix for ChatPage - simple block without userId in path
  blockUserSimple: (data) => api.post('/api/users/block', data),
  // Conversation Management
  createOrGetConversation: (userId) => api.post('/api/users/create-or-get-conversation', { user_id: userId }),
  // Settings Management
  getSettings: () => api.get('/api/settings'),
  updateSettings: (data) => api.post('/api/settings', data),
  deleteAccount: () => api.delete('/api/users/account'),
};



// Credits APIs
export const creditsAPI = {
  getBalance: () => api.get('/api/credits/balance'),
  getHistory: (limit = 50) => api.get(`/api/credits/history?limit=${limit}`),
};

// Location APIs
export const locationAPI = {
  update: (latitude, longitude) => api.post('/api/location/update', { latitude, longitude }),
  getNearby: (lat, lng, radius_km = 50) =>
    api.get(`/api/location/nearby-with-location?lat=${lat}&lng=${lng}&radius_km=${radius_km}`),
};

// Messages APIs
export const messagesAPI = {
  // ... existing methods unchanged

  startConversation: (receiver_id) => api.post('/api/messages/start-conversation', { receiver_id }),
  getConversations: () => api.get('/api/messages/conversations'),
  getConversationDetails: (conversationId) => api.get(`/api/messages/conversation/${conversationId}`),
  getMessages: (userId, limit = 50, before = null) => {
    let url = `/api/messages/${userId}?limit=${limit}`;
    if (before) url += `&before=${before}`;
    return api.get(url);
  },
  send: (data) => api.post('/api/messages/send', data),
  markRead: (userId) => api.post(`/api/messages/read/${userId}`),
  uploadMedia: (userId, formData) => api.post(`/api/messages/${userId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // Central conversation management
  createOrGetConversation: (targetUserId) => api.post('/api/users/create-or-get-conversation', { user_id: targetUserId }),

  // Test endpoint for debugging
  testEndpoint: () => api.get('/api/messages/test'),
  
  // Fix for ChatPage direct calls
  uploadImage: (formData) => api.post('/api/messages/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};



// Payments APIs
export const paymentsAPI = {
  getPackages: () => api.get('/api/payments/packages'),
  detectProvider: () => api.post('/api/payments/detect-provider'),
  checkout: (data) => api.post('/api/payments/checkout', data),
  createOrder: (package_id) => api.post('/api/payments/order', { package_id }),
  verifyPayment: (data) => api.post('/api/payments/verify', data),
  getHistory: () => api.get('/api/payments/history'),
};

// Notifications APIs
export const notificationsAPI = {
  getAll: (unreadOnly = false, limit = 20) =>
    api.get(`/api/notifications?unread_only=${unreadOnly}&limit=${limit}`),
  getUnreadCount: () => api.get('/api/notifications/unread-count'),
  markAsRead: (notificationId) => api.post(`/api/notifications/${notificationId}/read`),
  markAllAsRead: () => api.post('/api/notifications/mark-all-read'),
};

// Referral APIs
export const referralAPI = {
  getMyCode: () => api.get('/api/users/referral/my-code'),
  applyCode: (referral_code) => api.post('/api/users/referral/apply', { referral_code }),
  getStats: () => api.get('/api/users/referral/stats'),
};

// Admin APIs
export const adminAPI = {
  getOverview: () => api.get('/api/admin/analytics/overview'),
  getRevenueOverall: () => api.get('/api/admin/analytics/revenue/overall'),
  getRevenueDaily: (days = 7) => api.get(`/api/admin/analytics/revenue/daily?days=${days}`),
  getRevenueWeekly: (weeks = 8) => api.get(`/api/admin/analytics/revenue/weekly?weeks=${weeks}`),
  getRevenueMonthly: (months = 12) => api.get(`/api/admin/analytics/revenue/monthly?months=${months}`),
  getRevenuePerUser: (limit = 20) => api.get(`/api/admin/analytics/revenue/per-user?limit=${limit}`),
  sendNotification: (title, body, type = 'system', userIds = null) =>
    api.post('/api/admin/users/notifications/send', { title, body, notification_type: type, user_ids: userIds }),
  
  // Fix for ChatPage - simple report without userId in path
  reportUserSimple: (data) => api.post('/api/admin/report-user', data),
};

export default api;

