import { useEffect } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation
} from 'react-router-dom';
import { Toaster } from 'sonner';
import useAuthStore from '@/store/authStore';
import useAdminStore from '@/store/adminStore';

// Pages
import LoginPage from '@/pages/LoginPage';
import SignupPage from '@/pages/SignupPage';
import VerifyOTPPage from '@/pages/VerifyOTPPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import TermsPage from '@/pages/TermsPage';
import PrivacyPage from '@/pages/PrivacyPage';
import AboutPage from '@/pages/AboutPage';
import ContactPage from '@/pages/ContactPage';
import HelpCenterPage from '@/pages/HelpCenterPage';
import BlogPage from '@/pages/BlogPage';
import CareersPage from '@/pages/CareersPage';

// Dashboard Pages
import DashboardLayout from '@/pages/dashboard/DashboardLayout';
import HomePage from '@/pages/dashboard/HomePage';
import ChatPage from '@/pages/dashboard/ChatPage';
import NearbyPage from '@/pages/dashboard/NearbyPage';
import ProfilePage from '@/pages/dashboard/ProfilePage';
import CreditsPage from '@/pages/dashboard/CreditsPage';
import SettingsPage from '@/pages/dashboard/SettingsPage';
import CallPage from '@/pages/dashboard/CallPage';
import NotificationsPage from '@/pages/dashboard/NotificationsPage';
import ProfileViewerPage from '@/pages/dashboard/ProfileViewerPage';

// Admin Pages
import AdminLayout from '@/pages/admin/AdminLayout';
import AdminLoginPage from '@/pages/admin/AdminLoginPage';
import AdminDashboardPage from '@/pages/admin/DashboardPage';
import UserManagementPage from '@/pages/admin/UserManagementPage';
import ModerationPage from '@/pages/admin/ModerationPage';
import AnalyticsPage from '@/pages/admin/AnalyticsPage';
import AdminSettingsPage from '@/pages/admin/AdminSettingsPage';
import AdminLogPage from '@/pages/admin/AdminLogPage';

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// Public Route wrapper (redirect to dashboard if logged in)
function PublicRoute({ children }) {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

// Admin Protected Route wrapper
function AdminProtectedRoute({ children }) {
  const { isAuthenticated } = useAdminStore();

  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
}

// Redirect to static landing page if hitting root in React
function LandingRedirect() {
  useEffect(() => {
    window.location.href = '/';
  }, []);
  return null;
}

function App() {
  const { initialize, isLoading } = useAuthStore();
  const { initialize: initializeAdmin } = useAdminStore();

  useEffect(() => {
    initialize();
    initializeAdmin();
  }, [initialize, initializeAdmin]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="w-12 h-12 border-4 border-[#E9D5FF] border-t-[#0F172A] rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <ScrollToTop />
      <Toaster position="top-center" richColors />

      <Routes>
        {/* Root Landing Page - handled by static HTML via full page reload */}
        <Route path="/" element={<LandingRedirect />} />

        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={
          <PublicRoute>
            <SignupPage />
          </PublicRoute>
        } />
        <Route path="/verify-otp" element={<VerifyOTPPage />} />
        <Route path="/forgot-password" element={
          <PublicRoute>
            <ForgotPasswordPage />
          </PublicRoute>
        } />
        <Route path="/reset-password" element={
          <PublicRoute>
            <ResetPasswordPage />
          </PublicRoute>
        } />

        {/* Info Pages */}
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/help" element={<HelpCenterPage />} />
        <Route path="/blog" element={<BlogPage />} />
        <Route path="/careers" element={<CareersPage />} />
        <Route path="/press" element={<AboutPage />} /> {/* Reuse About for Press */}

        {/* Protected Dashboard Routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route index element={<HomePage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="nearby" element={<NearbyPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="profile/:userId" element={<ProfileViewerPage />} />
          <Route path="credits" element={<CreditsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* Call Page - Full Screen */}
        <Route path="/call/:userId" element={
          <ProtectedRoute>
            <CallPage />
          </ProtectedRoute>
        } />

        {/* Admin Login */}
        <Route path="/admin/login" element={<AdminLoginPage />} />

        {/* Admin Routes */}
        <Route path="/admin" element={
          <AdminProtectedRoute>
            <AdminLayout />
          </AdminProtectedRoute>
        }>
          <Route index element={<AdminDashboardPage />} />
          <Route path="users" element={<UserManagementPage />} />
          <Route path="moderation" element={<ModerationPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="settings" element={<AdminSettingsPage />} />
          <Route path="logs" element={<AdminLogPage />} />
        </Route>

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
