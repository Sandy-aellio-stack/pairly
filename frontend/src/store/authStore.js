import { create } from 'zustand';
import { authAPI, creditsAPI } from '../services/api';
import { connectSocket, disconnectSocket } from '../services/socket';
import { initializeFCM, cleanupFCM } from '../services/fcm';

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
        set({ 
          user: response.data, 
          isAuthenticated: true, 
          credits: response.data.credits_balance,
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
    const response = await authAPI.login({ email, password });
    const { tokens, user_id } = response.data;
    localStorage.setItem('tb_access_token', tokens.access_token);
    localStorage.setItem('tb_refresh_token', tokens.refresh_token);
    
    const userResponse = await authAPI.getMe();
    set({ 
      user: userResponse.data, 
      isAuthenticated: true,
      credits: userResponse.data.credits_balance 
    });
    connectSocket(tokens.access_token);
    // Initialize FCM for push notifications (non-blocking)
    initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
    return response.data;
  },

  signup: async (data) => {
    const response = await authAPI.signup(data);
    const { tokens, user_id, credits_balance } = response.data;
    localStorage.setItem('tb_access_token', tokens.access_token);
    localStorage.setItem('tb_refresh_token', tokens.refresh_token);
    
    const userResponse = await authAPI.getMe();
    set({ 
      user: userResponse.data, 
      isAuthenticated: true,
      credits: credits_balance 
    });
    // Initialize FCM for push notifications (non-blocking)
    initializeFCM().catch(err => console.warn('[Auth] FCM init failed:', err));
    return response.data;
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } catch (e) {}
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
    } catch (e) {}
  },

  updateCredits: (amount) => {
    set((state) => ({ credits: state.credits + amount }));
  },
}));

export default useAuthStore;
