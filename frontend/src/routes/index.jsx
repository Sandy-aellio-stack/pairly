import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

// Landing Page
import Landing from '@/pages/Landing';

// Auth Pages
import Login from '@/pages/auth/Login';
import Signup from '@/pages/auth/Signup';
import TwoFA from '@/pages/auth/TwoFA';

// User Pages
import Home from '@/pages/Home';
import Discovery from '@/pages/Discovery';
import Profile from '@/pages/Profile';
import EditProfile from '@/pages/EditProfile';
import Settings from '@/pages/Settings';

// Messaging
import ChatList from '@/pages/messaging/ChatList';
import ChatRoom from '@/pages/messaging/ChatRoom';

// Payments
import BuyCredits from '@/pages/payments/BuyCredits';
import PaymentSuccess from '@/pages/payments/PaymentSuccess';
import PaymentFailed from '@/pages/payments/PaymentFailed';

// Creator Dashboard
import CreatorDashboard from '@/pages/creator/Dashboard';
import Earnings from '@/pages/creator/Earnings';
import Payouts from '@/pages/creator/Payouts';

// Admin Dashboard
import AdminOverview from '@/pages/admin/Overview';
import AdminUsers from '@/pages/admin/Users';
import AdminSecurity from '@/pages/admin/Security';

const PrivateRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (isAuthenticated) {
    return <Navigate to="/home" replace />;
  }
  
  return children;
};

const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/2fa" element={<TwoFA />} />

      {/* Private Routes */}
      <Route
        path="/home"
        element={
          <PrivateRoute>
            <Home />
          </PrivateRoute>
        }
      />
      <Route
        path="/discovery"
        element={
          <PrivateRoute>
            <Discovery />
          </PrivateRoute>
        }
      />
      <Route
        path="/profile/:userId"
        element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        }
      />
      <Route
        path="/profile/edit"
        element={
          <PrivateRoute>
            <EditProfile />
          </PrivateRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <PrivateRoute>
            <Settings />
          </PrivateRoute>
        }
      />

      {/* Messaging */}
      <Route
        path="/messages"
        element={
          <PrivateRoute>
            <ChatList />
          </PrivateRoute>
        }
      />
      <Route
        path="/messages/:userId"
        element={
          <PrivateRoute>
            <ChatRoom />
          </PrivateRoute>
        }
      />

      {/* Payments */}
      <Route
        path="/buy-credits"
        element={
          <PrivateRoute>
            <BuyCredits />
          </PrivateRoute>
        }
      />
      <Route
        path="/payment/success"
        element={
          <PrivateRoute>
            <PaymentSuccess />
          </PrivateRoute>
        }
      />
      <Route
        path="/payment/failed"
        element={
          <PrivateRoute>
            <PaymentFailed />
          </PrivateRoute>
        }
      />

      {/* Creator Dashboard */}
      <Route
        path="/creator/dashboard"
        element={
          <PrivateRoute allowedRoles={['creator']}>
            <CreatorDashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/creator/earnings"
        element={
          <PrivateRoute allowedRoles={['creator']}>
            <Earnings />
          </PrivateRoute>
        }
      />
      <Route
        path="/creator/payouts"
        element={
          <PrivateRoute allowedRoles={['creator']}>
            <Payouts />
          </PrivateRoute>
        }
      />

      {/* Admin Dashboard */}
      <Route
        path="/admin"
        element={
          <PrivateRoute allowedRoles={['admin']}>
            <AdminOverview />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <PrivateRoute allowedRoles={['admin']}>
            <AdminUsers />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin/security"
        element={
          <PrivateRoute allowedRoles={['admin']}>
            <AdminSecurity />
          </PrivateRoute>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRoutes;