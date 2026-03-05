import { create } from 'zustand';
import { authAPI, creditsAPI } from '../services/api';
import { connectSocket, disconnectSocket } from '../services/socket';
import { initializeFCM, cleanupFCM } from '../services/fcm';

const getDeviceId = () => {
  let deviceId = localStorage.getItem('tb_device_id');
  if (!deviceId) {
    // Generate a simple unique ID if crypto.randomUUID is not available
    deviceId = typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : Math.random().toString(36).substring(2) + Date.now().toString(36);
    localStorage.setItem('tb_device_id', deviceId);
  }
  return deviceId;
};

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  credits: 0,

  initialize: async () => {
    const token = localStorage.getItem('tb_access_token');
    if (token) {
      try {
        const response = await authAPI.getMe();
        // getMe returns "credits" not "credits_balance"
        set({
          user: response.data,
          isAuthenticated: true,
          credits: response.data.credits,
          isLoading: false
        });
        connectSocket(token);
        // Initialize FCM for push notifications (non-blocking)
        initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
      } catch (error) {
        localStorage.removeItem('tb_access_token');
        localStorage.removeItem('tb_refresh_token');
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  login: async (email, password) => {
    const device_id = getDeviceId();
    const response = await authAPI.login({ email, password, device_id });

    // Backend returns: { access_token, refresh_token, user, ... } at root level
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('tb_access_token', access_token);
    localStorage.setItem('tb_refresh_token', refresh_token);

    // User data is already in the login response, use it directly
    set({
      user: user,
      isAuthenticated: true,
      credits: user.credits
    });
    connectSocket(access_token);
    // Initialize FCM for push notifications (non-blocking)
    initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
    return response.data;
  },

  signup: async (data) => {
    const response = await authAPI.signup(data);
    // Backend returns: { access_token, refresh_token, user, ... } at root level
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('tb_access_token', access_token);
    localStorage.setItem('tb_refresh_token', refresh_token);

    // User data is already in the signup response, use it directly
    set({
      user: user,
      isAuthenticated: true,
      credits: user.credits
    });
    // Initialize FCM for push notifications (non-blocking)
    initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
    return response.data;
  },


  logout: async () => {
    try {
      await authAPI.logout();
    } catch (e) { }
    // Cleanup FCM token (non-blocking)
    cleanupFCM().catch(err => console.warn('[Auth] FCM cleanup failed:', err));
    disconnectSocket();
    localStorage.removeItem('tb_access_token');
    localStorage.removeItem('tb_refresh_token');
    set({ user: null, isAuthenticated: false, credits: 0 });
  },

  refreshCredits: async () => {
    try {
      const response = await creditsAPI.getBalance();
      const newBalance = response.data.credits_balance;
      set((state) => ({
        credits: newBalance,
        user: state.user ? { ...state.user, credits_balance: newBalance } : null
      }));
    } catch (e) { }
  },

  updateCredits: (amount) => {
    set((state) => ({ credits: state.credits + amount }));
  },
}));

export default useAuthStore;
