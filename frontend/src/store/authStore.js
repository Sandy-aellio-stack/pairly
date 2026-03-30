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
  coins: 0,

  initialize: async () => {
    const token = localStorage.getItem('access_token');
    
    // Clear potentially stale cached storage if any (to ensure fresh data)
    if (localStorage.getItem('auth-storage')) {
      localStorage.removeItem('auth-storage');
    }

    // Listen for real-time balance updates from socket
    if (typeof window !== 'undefined' && !window.__appBalanceListenerAdded) {
      window.__appBalanceListenerAdded = true;
      window.addEventListener('app:balance_updated', (e) => {
        const newBalance = e.detail?.coins;
        if (typeof newBalance === 'number') {
          set((state) => ({
            coins: newBalance,
            user: state.user ? { ...state.user, coins: newBalance } : null
          }));
        }
      });
    }

    try {
      if (token) {
        // Use getMe to fetch the absolute latest user state from the server
        const response = await authAPI.getMe();
        const userData = response.data;
        
        set({
          user: userData,
          isAuthenticated: true,
          coins: userData.coins,
          isLoading: false
        });
        connectSocket(token);
        // Initialize FCM for push notifications (non-blocking)
        initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
      } else {
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } catch (error) {
      console.error('[AuthStore] Initialize error:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  refreshUser: async () => {
    try {
      const response = await authAPI.getMe();
      const userData = response.data;
      set({
        user: userData,
        coins: userData.coins,
        isAuthenticated: true
      });
      return userData;
    } catch (error) {
      console.error('[AuthStore] refreshUser failed:', error);
      if (error.response?.status === 401) {
        get().logout();
      }
      throw error;
    }
  },

  updateSettings: (newSettings) => {
    set((state) => ({
      user: state.user ? { ...state.user, settings: newSettings } : null
    }));
  },

  login: async (email, password) => {
    const device_id = getDeviceId();
    const response = await authAPI.login({ email, password, device_id });

    // Backend returns: { access_token, refresh_token, user, ... } at root level
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    // Set initial user data then immediately refresh to be absolutely sure
    set({
      user: user,
      isAuthenticated: true,
      coins: user.coins
    });
    
    connectSocket(access_token);
    // Initialize FCM for push notifications (non-blocking)
    initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
    
    // Explicitly refresh to sync developer coins/unlimited status
    await get().refreshUser();
    
    return response.data;
  },

    loginWithOTP: async (payload) => {
    const response = await authAPI.loginWithOTP(payload);
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    set({
      user: user,
      isAuthenticated: true,
      coins: user?.coins || 0
    });
    connectSocket(access_token);
    initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
    
    // Sync latest state from backend (dev coins, settings)
    await get().refreshUser();
    
    return response.data;
  },

  signup: async (data) => {
    const response = await authAPI.signup(data);
    // Backend returns: { access_token, refresh_token, user, ... } at root level
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    // User data is already in the signup response, use it directly
    set({
      user: user,
      isAuthenticated: true,
      coins: user.coins
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
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false, coins: 0 });
  },

  refreshCredits: async () => {
    return await get().refreshUser();
  },

  updateCoins: (amount) => {
    set((state) => ({ coins: state.coins + amount }));
  },
}));

export default useAuthStore;
