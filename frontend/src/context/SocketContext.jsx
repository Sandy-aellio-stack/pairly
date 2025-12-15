import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useAuth } from './AuthContext';

const SocketContext = createContext(null);

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within SocketProvider');
  }
  return context;
};

export const SocketProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!isAuthenticated || !user) return;

    const wsUrl = import.meta.env.VITE_BACKEND_URL.replace('https', 'wss').replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/api/messages/ws/${user.id}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      
      // Send auth token
      const token = localStorage.getItem('access_token');
      ws.send(JSON.stringify({ token }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'new_message') {
        setMessages((prev) => [...prev, data]);
      } else if (data.type === 'connected') {
        console.log('WebSocket authenticated');
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.message);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    socketRef.current = ws;
    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [isAuthenticated, user]);

  const sendMessage = (recipientId, content) => {
    if (socket && connected) {
      socket.send(
        JSON.stringify({
          type: 'chat_message',
          recipient_id: recipientId,
          content,
        })
      );
    }
  };

  const value = {
    socket,
    connected,
    messages,
    sendMessage,
  };

  return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
};