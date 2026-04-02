import { io } from "socket.io-client";

import { API_BASE_URL } from "../config/api";

let socket = null;

/*
  IMPORTANT:
  Your backend runs on port 8000
  Your frontend runs on port 5000
*/
const SOCKET_URL = import.meta.env.VITE_API_URL || API_BASE_URL;

export const connectSocket = (token) => {
  const accessToken = token || localStorage.getItem("access_token");
  console.log("Socket token:", accessToken);
  console.log('[SOCKET DEBUG] connectSocket invoked');
  console.log('[SOCKET DEBUG] SOCKET_URL:', SOCKET_URL);
  console.log('[SOCKET DEBUG] Token present:', !!accessToken);

  if (socket && socket.connected) {
    console.log('[SOCKET DEBUG] Reusing existing connected socket');
    return socket;
  }

  socket = io(SOCKET_URL, {
    transports: ["websocket"],
    auth: {
      token: accessToken,
    },
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    timeout: 20000,
    withCredentials: true,
    path: "/socket.io",
  });

  /* ---------- CONNECTION EVENTS ---------- */

  socket.on("connect", () => {
    console.log("✅ [SOCKET DEBUG] connected:", socket.id);
  });

  socket.on("disconnect", (reason) => {
    console.log("❌ [SOCKET DEBUG] disconnected, reason:", reason);
  });

  socket.on("connect_error", (error) => {
    console.error("❌ [SOCKET DEBUG] connect_error:", error.message);
    console.error("[SOCKET DEBUG] Full error object:", error);
  });

  socket.io.on("reconnect_attempt", (attempt) => {
    console.log("🔄 Reconnect attempt:", attempt);
  });

  socket.io.on("reconnect", (attempt) => {
    console.log("🔌 Reconnected after", attempt, "attempts");
  });

  socket.on("call_failed", (err) => {
    console.error("Call failed:", err);
  });

  /* ---------- GLOBAL EVENTS ---------- */

  socket.on("force_logout", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("tb_user");

    socket.disconnect();
    socket = null;

    window.location.href = "/";
  });

  socket.on("balance_updated", (data) => {
    const event = new CustomEvent("Luveloop:balance_updated", {
      detail: data,
    });
    window.dispatchEvent(event);
  });

  socket.on("new_notification", (data) => {
    const event = new CustomEvent("Luveloop:new_notification", {
      detail: data,
    });
    window.dispatchEvent(event);
  });

  return socket;
};

/* ---------- BASIC SOCKET HELPERS ---------- */

export const getSocket = () => socket;

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

/* ---------- CHAT EVENTS ---------- */

export const joinChat = (userId) => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error("Socket not connected"));
      return;
    }

    socket.emit("join_chat", { user_id: userId }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const leaveChat = (roomId) => {
  if (socket?.connected) {
    socket.emit("leave_chat", { room_id: roomId });
  }
};

export const sendMessage = (receiverId, content, type = "text", conversationId = null, tempId = null) => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error("Socket not connected"));
      return;
    }

    const payload = { receiver_id: receiverId, content, type };
    if (conversationId) {
      payload.conversation_id = conversationId;
    }
    if (tempId) {
      payload.temp_id = tempId;
    }

    // Debug: payload logged only on error

    socket.emit(
      "message:send",
      payload,
      (response) => {
        // Ack handled by caller
        if (response?.error) {
          console.error("[SOCKET DEBUG] Ack error:", response.error);
          reject(new Error(response.error));
        } else {
          resolve(response);
        }
      }
    );
  });
};

export const sendTyping = (receiverId) => {
  if (socket?.connected) {
    socket.emit("message:typing", { receiver_id: receiverId });
  }
};

export const sendStopTyping = (receiverId) => {
  if (socket?.connected) {
    socket.emit("message:stop-typing", { receiver_id: receiverId });
  }
};

export const markMessageRead = (senderId) => {
  if (socket?.connected) {
    socket.emit("message:read", { sender_id: senderId });
  }
};

export const markMessageDelivered = (messageId, senderId) => {
  if (socket?.connected) {
    socket.emit("message:delivered", { message_id: messageId, sender_id: senderId });
  }
};

/* ---------- CALL EVENTS ---------- */

