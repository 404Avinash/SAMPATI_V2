import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppState } from "../context/AppStateContext";
import { formatINR } from "../services/api";
import KpiStrip from "../components/KpiStrip";
import VerdictHistoryChart from "../components/VerdictHistoryChart";
import ControlBar from "../components/ControlBar";
import NetworkConstellation from "../components/NetworkConstellation";
import LiveFeed from "../components/LiveFeed";
import VerdictDonut from "../components/VerdictDonut";

export default function OverviewPage() {
  const {
    stats,
    cases,
    verdictHistory,
    busy,
    runSimulation,
    runFederation,
    openCase,
    honeypotAlerts = [],
    dismissHoneypotAlert,
  } = useAppState();

  return (
    <div className="space-y-6 relative">
      {/* Honeypot Red Toast Alert Notifications (Persists for 5 seconds) */}
      <div className="fixed top-20 right-6 z-50 flex flex-col gap-3 pointer-events-none max-w-md w-full px-4 sm:px-0">
        <AnimatePresence>
          {honeypotAlerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.9, transition: { duration: 0.2 } }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="pointer-events-auto bg-rose-700 text-white rounded-lg shadow-2xl border-2 border-rose-400/80 p-4 font-mono relative overflow-hidden"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase tracking-wider">
                  <span className="text-base animate-bounce">🚨</span>
                  <span>Honeypot Interception Trap</span>
                </div>
                <button
                  onClick={() => dismissHoneypotAlert?.(alert.id)}
                  className="text-white/80 hover:text-white text-xs font-bold px-1.5 py-0.5 rounded hover:bg-white/20 transition-colors"
                  title="Dismiss alert"
                >
                  ✕
                </button>
              </div>

              <div className="mt-2 text-xs text-rose-100 space-y-1">
                <p className="text-[11px] text-white/90">
                  Intercepted unauthorized payment directed to designated honeypot trap:
                </p>
                <div className="bg-rose-950/80 text-amber-300 px-2.5 py-1.5 rounded font-mono font-bold text-xs border border-rose-500/40 break-all select-all">
                  {alert.vpa}
                </div>
                {alert.amount ? (
                  <div className="flex items-center justify-between text-[11px] pt-1 text-rose-200">
                    <span>Protected Amount:</span>
                    <span className="font-bold text-white">{formatINR(alert.amount)}</span>
                  </div>
                ) : null}
              </div>

              {/* 5-Second Animated Dismissal Progress Bar */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-rose-950/50">
                <motion.div
                  initial={{ width: "100%" }}
                  animate={{ width: "0%" }}
                  transition={{ duration: 5, ease: "linear" }}
                  className="h-full bg-amber-400"
                />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* KPI Overview Strip */}
      <KpiStrip stats={stats} />

      {/* Real-time Verdict Velocity Chart */}
      <VerdictHistoryChart history={verdictHistory} />

      {/* Simulation & Intelligence Controls */}
      <ControlBar
        onSimulate={runSimulation}
        onFederate={runFederation}
        busy={busy}
      />

      {/* Mule-Network Interactive Fabric */}
      <div className="panel overflow-hidden">
        <div className="panel-header flex items-center justify-between">
          <div className="panel-title">
            <div className="text-[11px] uppercase tracking-wide text-muted font-mono">
              Topology Visualizer
            </div>
            <div className="font-serif font-bold text-ink-900">
              Live Constellation &amp; Mule Rings
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-muted">
            <span className="px-2 py-0.5 rounded bg-surface-muted border border-hairline">
              {cases.length} active rings tracked
            </span>
          </div>
        </div>
        <div className="h-[440px] p-2 bg-[#f8f9fc]">
          <NetworkConstellation cases={cases} onSelectCase={openCase} />
        </div>
      </div>

      {/* Split Bottom Grid: Live Feed + Verdict Mix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 panel overflow-hidden">
          <div className="panel-header flex items-center justify-between">
            <div className="panel-title">
              <div className="text-[11px] uppercase tracking-wide text-muted font-mono">
                Worklist
              </div>
              <div className="font-serif font-bold text-ink-900">
                Flagged Activity Feed
              </div>
            </div>
            <span className="text-xs text-muted font-mono">{cases.length} shown</span>
          </div>
          <div className="h-[420px]">
            <LiveFeed cases={cases} onSelect={openCase} />
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <div className="text-[11px] uppercase tracking-wide text-muted font-mono">
                Telemetry
              </div>
              <div className="font-serif font-bold text-ink-900">Verdict Mix</div>
            </div>
          </div>
          <div className="p-5 flex items-center justify-center">
            <VerdictDonut
              allowed={stats.allowed}
              held={stats.held}
              blocked={stats.blocked}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
