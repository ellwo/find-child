import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Layout from "@/components/Layout";
import Dashboard from "./pages/Dashboard";
import Cameras from "./pages/Cameras";
import SavedImages from "./pages/SavedImages";
import Search from "./pages/Search";
import NotFound from "./pages/NotFound";

// Admin pages
import AdminLogin from "./pages/admin/Login";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminBuses from "./pages/admin/Buses";
import AdminParents from "./pages/admin/Parents";
import AdminStudents from "./pages/admin/Students";
import AdminSettings from "./pages/admin/Settings";
import AdminLiveTracking from "./pages/admin/LiveTracking";
import AdminStudentTracking from "./pages/admin/StudentTracking";
import AdminAttendance from "./pages/admin/Attendance";

// Parent pages
import ParentLogin from "./pages/parent/Login";
import ParentDashboard from "./pages/parent/Dashboard";
import ParentStudentTracking from "./pages/parent/StudentTracking";

import "@/i18n/config";

const queryClient = new QueryClient();

// Protected Route Component
const ProtectedRoute = ({ children, requireAdmin = false, requireParent = false }: { 
  children: React.ReactNode; 
  requireAdmin?: boolean; 
  requireParent?: boolean;
}) => {
  const { isAuthenticated, isAdmin, isParent, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">جاري التحميل...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  if (requireParent && !isParent) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Layout><Dashboard /></Layout>} />
              <Route path="/cameras" element={<Layout><Cameras /></Layout>} />
              <Route path="/saved-images" element={<Layout><SavedImages /></Layout>} />
              <Route path="/search" element={<Layout><Search /></Layout>} />

              {/* Admin routes */}
              <Route path="/admin/login" element={<AdminLogin />} />
              <Route
                path="/admin/dashboard"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminDashboard /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/buses"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminBuses /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/parents"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminParents /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/students"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminStudents /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/settings"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminSettings /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/live-tracking"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminLiveTracking /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/students/:id/tracking"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminStudentTracking /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/attendance"
                element={
                  <ProtectedRoute requireAdmin>
                    <Layout><AdminAttendance /></Layout>
                  </ProtectedRoute>
                }
              />

              {/* Parent routes */}
              <Route path="/parent/login" element={<ParentLogin />} />
              <Route
                path="/parent/dashboard"
                element={
                  <ProtectedRoute requireParent>
                    <Layout><ParentDashboard /></Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/parent/students/:id"
                element={
                  <ProtectedRoute requireParent>
                    <Layout><ParentStudentTracking /></Layout>
                  </ProtectedRoute>
                }
              />

              {/* Catch all */}
              <Route path="*" element={<Layout><NotFound /></Layout>} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
