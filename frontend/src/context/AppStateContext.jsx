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
    honeypot_hits: 0,
    honeypot_hits_24h: 0,
    rings: 0,
    dpip: 0,
  });
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(false);
  const [sensitivity, setSensitivity] = useState(1.0);
  const [deployStatus, setDeployStatus] = useState(null);
  const [autoFeedActive, setAutoFeedActive] = useState(false);
  const [autoFeedTps, setAutoFeedTps] = useState(10.0);
  const [autoFeedStats, setAutoFeedStats] = useState({
    active: false,
    rate_tps: 10.0,
    total_generated: 0,
    total_flagged: 0,
  });
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
        const hpVal =
          s.honeypot_hits_24h ??
          s.honeypot_hits ??
          s.honeypots?.total_hits ??
          s.honeypots?.hits_24h ??
          0;
        setStats((prev) => ({
          evaluated: s.total_evaluations ?? s.evaluated ?? prev.evaluated,
          allowed: s.verdicts?.ALLOW ?? s.allowed ?? prev.allowed,
          held: s.verdicts?.HOLD ?? s.held ?? prev.held,
          blocked: s.verdicts?.BLOCK ?? s.blocked ?? prev.blocked,
          honeypot_hits: hpVal !== undefined && hpVal !== null ? hpVal : prev.honeypot_hits,
          honeypot_hits_24h: hpVal !== undefined && hpVal !== null ? hpVal : prev.honeypot_hits_24h,
          rings: s.rings_known ?? s.rings ?? prev.rings,
          dpip: s.dpip?.rings_published ?? s.dpip ?? prev.dpip,
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

  const refreshAutoFeedStatus = useCallback(async () => {
    try {
      const data = await api.getAutoFeedStatus();
      if (data && typeof data === "object") {
        if (typeof data.active === "boolean") {
          setAutoFeedActive(data.active);
        }
        if (data.rate_tps || data.tps) {
          setAutoFeedTps(data.rate_tps || data.tps);
        }
        setAutoFeedStats(data);
      }
    } catch (err) {
      console.warn("autofeed status refresh failed", err);
    }
  }, []);

  const startAutoFeed = useCallback(
    async (tps = 10.0, fraudRatio = 0.15, bursty = true) => {
      try {
        const res = await api.startAutoFeed({ rate_tps: tps, fraud_ratio: fraudRatio, bursty });
        setAutoFeedActive(true);
        setAutoFeedTps(tps);
        setAutoFeedStats((prev) => ({ ...prev, active: true, rate_tps: tps }));
        return res;
      } catch (err) {
        console.error("startAutoFeed failed", err);
      }
    },
    []
  );

  const stopAutoFeed = useCallback(async () => {
    try {
      const res = await api.stopAutoFeed();
      setAutoFeedActive(false);
      setAutoFeedStats((prev) => ({ ...prev, active: false }));
      return res;
    } catch (err) {
      console.error("stopAutoFeed failed", err);
    }
  }, []);

  const toggleAutoFeed = useCallback(async () => {
    if (autoFeedActive) {
      await stopAutoFeed();
    } else {
      await startAutoFeed(autoFeedTps, 0.15, true);
    }
  }, [autoFeedActive, autoFeedTps, startAutoFeed, stopAutoFeed]);

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
        const hpVal =
          incomingStats.honeypot_hits_24h ??
          incomingStats.honeypot_hits ??
          incomingStats.honeypots?.total_hits ??
          null;
        setStats((prev) => ({
          evaluated: incomingStats.evaluated ?? prev.evaluated,
          allowed: incomingStats.allowed ?? prev.allowed,
          held: incomingStats.held ?? prev.held,
          blocked: incomingStats.blocked ?? prev.blocked,
          honeypot_hits: hpVal !== null ? hpVal : prev.honeypot_hits,
          honeypot_hits_24h: hpVal !== null ? hpVal : prev.honeypot_hits_24h,
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
      const hpVal =
        incomingStats.honeypot_hits_24h ??
        incomingStats.honeypot_hits ??
        incomingStats.honeypots?.total_hits ??
        null;
      setStats((prev) => ({
        evaluated: incomingStats.evaluated ?? prev.evaluated,
        allowed: incomingStats.allowed ?? prev.allowed,
        held: incomingStats.held ?? prev.held,
        blocked: incomingStats.blocked ?? prev.blocked,
        honeypot_hits: hpVal !== null ? hpVal : prev.honeypot_hits,
        honeypot_hits_24h: hpVal !== null ? hpVal : prev.honeypot_hits_24h,
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

        const hpVal = result.honeypot_hits_24h ?? result.honeypot_hits ?? null;

        setStats((prev) => ({
          evaluated: prev.evaluated + (result.processed || 0),
          allowed,
          held,
          blocked,
          honeypot_hits: hpVal !== null ? hpVal : prev.honeypot_hits,
          honeypot_hits_24h: hpVal !== null ? hpVal : prev.honeypot_hits_24h,
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
    refreshAutoFeedStatus();
    const timer = setTimeout(() => {
      runSimulation(300, 0.15);
    }, 400);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll auto-feed status while active
  useEffect(() => {
    if (!autoFeedActive) return;
    const interval = setInterval(() => {
      refreshAutoFeedStatus();
    }, 3000);
    return () => clearInterval(interval);
  }, [autoFeedActive, refreshAutoFeedStatus]);

  const value = {
    stats,
    cases,
    verdictHistory,
    selectedCase,
    busy,
    live: live || connected || autoFeedActive,
    connected,
    sensitivity,
    deployStatus,
    autoFeedActive,
    autoFeedTps,
    autoFeedStats,
    setAutoFeedTps,
    startAutoFeed,
    stopAutoFeed,
    toggleAutoFeed,
    refreshAutoFeedStatus,
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
