import { io } from 'socket.io-client';
import { API_BASE_URL } from '../config/api';

let socket = null;

const SOCKET_URL = API_BASE_URL;

export const connectSocket = (token) => {
  if (socket?.connected) {
    return socket;
  }

  socket = io(SOCKET_URL, {
    auth: { token },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    path: '/socket.io',
  });

  socket.on('connect', () => {
    console.log('Socket connected:', socket.id);
  });

  socket.on('disconnect', (reason) => {
    console.log('Socket disconnected:', reason);
  });

  socket.on('connect_error', (error) => {
    console.error('Socket connection error:', error.message);
  });

  socket.on('force_logout', (data) => {
    console.warn('Force logout received:', data?.reason || 'New device login');
    localStorage.removeItem('tb_access_token');
    localStorage.removeItem('tb_refresh_token');
    localStorage.removeItem('tb_user');
    socket.disconnect();
    socket = null;
    window.location.href = '/';
  });

  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

export const getSocket = () => socket;

export const joinChat = (userId) => {
  return new Promise((resolve, reject) => {
    if (!socket?.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('join_chat', { user_id: userId }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const leaveChat = (roomId) => {
  if (socket?.connected) {
    socket.emit('leave_chat', { room_id: roomId });
  }
};

export const sendMessage = (receiverId, content, type = 'text') => {
  return new Promise((resolve, reject) => {
    if (!socket?.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('send_message', { receiver_id: receiverId, content, type }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const sendTyping = (receiverId) => {
  if (socket?.connected) {
    socket.emit('typing', { receiver_id: receiverId });
  }
};

export const sendStopTyping = (receiverId) => {
  if (socket?.connected) {
    socket.emit('stop_typing', { receiver_id: receiverId });
  }
};

export const callUser = (receiverId, callType, offer) => {
  return new Promise((resolve, reject) => {
    if (!socket?.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('call_user', { receiver_id: receiverId, call_type: callType, offer }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const answerCall = (callId, answer) => {
  return new Promise((resolve, reject) => {
    if (!socket?.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('answer_call', { call_id: callId, answer }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const rejectCall = (callId, reason = 'rejected') => {
  return new Promise((resolve, reject) => {
    if (!socket?.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('reject_call', { call_id: callId, reason }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const endCall = (callId) => {
  return new Promise((resolve, reject) => {
    if (!socket?.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('end_call', { call_id: callId }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const sendIceCandidate = (callId, candidate) => {
  if (socket?.connected) {
    socket.emit('ice_candidate', { call_id: callId, candidate });
  }
};

export const onNewMessage = (callback) => {
  socket?.on('new_message', callback);
};

export const offNewMessage = (callback) => {
  socket?.off('new_message', callback);
};

export const onTyping = (callback) => {
  socket?.on('user_typing', callback);
};

export const onStopTyping = (callback) => {
  socket?.on('user_stopped_typing', callback);
};

export const onIncomingCall = (callback) => {
  socket?.on('incoming_call', callback);
};

export const offIncomingCall = (callback) => {
  socket?.off('incoming_call', callback);
};

export const onCallAnswered = (callback) => {
  socket?.on('call_answered', callback);
};

export const onCallRejected = (callback) => {
  socket?.on('call_rejected', callback);
};

export const onCallEnded = (callback) => {
  socket?.on('call_ended', callback);
};

export const onIceCandidate = (callback) => {
  socket?.on('ice_candidate', callback);
};

export const removeCallListeners = () => {
  if (socket) {
    socket.off('call_answered');
    socket.off('call_rejected');
    socket.off('call_ended');
    socket.off('ice_candidate');
  }
};

export const removeChatListeners = () => {
  if (socket) {
    socket.off('new_message');
    socket.off('user_typing');
    socket.off('user_stopped_typing');
  }
};

export const onForceLogout = (callback) => {
  socket?.on('force_logout', callback);
};

export const removeAllListeners = () => {
  if (socket) {
    socket.off('new_message');
    socket.off('user_typing');
    socket.off('user_stopped_typing');
    socket.off('incoming_call');
    socket.off('call_answered');
    socket.off('call_rejected');
    socket.off('call_ended');
    socket.off('ice_candidate');
    socket.off('force_logout');
  }
};

export default {
  connectSocket,
  disconnectSocket,
  getSocket,
  joinChat,
  leaveChat,
  sendMessage,
  sendTyping,
  sendStopTyping,
  callUser,
  answerCall,
  rejectCall,
  endCall,
  sendIceCandidate,
  onNewMessage,
  offNewMessage,
  onTyping,
  onStopTyping,
  onIncomingCall,
  offIncomingCall,
  onCallAnswered,
  onCallRejected,
  onCallEnded,
  onIceCandidate,
  onForceLogout,
  removeCallListeners,
  removeChatListeners,
  removeAllListeners,
};
