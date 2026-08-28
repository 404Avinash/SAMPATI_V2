import React, { useCallback, useEffect, useRef, useState } from "react";
import Masthead from "./components/Masthead";
import KpiStrip from "./components/KpiStrip";
import VerdictHistoryChart from "./components/VerdictHistoryChart";
import ControlBar from "./components/ControlBar";
import NetworkConstellation from "./components/NetworkConstellation";
import LiveFeed from "./components/LiveFeed";
import VerdictDonut from "./components/VerdictDonut";
import CaseDrawer from "./components/CaseDrawer";
import { useWebSocket } from "./hooks/useWebSocket";
import { api } from "./services/api";

export default function App() {
  const [stats, setStats] = useState({
    evaluated: 0,
    allowed: 0,
    held: 0,
    blocked: 0,
    rings: 0,
    dpip: 0,
  });
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(false);
  const [sensitivity, setSensitivity] = useState(1.0);
  const seenTotals = useRef({ allowed: 0, held: 0, blocked: 0 });

  // Time-series history sliding buffer for Recharts VerdictHistoryChart (capped to last 40 points)
  const [verdictHistory, setVerdictHistory] = useState([
    {
      time: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      timestamp: Date.now(),
      ALLOW: 0,
      HOLD: 0,
      BLOCK: 0,
      allowed: 0,
      held: 0,
      blocked: 0,
    },
  ]);

  const appendVerdictHistory = useCallback((currentCounts) => {
    const timeStr = new Date().toLocaleTimeString("en-IN", { hour12: false });
    const allowVal = currentCounts.ALLOW ?? currentCounts.allowed ?? 0;
    const holdVal = currentCounts.HOLD ?? currentCounts.held ?? 0;
    const blockVal = currentCounts.BLOCK ?? currentCounts.blocked ?? 0;

    setVerdictHistory((prev) => {
      const newPoint = {
        time: timeStr,
        timestamp: Date.now(),
        ALLOW: allowVal,
        HOLD: holdVal,
        BLOCK: blockVal,
        allowed: allowVal,
        held: holdVal,
        blocked: blockVal,
      };
      const updated = [...prev, newPoint];
      return updated.slice(-40);
    });
  }, []);

  const refreshCases = useCallback(async () => {
    try {
      const data = await api.cases();
      const list = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
        ? data.items
        : Array.isArray(data?.cases)
        ? data.cases
        : [];
      setCases(list);
    } catch (err) {
      console.error("cases refresh failed", err);
    }
  }, []);

  const refreshStats = useCallback(async () => {
    try {
      const s = await api.stats();
      setStats((prev) => ({
        ...prev,
        rings: s.rings_known ?? prev.rings,
        dpip: s.dpip?.rings_published ?? prev.dpip,
      }));
      setSensitivity(s.adaptive_sensitivity ?? 1.0);
    } catch (err) {
      console.error("stats refresh failed", err);
    }
  }, []);

  // WebSocket Live Event Handlers
  const handleWsNewCase = useCallback(
    (newCase, incomingStats) => {
      if (newCase) {
        setCases((prev) => [newCase, ...prev.slice(0, 99)]);
      }
      if (incomingStats) {
        setStats((prev) => ({
          ...prev,
          evaluated: incomingStats.evaluated ?? prev.evaluated,
          allowed: incomingStats.allowed ?? prev.allowed,
          held: incomingStats.held ?? prev.held,
          blocked: incomingStats.blocked ?? prev.blocked,
          rings: incomingStats.rings ?? prev.rings,
          dpip: incomingStats.dpip ?? prev.dpip,
        }));
        appendVerdictHistory(incomingStats);
      }
    },
    [appendVerdictHistory]
  );

  const handleWsStatsUpdate = useCallback(
    (incomingStats) => {
      if (!incomingStats) return;
      setStats((prev) => ({
        ...prev,
        evaluated: incomingStats.evaluated ?? prev.evaluated,
        allowed: incomingStats.allowed ?? prev.allowed,
        held: incomingStats.held ?? prev.held,
        blocked: incomingStats.blocked ?? prev.blocked,
        rings: incomingStats.rings ?? prev.rings,
        dpip: incomingStats.dpip ?? prev.dpip,
      }));
      appendVerdictHistory(incomingStats);
    },
    [appendVerdictHistory]
  );

  const { connected } = useWebSocket({
    onNewCase: handleWsNewCase,
    onStatsUpdate: handleWsStatsUpdate,
    onOpen: () => setLive(true),
    onClose: () => setLive(false),
    enabled: true,
  });

  const runSimulation = useCallback(
    async (count, fraudRatio) => {
      setBusy(true);
      setLive(true);
      try {
        const result = await api.simulate(count, fraudRatio);
        const v = result.verdicts || {};
        const allowed = seenTotals.current.allowed + (v.ALLOW || 0);
        const held = seenTotals.current.held + (v.HOLD || 0);
        const blocked = seenTotals.current.blocked + (v.BLOCK || 0);
        seenTotals.current = { allowed, held, blocked };

        setStats((prev) => ({
          ...prev,
          evaluated: prev.evaluated + (result.processed || 0),
          allowed,
          held,
          blocked,
          rings: result.detected_rings ?? prev.rings,
        }));

        appendVerdictHistory({ allowed, held, blocked });
        await Promise.all([refreshCases(), refreshStats()]);
      } catch (err) {
        console.error("simulate failed", err);
      } finally {
        setBusy(false);
      }
    },
    [refreshCases, refreshStats, appendVerdictHistory]
  );

  const runFederation = useCallback(async () => {
    setBusy(true);
    try {
      await api.runFederation();
      await Promise.all([refreshCases(), refreshStats()]);
    } catch (err) {
      console.error("federation failed", err);
    } finally {
      setBusy(false);
    }
  }, [refreshCases, refreshStats]);

  const handleFeedback = useCallback(
    async (caseId, confirmed) => {
      try {
        await api.feedback(caseId, confirmed);
        setSelectedCase(null);
        await Promise.all([refreshCases(), refreshStats()]);
      } catch (err) {
        console.error("feedback failed", err);
      }
    },
    [refreshCases, refreshStats]
  );

  const openCase = useCallback(async (c) => {
    if (!c) return;
    try {
      const caseId = c.case_id || (typeof c === "string" ? c : null);
      if (caseId) {
        const full = await api.case(caseId);
        setSelectedCase(full);
      } else {
        setSelectedCase(c);
      }
    } catch {
      setSelectedCase(c);
    }
  }, []);

  // Auto-run a demo simulation on first load so the dashboard is never empty.
  useEffect(() => {
    refreshStats();
    refreshCases();
    const timer = setTimeout(() => {
      runSimulation(300, 0.15);
    }, 500);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-surface-muted pb-10">
      <Masthead sensitivity={sensitivity} live={live || connected} />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <KpiStrip stats={stats} />

        <VerdictHistoryChart history={verdictHistory} />

        <ControlBar onSimulate={runSimulation} onFederate={runFederation} busy={busy} />

        <div className="panel">
          <div className="panel-header flex items-center justify-between">
            <div className="panel-title">
              <div className="text-[11px] uppercase tracking-wide text-muted">Mule-Network Fabric</div>
              <div className="font-serif font-semibold text-ink-900">Live Constellation</div>
            </div>
            <span className="text-xs text-muted font-mono">{cases.length} rings tracked</span>
          </div>
          <div className="h-[420px] p-3">
            <NetworkConstellation cases={cases} onSelectCase={openCase} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 panel">
            <div className="panel-header flex items-center justify-between">
              <div className="panel-title">
                <div className="text-[11px] uppercase tracking-wide text-muted">Worklist</div>
                <div className="font-serif font-semibold text-ink-900">Flagged Activity Feed</div>
              </div>
              <span className="text-xs text-muted">{cases.length} shown</span>
            </div>
            <div className="h-[420px]">
              <LiveFeed cases={cases} onSelect={openCase} />
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div className="panel-title">
                <div className="text-[11px] uppercase tracking-wide text-muted">Distribution</div>
                <div className="font-serif font-semibold text-ink-900">Verdict Mix</div>
              </div>
            </div>
            <div className="p-4">
              <VerdictDonut allowed={stats.allowed} held={stats.held} blocked={stats.blocked} />
            </div>
          </div>
        </div>
      </main>

      <footer className="max-w-7xl mx-auto px-6 py-4 text-xs text-muted border-t border-hairline mt-6">
        SAMPATI · AEGIS-UPI — prototype operations console for academic demonstration.
        <span className="float-right space-x-3">
          <span>Privacy-preserving</span>
          <span>Explainable</span>
          <span>Human-in-the-loop</span>
        </span>
      </footer>

      <CaseDrawer caseData={selectedCase} onClose={() => setSelectedCase(null)} onFeedback={handleFeedback} />
    </div>
  );
}
