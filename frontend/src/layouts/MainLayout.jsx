import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/common/Sidebar";
import Topbar from "../components/common/Topbar";
import CaseDrawer from "../components/CaseDrawer";
import { useAppState } from "../context/AppStateContext";

export default function MainLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { selectedCase, closeCase, handleFeedback } = useAppState();

  return (
    <div className="min-h-screen bg-surface-muted flex flex-col antialiased font-sans text-ink-900 selection:bg-saffron/20 selection:text-ink-900">
      <div className="flex flex-1 relative">
        {/* Persistent Responsive Sidebar */}
        <Sidebar
          mobileOpen={mobileOpen}
          onCloseMobile={() => setMobileOpen(false)}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Persistent Topbar */}
          <Topbar onToggleMobile={() => setMobileOpen((prev) => !prev)} />

          {/* Active Page Outlet */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
            <Outlet />
          </main>

          {/* Standard Footer */}
          <footer className="w-full border-t border-hairline bg-white/70 backdrop-blur py-4 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-xs text-muted flex flex-col sm:flex-row items-center justify-between gap-2">
              <div>
                <span className="font-semibold text-ink-900 font-serif">SAMPATI</span> · AEGIS-UPI — prototype operations console for academic demonstration.
              </div>
              <div className="flex items-center gap-4 text-[11px] font-mono">
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Privacy-preserving
                </span>
                <span>·</span>
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-saffron" />
                  Explainable
                </span>
                <span>·</span>
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Human-in-the-loop
                </span>
              </div>
            </div>
          </footer>
        </div>
      </div>

      {/* Global Slide-Out Case Drawer */}
      <CaseDrawer
        caseData={selectedCase}
        onClose={closeCase}
        onFeedback={handleFeedback}
      />
    </div>
  );
}
