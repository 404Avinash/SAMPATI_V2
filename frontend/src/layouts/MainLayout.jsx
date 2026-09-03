import React from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/common/Navbar";
import CaseDrawer from "../components/CaseDrawer";
import ToastContainer from "../components/common/ToastContainer";
import { useAppState } from "../context/AppStateContext";

export default function MainLayout() {
  const { selectedCase, closeCase, handleFeedback, deployStatus } = useAppState();

  const shortSha = deployStatus?.commit_sha ? deployStatus.commit_sha.slice(0, 7) : "c28be10";

  return (
    <div className="min-h-screen bg-surface-muted flex flex-col antialiased font-sans text-ink-900 selection:bg-saffron/20 selection:text-ink-900">
      {/* Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Active Page Outlet */}
        <main className="flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-[1400px]">
          <Outlet />
        </main>

        {/* Standard Footer */}
        <footer className="w-full border-t border-hairline bg-white/70 backdrop-blur py-4 mt-auto">
          <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 text-xs text-muted flex flex-col xl:flex-row items-center justify-between gap-4">
            <div className="text-center xl:text-left">
              <span className="font-semibold text-ink-900 font-serif">SAMPATI</span> · AEGIS-UPI — prototype operations console for academic demonstration.
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 xl:gap-4 text-[11px] font-mono">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Privacy-preserving
              </span>
              <span className="hidden sm:inline">·</span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-saffron" />
                Explainable
              </span>
              <span className="hidden sm:inline">·</span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                Human-in-the-loop
              </span>
              <span className="hidden sm:inline">·</span>
              <span className="font-semibold px-1.5 py-0.5 rounded bg-surface-muted border border-hairline text-ink-900">
                {shortSha}
              </span>
              <span className="hidden sm:inline">·</span>
              <span>v2.1.0 · AWS EC2</span>
            </div>
          </div>
        </footer>
      </div>

      {/* Global Slide-Out Case Drawer */}
      <CaseDrawer
        caseData={selectedCase}
        onClose={closeCase}
        onFeedback={handleFeedback}
      />

      {/* Global Toast Notification Container */}
      <ToastContainer />
    </div>
  );
}