export const callUser = (receiverId, callType) => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error("Socket not connected"));
      return;
    }

    console.log("Initiating call", {
      targetUserId: receiverId,
      callType: callType
    });

    socket.emit(
      "call_user",
      { user_id: receiverId, call_type: callType },
      (response) => {
        if (response?.error) reject(new Error(response.error));
        else resolve(response);
      }
    );
  });
};

export const answerCall = (callId, answer) => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error("Socket not connected"));
      return;
    }

    socket.emit(
      "call:accept",
      { call_id: callId, answer },
      (response) => {
        if (response?.error) reject(new Error(response.error));
        else resolve(response);
      }
    );
  });
};

export const rejectCall = (callId, reason = "rejected") => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error("Socket not connected"));
      return;
    }

    socket.emit(
      "call:reject",
      { call_id: callId, reason },
      (response) => {
        if (response?.error) reject(new Error(response.error));
        else resolve(response);
      }
    );
  });
};

export const endCall = (callId) => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error("Socket not connected"));
      return;
    }

    socket.emit("call:end", { call_id: callId }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

export const sendIceCandidate = (callId, candidate) => {
  if (socket?.connected) {
    socket.emit("webrtc:ice-candidate", { call_id: callId, candidate });
  }
};

export const sendMediaState = (callId, type, enabled) => {
  if (socket?.connected) {
    socket.emit("call:media-state", { call_id: callId, type, enabled });
  }
};

/* Emit call:initiate - lightweight call signal (no SDP needed upfront) */
export const initiateCall = (targetUserId, type = 'audio') => {
  return new Promise((resolve, reject) => {
    if (!socket || !socket.connected) {
      reject(new Error('Socket not connected'));
      return;
    }
    socket.emit('call:initiate', { targetUserId, type }, (response) => {
      if (response?.error) reject(new Error(response.error));
      else resolve(response);
    });
  });
};

/* ---------- LISTENERS ---------- */

export const onNewMessage = (callback) => {
  socket?.on("message:new", callback);
};
export const offNewMessage = (callback) => {
  socket?.off("message:new", callback);
};

export const onTyping = (callback) => socket?.on("message:typing", callback);
export const onStopTyping = (callback) =>
  socket?.on("message:stop-typing", callback);

export const onMessageDelivered = (callback) => socket?.on("message:delivered", callback);
export const offMessageDelivered = (callback) => socket?.off("message:delivered", callback);

export const onMessageRead = (callback) => socket?.on("message:read", callback);
export const offMessageRead = (callback) => socket?.off("message:read", callback);

export const onIncomingCall = (callback) =>
  socket?.on("incoming_call", callback);

export const offIncomingCall = (callback) =>
  socket?.off("incoming_call", callback);

export const onCallIncoming = (callback) =>
  socket?.on("incoming_call", callback);

export const offCallIncoming = (callback) =>
  socket?.off("incoming_call", callback);

export const onCallAnswered = (callback) =>
  socket?.on("call:accept", callback);

export const onCallRejected = (callback) =>
  socket?.on("call:reject", callback);

export const onCallEnded = (callback) => socket?.on("call:end", callback);

export const onIceCandidate = (callback) =>
  socket?.on("webrtc:ice-candidate", callback);

export const onMediaStateChange = (callback) =>
  socket?.on("call:media-state", callback);

export const removeAllListeners = () => {
  if (!socket) return;

  socket.removeAllListeners("message:new");
  socket.removeAllListeners("message:delivered");
  socket.removeAllListeners("message:read");
  socket.removeAllListeners("message:typing");
  socket.removeAllListeners("message:stop-typing");
  socket.removeAllListeners("incoming_call");
  socket.removeAllListeners("call:accept");
  socket.removeAllListeners("call:reject");
  socket.removeAllListeners("call:end");
  socket.removeAllListeners("webrtc:ice-candidate");
  socket.removeAllListeners("webrtc:offer");
  socket.removeAllListeners("webrtc:answer");
  socket.removeAllListeners("call:media-state");
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
  markMessageRead,
  callUser,
  initiateCall,
  answerCall,
  rejectCall,
  endCall,
  sendIceCandidate,
  sendMediaState,
  onNewMessage,
  offNewMessage,
  onMessageDelivered,
  offMessageDelivered,
  onMessageRead,
  offMessageRead,
  onTyping,
  onStopTyping,
  onIncomingCall,
  offIncomingCall,
  onCallAnswered,
  onCallRejected,
  onCallEnded,
  onIceCandidate,
  onMediaStateChange,
  removeAllListeners
};