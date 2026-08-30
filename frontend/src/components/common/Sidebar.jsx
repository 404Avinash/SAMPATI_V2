import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAppState } from "../../context/AppStateContext";

const NAV_ITEMS = [
  {
    to: "/overview",
    label: "Overview",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
        />
      </svg>
    ),
    description: "Live Constellation & Feed",
  },
  {
    to: "/investigations",
    label: "Investigations",
    badgeKey: "investigations",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
    ),
    description: "Triage & Case Dossiers",
  },
  {
    to: "/analytics",
    label: "Analytics",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    description: "Trends & Mule Intelligence",
  },
  {
    to: "/health",
    label: "System Health",
    hasPulse: true,
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
    description: "Latency & SRE Telemetry",
  },
  {
    to: "/settings",
    label: "Settings",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.75}
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    description: "Sensitivity & CI/CD Status",
  },
];

export default function Sidebar({ mobileOpen, onCloseMobile }) {
  const { cases, live, deployStatus } = useAppState();

  const [collapsed, setCollapsed] = useState(() => {
    try {
      const stored = localStorage.getItem("sampati_sidebar_collapsed");
      return stored === "true";
    } catch {
      return false;
    }
  });

  const toggleCollapse = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("sampati_sidebar_collapsed", String(next));
      } catch (e) {
        // ignore storage errors
      }
      return next;
    });
  };

  const flaggedCount = cases.filter(
    (c) =>
      (c.verdict === "HOLD" || c.verdict === "BLOCK" || (c.risk_score && c.risk_score >= 50)) &&
      c.status !== "REVIEWED" &&
      c.status !== "RESOLVED" &&
      c.status !== "DISMISSED"
  ).length;

  const shortSha = deployStatus?.commit_sha
    ? deployStatus.commit_sha.slice(0, 7)
    : "c28be10";

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-ink-900/60 backdrop-blur-sm md:hidden transition-opacity"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:sticky top-0 h-screen z-40 flex flex-col bg-white border-r border-hairline transition-all duration-300 ease-in-out ${
          collapsed ? "w-20" : "w-64"
        } ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-hairline shrink-0">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-lg bg-ink-900 flex items-center justify-center shrink-0 shadow-glow">
              <img src="/shield.svg" alt="SAMPATI" className="w-6 h-6" />
            </div>
            {!collapsed && (
              <div className="leading-tight truncate">
                <div className="font-serif font-bold text-ink-900 tracking-tight flex items-center gap-1.5">
                  SAMPATI
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-saffron/10 text-saffron font-bold">
                    V2
                  </span>
                </div>
                <div className="text-[10px] text-muted uppercase tracking-wider font-mono truncate">
                  AEGIS · UPI Core
                </div>
              </div>
            )}
          </div>

          {/* Mobile Close Button */}
          <button
            onClick={onCloseMobile}
            className="md:hidden text-muted hover:text-ink-900 p-1.5 rounded"
          >
            ✕
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => onCloseMobile?.()}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-ink-900 text-white shadow-sm"
                    : "text-ink-800 hover:bg-surface-muted hover:text-ink-900"
                } ${collapsed ? "justify-center" : ""}`
              }
              title={collapsed ? `${item.label} — ${item.description}` : undefined}
            >
              {({ isActive }) => (
                <>
                  <div
                    className={`relative shrink-0 ${
                      isActive ? "text-saffron-light" : "text-muted group-hover:text-ink-900"
                    }`}
                  >
                    {item.icon}
                    {item.hasPulse && (
                      <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-500 animate-pulse ring-2 ring-white" />
                    )}
                  </div>

                  {!collapsed && (
                    <div className="flex-1 flex items-center justify-between truncate">
                      <span className="truncate">{item.label}</span>
                      {item.badgeKey === "investigations" && flaggedCount > 0 && (
                        <span
                          className={`ml-2 px-1.5 py-0.5 text-[11px] font-mono font-bold rounded-full ${
                            isActive
                              ? "bg-rose-500 text-white"
                              : "bg-rose-100 text-rose-700 border border-rose-200"
                          }`}
                        >
                          {flaggedCount}
                        </span>
                      )}
                    </div>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer Meta & Collapse Toggle */}
        <div className="p-3 border-t border-hairline shrink-0 space-y-2 bg-surface-muted/40">
          {!collapsed && (
            <div className="px-2 py-1.5 rounded bg-white border border-hairline text-xs font-mono flex items-center justify-between text-muted">
              <span className="flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    live ? "bg-emerald-500 animate-pulse" : "bg-muted"
                  }`}
                />
                <span>{live ? "WS Stream Active" : "Offline"}</span>
              </span>
              <span className="text-[10px] text-ink-900 font-semibold px-1 rounded bg-surface-muted">
                {shortSha}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between px-1">
            {!collapsed && (
              <span className="text-[11px] text-muted font-mono">v2.1.0 · AWS EC2</span>
            )}
            <button
              onClick={toggleCollapse}
              className="p-1.5 rounded-md hover:bg-surface-muted text-muted hover:text-ink-900 transition-colors ml-auto"
              title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            >
              <svg
                className={`w-4 h-4 transition-transform duration-200 ${
                  collapsed ? "rotate-180" : ""
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
