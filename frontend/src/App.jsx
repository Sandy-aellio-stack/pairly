import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { SocketProvider } from '@/context/SocketContext';
import { Toaster } from '@/components/ui/sonner';
import AppRoutes from '@/routes';
import '@/App.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SocketProvider>
          <AppRoutes />
          <Toaster />
        </SocketProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
