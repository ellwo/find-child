import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import Layout from "@/components/Layout";
import Dashboard from "./pages/Dashboard";
import Cameras from "./pages/Cameras";
import SavedImages from "./pages/SavedImages";
import Search from "./pages/Search";
import Login from "./pages/Login";
import ReportMissing from "./pages/ReportMissing";
import TrackReport from "./pages/TrackReport";
import AdminReports from "./pages/AdminReports";
import NotFound from "./pages/NotFound";
import "@/i18n/config";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Public routes without layout */}
            <Route path="/login" element={<Login />} />
            
            {/* Public routes with layout */}
            <Route path="/report" element={<Layout><ReportMissing /></Layout>} />
            <Route path="/track" element={<Layout><TrackReport /></Layout>} />
            
            {/* Protected routes with layout */}
            <Route path="/" element={<Layout><Dashboard /></Layout>} />
            <Route path="/cameras" element={<Layout><Cameras /></Layout>} />
            <Route path="/saved-images" element={<Layout><SavedImages /></Layout>} />
            <Route path="/search" element={<Layout><Search /></Layout>} />
            <Route path="/admin/reports" element={<Layout><AdminReports /></Layout>} />
            
            {/* Catch-all route */}
            <Route path="*" element={<Layout><NotFound /></Layout>} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
