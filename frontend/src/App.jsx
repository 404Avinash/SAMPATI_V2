import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppStateProvider } from "./context/AppStateContext";
import { ToastProvider } from "./context/ToastContext";
import MainLayout from "./layouts/MainLayout";
import ScrollToTop from "./components/common/ScrollToTop";
import OverviewPage from "./pages/OverviewPage";
import ThreatIntelPage from "./pages/ThreatIntelPage";
import TopologyPage from "./pages/TopologyPage";
import InvestigationsPage from "./pages/InvestigationsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SystemHealthPage from "./pages/SystemHealthPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <AppStateProvider>
      <ToastProvider>
        <BrowserRouter>
          <ScrollToTop />
          <Routes>
            <Route element={<MainLayout />}>
              {/* Redirect root to /overview */}
              <Route path="/" element={<Navigate to="/overview" replace />} />

              {/* Core Application Pages */}
              <Route path="/overview" element={<OverviewPage />} />
              <Route path="/threat-intel" element={<ThreatIntelPage />} />
              <Route path="/topology" element={<TopologyPage />} />
              <Route path="/topology/:viewMode" element={<TopologyPage />} />
              <Route path="/investigations" element={<InvestigationsPage />} />
              <Route path="/investigations/:caseId" element={<InvestigationsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/health" element={<SystemHealthPage />} />
              <Route path="/system-health" element={<Navigate to="/health" replace />} />
              <Route path="/settings" element={<SettingsPage />} />

              {/* Fallback Catch-All Route */}
              <Route path="*" element={<Navigate to="/overview" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AppStateProvider>
  );
}
