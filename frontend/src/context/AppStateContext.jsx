import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../services/api";

const AppStateContext = createContext(null);

export function AppStateProvider({ children }) {
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
  const [deployStatus, setDeployStatus] = useState(null);
  const seenTotals = useRef({ allowed: 0, held: 0, blocked: 0 });

  // Rolling 40-point time-series history
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
      if (list.length > 0) {
        setCases(list);
      }
    } catch (err) {
      console.warn("cases refresh failed", err);
    }
  }, []);

  const refreshStats = useCallback(async () => {
    try {
      const s = await api.stats();
      if (s) {
        setStats((prev) => ({
          evaluated: s.total_evaluations ?? s.evaluated ?? prev.evaluated,
          allowed: s.verdicts?.ALLOW ?? s.allowed ?? prev.allowed,
          held: s.verdicts?.HOLD ?? s.held ?? prev.held,
          blocked: s.verdicts?.BLOCK ?? s.blocked ?? prev.blocked,
          rings: s.rings_known ?? prev.rings,
          dpip: s.dpip?.rings_published ?? prev.dpip,
        }));
        if (s.adaptive_sensitivity != null) {
          setSensitivity(s.adaptive_sensitivity);
        }
      }
    } catch (err) {
      console.warn("stats refresh failed", err);
    }
  }, []);

  const refreshDeployStatus = useCallback(async () => {
    try {
      const data = await api.getDeployStatus();
      setDeployStatus(data);
    } catch (err) {
      console.warn("deploy status refresh failed", err);
    }
  }, []);

  // WebSocket Live Handlers
  const handleWsNewCase = useCallback(
    (newCase, incomingStats) => {
      if (newCase) {
        setCases((prev) => {
          // Avoid duplicate insertion
          const exists = prev.some((c) => c.case_id === newCase.case_id);
          if (exists) {
            return prev.map((c) => (c.case_id === newCase.case_id ? { ...c, ...newCase } : c));
          }
          return [newCase, ...prev.slice(0, 149)];
        });
      }
      if (incomingStats) {
        setStats((prev) => ({
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
          evaluated: prev.evaluated + (result.processed || 0),
          allowed,
          held,
          blocked,
          rings: result.detected_rings ?? prev.rings,
          dpip: prev.dpip,
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
        setSelectedCase((prev) => (prev?.case_id === caseId ? { ...prev, feedback_confirmed: confirmed } : prev));
        await Promise.all([refreshCases(), refreshStats()]);
      } catch (err) {
        console.error("feedback failed", err);
      }
    },
    [refreshCases, refreshStats]
  );

  const updateCaseStatus = useCallback(
    async (caseId, payload) => {
      try {
        const res = await api.updateCaseStatus(caseId, payload);
        const newStatus = res?.new_status || (typeof payload === "string" ? payload.toUpperCase() : payload.status?.toUpperCase());

        setCases((prev) =>
          prev.map((c) => (c.case_id === caseId ? { ...c, status: newStatus, ...(res?.case || {}) } : c))
        );

        setSelectedCase((prev) =>
          prev?.case_id === caseId ? { ...prev, status: newStatus, ...(res?.case || {}) } : prev
        );

        await refreshStats();
        return res;
      } catch (err) {
        console.error("updateCaseStatus failed", err);
        throw err;
      }
    },
    [refreshStats]
  );

  const updateSensitivity = useCallback(async (newVal) => {
    setSensitivity(newVal);
    try {
      await api.updateSensitivity(newVal);
    } catch (err) {
      console.warn("sensitivity update backend call failed", err);
    }
  }, []);

  const openCase = useCallback(async (c) => {
    if (!c) return;
    try {
      const caseId = typeof c === "string" ? c : c.case_id;
      if (caseId) {
        const full = await api.case(caseId);
        setSelectedCase(full || c);
      } else {
        setSelectedCase(c);
      }
    } catch {
      setSelectedCase(c);
    }
  }, []);

  const closeCase = useCallback(() => {
    setSelectedCase(null);
  }, []);

  // Initial load
  useEffect(() => {
    refreshStats();
    refreshCases();
    refreshDeployStatus();
    const timer = setTimeout(() => {
      runSimulation(300, 0.15);
    }, 400);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = {
    stats,
    cases,
    verdictHistory,
    selectedCase,
    busy,
    live: live || connected,
    connected,
    sensitivity,
    deployStatus,
    runSimulation,
    runFederation,
    refreshCases,
    refreshStats,
    refreshDeployStatus,
    openCase,
    closeCase,
    updateCaseStatus,
    handleFeedback,
    setSensitivity,
    updateSensitivity,
  };

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error("useAppState must be used within an AppStateProvider");
  }
  return context;
}
