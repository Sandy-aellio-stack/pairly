import axios from 'axios';

import { API_BASE_URL } from '../config/api';

const API_URL = API_BASE_URL;

// Base URL - backend routes already include /api prefix
// Do NOT add /api here to avoid duplication (/api/api/...)
let baseURL = API_URL.replace(/\/+$/, ''); // Remove trailing slashes

const api = axios.create({
  baseURL: baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('tb_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh and error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const url = originalRequest?.url || '';
      // Don't try refresh on login/signup endpoints
      const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/signup') || url.includes('/auth/otp');

      if (!isAuthEndpoint) {
        const refreshToken = localStorage.getItem('tb_refresh_token');

        if (refreshToken) {
          try {
            const response = await axios.post(`${baseURL}/auth/refresh`, {
              refresh_token: refreshToken
            });

            const { access_token, refresh_token } = response.data;
            localStorage.setItem('tb_access_token', access_token);
            localStorage.setItem('tb_refresh_token', refresh_token);

            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return api(originalRequest);
          } catch (refreshError) {
            // Refresh failed - clear tokens and redirect to login
            localStorage.removeItem('tb_access_token');
            localStorage.removeItem('tb_refresh_token');
            localStorage.removeItem('tb_user');
            window.location.href = '/';
            return Promise.reject(refreshError);
          }
        } else {
          // No refresh token - clear and redirect
          localStorage.removeItem('tb_access_token');
          localStorage.removeItem('tb_refresh_token');
          localStorage.removeItem('tb_user');
          window.location.href = '/';
        }
      }
    }
    return Promise.reject(error);
  }
);

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
  // Firebase Phone Auth
  firebaseLogin: (data) => api.post('/api/auth/firebase-login', data),
};

// User APIs
export const userAPI = {
  getDashboardStats: () => api.get('/api/users/dashboard-stats'),
  getProfile: (userId) => api.get(`/api/users/profile/${userId}`),
  updateProfile: (data) => api.put('/api/users/profile', data),
  updatePreferences: (data) => api.put('/api/users/preferences', data),
  getCredits: () => api.get('/api/users/credits'),
  uploadPhoto: (formData) => api.post('/api/users/upload-photo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getSettings: () => api.get('/api/users/settings'),
  updateSettings: (data) => api.put('/api/users/settings', data),
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
  startConversation: (receiver_id) => api.post('/api/messages/start-conversation', { receiver_id }),
  send: (receiver_id, content) => api.post('/api/messages/send', { receiver_id, content }),
  getConversations: () => api.get('/api/messages/conversations'),
  getMessages: (userId, limit = 50) => api.get(`/api/messages/${userId}?limit=${limit}`),
  markRead: (userId) => api.post(`/api/messages/read/${userId}`),
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

export default api;
