import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppStateProvider } from "./context/AppStateContext";
import MainLayout from "./layouts/MainLayout";
import OverviewPage from "./pages/OverviewPage";
import InvestigationsPage from "./pages/InvestigationsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SystemHealthPage from "./pages/SystemHealthPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            {/* Redirect root to /overview */}
            <Route path="/" element={<Navigate to="/overview" replace />} />

            {/* Core Application Pages */}
            <Route path="/overview" element={<OverviewPage />} />
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
    </AppStateProvider>
  );
}
