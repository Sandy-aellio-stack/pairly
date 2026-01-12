import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');

const api = axios.create({
  baseURL: `${API_URL}/api`,
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('tb_access_token');
      localStorage.removeItem('tb_refresh_token');
      localStorage.removeItem('tb_user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Auth APIs - matches /api/auth/*
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  sendOTP: (mobile_number) => api.post('/auth/otp/send', { mobile_number }),
  verifyOTP: (mobile_number, otp_code) => api.post('/auth/otp/verify', { mobile_number, otp_code }),
};

// User APIs - matches /api/users/*
export const userAPI = {
  getProfile: (userId) => api.get(`/users/profile/${userId}`),
  updateProfile: (data) => api.put('/users/profile', data),
  updatePreferences: (data) => api.put('/users/preferences', data),
  getCredits: () => api.get('/users/credits'),
  uploadPhoto: (formData) => api.post('/users/upload-photo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getSettings: () => api.get('/users/settings'),
  updateSettings: (data) => api.put('/users/settings', data),
};

// Credits APIs - matches /api/credits/*
export const creditsAPI = {
  getBalance: () => api.get('/credits/balance'),
  getHistory: (limit = 50) => api.get(`/credits/history?limit=${limit}`),
};

// Location APIs - matches /api/location/*
export const locationAPI = {
  update: (latitude, longitude) => api.post('/location/update', { latitude, longitude }),
  getNearby: (lat, lng, radius_km = 50) => 
    api.get(`/location/nearby?lat=${lat}&lng=${lng}&radius_km=${radius_km}`),
};

// Messages APIs - matches /api/messages/*
export const messagesAPI = {
  send: (receiver_id, content) => api.post('/messages/send', { receiver_id, content }),
  getConversations: () => api.get('/messages/conversations'),
  getMessages: (userId, limit = 50) => api.get(`/messages/${userId}?limit=${limit}`),
  markRead: (userId) => api.post(`/messages/read/${userId}`),
};

// Payments APIs - matches /api/payments/*
export const paymentsAPI = {
  getPackages: () => api.get('/payments/packages'),
  detectProvider: () => api.post('/payments/detect-provider'),
  checkout: (data) => api.post('/payments/checkout', data),
  createOrder: (package_id) => api.post('/payments/order', { package_id }),
  verifyPayment: (data) => api.post('/payments/verify', data),
  getHistory: () => api.get('/payments/history'),
};

// Notifications APIs - matches /api/notifications/*
export const notificationsAPI = {
  getAll: (unreadOnly = false, limit = 20) => 
    api.get(`/notifications?unread_only=${unreadOnly}&limit=${limit}`),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (notificationId) => api.post(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.post('/notifications/mark-all-read'),
};

export default api;
