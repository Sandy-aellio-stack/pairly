/**
 * FCM Push Notification Service for TrueBond
 * 
 * Handles Firebase Cloud Messaging token registration and permission management.
 * 
 * Usage:
 * 1. Call initializeFCM() after user login
 * 2. Call cleanupFCM() on logout
 * 
 * Note: Requires Firebase configuration in the app.
 * Set VITE_FIREBASE_CONFIG in .env or configure firebaseConfig below.
 */

import { userAPI } from './api';

// FCM Token storage key
const FCM_TOKEN_KEY = 'tb_fcm_token';

// Firebase config - will be provided via environment or hardcoded for test mode
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
};

// Check if Firebase is configured
const isFirebaseConfigured = () => {
  return firebaseConfig.apiKey && firebaseConfig.projectId;
};

// State
let firebaseApp = null;
let messaging = null;
let currentToken = null;

/**
 * Initialize Firebase and get FCM token
 * Call this after user login
 */
export const initializeFCM = async () => {
  try {
    // Check if Firebase is configured
    if (!isFirebaseConfigured()) {
      console.log('[FCM] Firebase not configured - push notifications disabled');
      return null;
    }

    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.log('[FCM] Browser does not support notifications');
      return null;
    }

    // Request notification permission
    const permission = await requestNotificationPermission();
    if (permission !== 'granted') {
      console.log('[FCM] Notification permission denied');
      return null;
    }

    // Dynamically import Firebase (lazy load)
    const { initializeApp } = await import('firebase/app');
    const { getMessaging, getToken, onMessage } = await import('firebase/messaging');

    // Initialize Firebase app
    if (!firebaseApp) {
      firebaseApp = initializeApp(firebaseConfig);
    }

    // Get messaging instance
    messaging = getMessaging(firebaseApp);

    // Get FCM token
    const token = await getToken(messaging, {
      vapidKey: import.meta.env.VITE_FIREBASE_VAPID_KEY || '',
    });

    if (token) {
      console.log('[FCM] Token obtained');
      currentToken = token;

      // Store locally
      localStorage.setItem(FCM_TOKEN_KEY, token);

      // Register with backend
      await registerTokenWithBackend(token);

      // Set up foreground message handler
      onMessage(messaging, handleForegroundMessage);

      return token;
    } else {
      console.log('[FCM] No registration token available');
      return null;
    }
  } catch (error) {
    console.error('[FCM] Initialization error:', error);
    return null;
  }
};

/**
 * Request notification permission from user
 */
export const requestNotificationPermission = async () => {
  try {
    if (!('Notification' in window)) {
      return 'denied';
    }

    // Check current permission
    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission === 'denied') {
      return 'denied';
    }

    // Request permission
    const permission = await Notification.requestPermission();
    return permission;
  } catch (error) {
    console.error('[FCM] Permission request error:', error);
    return 'denied';
  }
};

/**
 * Register FCM token with backend
 */
const registerTokenWithBackend = async (token) => {
  try {
    const response = await userAPI.registerFCMToken(token);
    console.log('[FCM] Token registered with backend:', response.data);
    return true;
  } catch (error) {
    console.error('[FCM] Failed to register token with backend:', error);
    return false;
  }
};

/**
 * Handle foreground messages (when app is open)
 */
const handleForegroundMessage = (payload) => {
  console.log('[FCM] Foreground message received:', payload);

  // Show in-app notification or toast
  const { title, body } = payload.notification || {};
  const data = payload.data || {};

  // If user is in the app, we might want to show a toast instead of system notification
  // This can be customized based on app state
  
  // For now, show a system notification even in foreground
  if (title && Notification.permission === 'granted') {
    new Notification(title, {
      body: body,
      icon: '/logo192.png',
      tag: data.reference_id || 'truebond-notification',
      data: data,
    });
  }

  // Dispatch custom event for app components to handle
  window.dispatchEvent(new CustomEvent('fcm-message', { detail: payload }));
};

/**
 * Clean up FCM on logout
 */
export const cleanupFCM = async () => {
  try {
    const token = localStorage.getItem(FCM_TOKEN_KEY);
    
    if (token) {
      // Unregister from backend
      try {
        await userAPI.unregisterFCMToken(token);
        console.log('[FCM] Token unregistered from backend');
      } catch (error) {
        console.warn('[FCM] Failed to unregister token:', error);
      }

      // Clear local storage
      localStorage.removeItem(FCM_TOKEN_KEY);
    }

    currentToken = null;
  } catch (error) {
    console.error('[FCM] Cleanup error:', error);
  }
};

/**
 * Get current notification permission status
 */
export const getNotificationPermission = () => {
  if (!('Notification' in window)) {
    return 'unsupported';
  }
  return Notification.permission;
};

/**
 * Check if push notifications are enabled
 */
export const isPushEnabled = () => {
  return (
    isFirebaseConfigured() &&
    'Notification' in window &&
    Notification.permission === 'granted' &&
    currentToken !== null
  );
};

/**
 * Get the current FCM token
 */
export const getCurrentToken = () => {
  return currentToken || localStorage.getItem(FCM_TOKEN_KEY);
};

export default {
  initializeFCM,
  cleanupFCM,
  requestNotificationPermission,
  getNotificationPermission,
  isPushEnabled,
  getCurrentToken,
};
