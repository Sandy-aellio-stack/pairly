import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

// Landing & Public Pages
import Landing from '@/pages/Landing';
import Features from '@/pages/Features';
import Safety from '@/pages/Safety';
import Support from '@/pages/Support';
import Pricing from '@/pages/Pricing';
import Creators from '@/pages/Creators';

// Auth Pages
import Login from '@/pages/auth/Login';
import Signup from '@/pages/auth/Signup';
import TwoFA from '@/pages/auth/TwoFA';

// User Pages
import Home from '@/pages/Home';
import Discovery from '@/pages/Discovery';
import SnapMap from '@/pages/SnapMap';
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
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-amber-50 to-pink-50">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-400 to-pink-500 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <svg className="h-8 w-8 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/home" replace />;
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
      {/* Public Pages (accessible to all) */}
      <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
      <Route path="/features" element={<Features />} />
      <Route path="/safety" element={<Safety />} />
      <Route path="/support" element={<Support />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/creators" element={<Creators />} />

      {/* Auth Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/2fa" element={<TwoFA />} />

      {/* Private Routes - Main App */}
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
        path="/map"
        element={
          <PrivateRoute>
            <SnapMap />
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
