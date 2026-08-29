import React from "react";
import { useAppState } from "../../context/AppStateContext";

export default function Topbar({ onToggleMobile }) {
  const { sensitivity, live, busy, refreshCases, refreshStats } = useAppState();

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-hairline">
      {/* Tricolor accent bar */}
      <div className="h-1 w-full bg-gradient-to-r from-saffron via-white to-verdict-allow" />

      <div className="px-4 md:px-8 py-3 flex items-center justify-between gap-4">
        {/* Left: Mobile hamburger & title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobile}
            className="md:hidden p-2 rounded-md hover:bg-surface-muted text-ink-900 border border-hairline"
            aria-label="Toggle Navigation"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-serif text-lg md:text-xl font-bold text-ink-900 leading-tight">
                SAMPATI Operations Hub
              </h1>
              <span className="hidden sm:inline-block text-[11px] font-mono px-2 py-0.5 rounded bg-surface-muted text-muted border border-hairline font-semibold">
                RBI DPIP Complement
              </span>
            </div>
            <p className="hidden md:block text-xs text-muted">
              Real-time UPI Mule-Network Interception &amp; Explainability Fabric
            </p>
          </div>
        </div>

        {/* Right: Telemetry & Status Badges */}
        <div className="flex items-center gap-3 sm:gap-5">
          {/* Sensitivity Indicator */}
          <div className="text-right hidden xs:block">
            <div className="text-[10px] uppercase text-muted tracking-wide font-mono">
              Adaptive Sensitivity
            </div>
            <div className="font-mono text-sm font-bold text-ink-900">
              {Number(sensitivity || 1.0).toFixed(3)}
            </div>
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => {
              refreshStats();
              refreshCases();
            }}
            disabled={busy}
            className="p-2 rounded-md hover:bg-surface-muted text-muted hover:text-ink-900 border border-hairline transition-colors disabled:opacity-50"
            title="Refresh state"
          >
            <svg
              className={`w-4 h-4 ${busy ? "animate-spin text-saffron" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>

          {/* Live Status Pill */}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold font-mono border ${
              live
                ? "bg-verdict-allowBg text-verdict-allow border-verdict-allow/30"
                : "bg-surface-muted text-muted border-hairline"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                live ? "bg-verdict-allow animate-pulse" : "bg-muted"
              }`}
            />
            {live ? "LIVE STREAM" : "IDLE"}
          </span>
        </div>
      </div>
    </header>
  );
}
