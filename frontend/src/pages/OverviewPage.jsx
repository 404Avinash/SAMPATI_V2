import React from "react";
import { useAppState } from "../context/AppStateContext";
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
  } = useAppState();

  return (
    <div className="space-y-6">
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
