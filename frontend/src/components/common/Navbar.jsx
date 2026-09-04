import React from "react";
import { NavLink } from "react-router-dom";
import { useAppState } from "../../context/AppStateContext";
import { useToast } from "../../context/ToastContext";

const NAV_ITEMS = [
  {
    to: "/overview",
    label: "Overview",
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
  },
  {
    to: "/threat-intel",
    label: "Threat Intelligence",
    badgeKey: "threats",
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    to: "/investigations",
    label: "Investigations",
    badgeKey: "investigations",
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  {
    to: "/analytics",
    label: "Analytics",
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    to: "/health",
    label: "System Health",
    hasPulse: true,
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    to: "/settings",
    label: "Settings",
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

export default function Navbar() {
  const { toast } = useToast();
  const { cases, stats, live, busy, refreshCases, refreshStats, sensitivity } = useAppState();

  const handleRefreshTelemetry = () => {
    refreshStats();
    refreshCases();
    toast.info("Platform metrics & case records refreshed");
  };

  const openCasesCount =
    stats?.open_cases ??
    stats?.cases?.open ??
    cases.filter(
      (c) =>
        (c.status || "OPEN") === "OPEN" &&
        c.status !== "RESOLVED" &&
        c.status !== "DISMISSED"
    ).length;

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-hairline shadow-sm">
      {/* Tricolor accent bar */}
      <div className="h-1 w-full bg-gradient-to-r from-saffron via-white to-verdict-allow" />

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 shrink-0 mr-4">
            <div className="w-8 h-8 rounded-lg bg-ink-900 flex items-center justify-center shadow-glow shrink-0">
              <img src="/shield.svg" alt="SAMPATI" className="w-5 h-5" />
            </div>
            <div className="hidden sm:block">
              <div className="font-serif font-bold text-ink-900 tracking-tight flex items-center gap-1.5 leading-none text-lg">
                SAMPATI Operations Hub
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-saffron/10 text-saffron font-bold ml-1 hidden lg:inline-block">
                  V2
                </span>
              </div>
            </div>
          </div>

          {/* Center Navigation Links (Desktop) */}
          <nav className="hidden md:flex flex-1 items-center justify-center gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `group relative flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-surface-muted text-ink-900 shadow-sm border border-hairline"
                      : "text-muted hover:bg-surface-muted/50 hover:text-ink-900 border border-transparent"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className={isActive ? "text-saffron-light" : "group-hover:text-ink-900"}>
                      {item.icon}
                      {item.hasPulse && (
                        <span className="absolute top-1 left-2 w-2 h-2 rounded-full bg-emerald-500 animate-pulse ring-2 ring-white" />
                      )}
                    </div>
                    <span>{item.label}</span>
                    {item.badgeKey === "investigations" && openCasesCount > 0 && (
                      <span className={`ml-1 px-1.5 py-0.5 text-[10px] font-mono font-bold rounded-full ${
                        isActive ? "bg-rose-500 text-white" : "bg-rose-100 text-rose-700"
                      }`}>
                        {openCasesCount}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Right Status / Telemetry */}
          <div className="flex items-center gap-3 shrink-0 ml-auto">
            <div className="text-right hidden xl:block mr-2">
              <div className="text-[10px] uppercase text-muted tracking-wide font-mono">Sensitivity</div>
              <div className="font-mono text-sm font-bold text-ink-900">{Number(sensitivity || 1.0).toFixed(3)}</div>
            </div>

            <button
              onClick={handleRefreshTelemetry}
              disabled={busy}
              className="p-2 rounded-md hover:bg-surface-muted text-muted hover:text-ink-900 border border-hairline transition-colors disabled:opacity-50"
              title="Refresh Data"
            >
               <svg className={`w-4 h-4 ${busy ? "animate-spin text-saffron" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
               </svg>
            </button>

            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold font-mono border ${
                live ? "bg-verdict-allowBg text-verdict-allow border-verdict-allow/30" : "bg-surface-muted text-muted border-hairline"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${live ? "bg-verdict-allow animate-pulse" : "bg-muted"}`} />
              <span className="hidden sm:inline">{live ? "LIVE STREAM" : "IDLE"}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Mobile Nav Scroll */}
      <div className="md:hidden overflow-x-auto border-t border-hairline bg-surface-muted/30 pb-1" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
         <nav className="flex items-center px-4 py-2 gap-2 min-w-max">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium ${
                    isActive ? "bg-white border border-hairline text-ink-900 shadow-sm" : "text-muted hover:text-ink-900"
                  }`
                }
              >
                 {item.icon}
                 {item.label}
                 {item.badgeKey === "investigations" && openCasesCount > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 text-[9px] font-mono font-bold rounded-full bg-rose-500 text-white">
                      {openCasesCount}
                    </span>
                  )}
              </NavLink>
            ))}
         </nav>
      </div>
    </header>
  );
}
