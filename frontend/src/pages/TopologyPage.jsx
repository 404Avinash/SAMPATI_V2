import React, { useState, useMemo, useRef, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAppState } from "../context/AppStateContext";
import { useToast } from "../context/ToastContext";
import { formatINR } from "../services/api";
import NetworkConstellation from "../components/NetworkConstellation";
import GeoMuleMap, { INDIAN_HUBS } from "../components/overview/GeoMuleMap";

export default function TopologyPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawMode = searchParams.get("view");
  const viewMode = rawMode === "geomap" || rawMode === "dual" ? rawMode : "constellation";

  const { cases, openCase, runSimulation, busy } = useAppState();
  const { toast } = useToast();

  const containerRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Monitor fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  const setViewMode = (mode) => {
    if (mode === "constellation") {
      setSearchParams({}, { replace: true });
    } else {
      setSearchParams({ view: mode }, { replace: true });
    }
  };

  const handleToggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.().then(() => {
        toast.info("Entered fullscreen topology workspace");
      }).catch((err) => {
        console.error("Fullscreen request failed", err);
        toast.warning("Fullscreen mode could not be opened");
      });
    } else {
      document.exitFullscreen?.().then(() => {
        toast.info("Exited fullscreen mode");
      }).catch((err) => {
        console.error("Exit fullscreen failed", err);
      });
    }
  };

  const handleSimulateBurst = async () => {
    toast.success("Simulation burst triggered across fraud mesh");
    try {
      await runSimulation(300, 0.25);
    } catch (err) {
      console.error("Burst simulation failed", err);
    }
  };

  // Compute live intercepted volume across active cases
  const interceptedVolume = useMemo(() => {
    if (!cases || !cases.length) return "₹6.78 Cr";
    const sum = cases.reduce((acc, c) => {
      const amt = Number(c.amount) || Number(c.total_amount) || Number(c.trigger_txn?.amount) || 0;
      return acc + amt;
    }, 0);
    return sum > 0 ? formatINR(sum) : "₹6.78 Cr";
  }, [cases]);

  return (
    <div className="space-y-4">
      {/* Top Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-serif text-2xl font-bold text-ink-900 tracking-tight">
              Fraud Mesh Topology
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-saffron/10 text-saffron border border-saffron/20 font-bold">
              MULTI-PERSPECTIVE
            </span>
          </div>
          <p className="text-xs text-muted mt-0.5">
            Spatial and network graph intelligence console. Analyze force-directed algorithmic clusters,
            inter-state mule routing corridors, or synchronized dual perspectives.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={handleSimulateBurst}
            disabled={busy}
            className="btn-secondary text-xs flex items-center gap-1.5 px-3 py-1.5"
            title="Generate high-velocity traffic burst to observe real-time topology reactions"
          >
            <span className={busy ? "animate-spin" : ""}>⚡</span>
            <span>{busy ? "Simulating…" : "Simulate Burst"}</span>
          </button>
          <button
            type="button"
            onClick={handleToggleFullscreen}
            className="btn-secondary text-xs flex items-center gap-1.5 px-3 py-1.5"
            title="Toggle Fullscreen Workspace"
          >
            <span>{isFullscreen ? "🗗" : "⛶"}</span>
            <span>{isFullscreen ? "Exit Fullscreen" : "Fullscreen"}</span>
          </button>
        </div>
      </div>

      {/* Integrated Dedicated Sub-Navbar */}
      <div className="bg-white border border-hairline rounded-xl p-2.5 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: 3-Way Sub-Nav Segmented Controls */}
        <div className="flex items-center gap-1 bg-surface-muted p-1 rounded-lg border border-hairline text-xs font-mono w-full md:w-auto justify-center">
          <button
            type="button"
            onClick={() => setViewMode("constellation")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md font-semibold transition-all ${
              viewMode === "constellation"
                ? "bg-white text-ink-900 shadow-xs border border-hairline"
                : "text-muted hover:text-ink-900"
            }`}
          >
            <span>☍</span>
            <span>Constellation Force Graph</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode("geomap")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md font-semibold transition-all ${
              viewMode === "geomap"
                ? "bg-white text-ink-900 shadow-xs border border-hairline"
                : "text-muted hover:text-ink-900"
            }`}
          >
            <span>🗺️</span>
            <span>India Mule Corridors</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode("dual")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md font-semibold transition-all ${
              viewMode === "dual"
                ? "bg-white text-ink-900 shadow-xs border border-hairline"
                : "text-muted hover:text-ink-900"
            }`}
          >
            <span>⛶</span>
            <span>Dual Perspective</span>
          </button>
        </div>

        {/* Right: Live Telemetry Strip */}
        <div className="flex flex-wrap items-center justify-center md:justify-end gap-2.5 text-xs font-mono">
          <span className="px-2.5 py-1 rounded bg-surface-muted border border-hairline text-ink-900 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span><strong>{cases.length}</strong> Active Mule Rings</span>
          </span>
          <span className="px-2.5 py-1 rounded bg-surface-muted border border-hairline text-muted flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            <span><strong>{INDIAN_HUBS?.length || 9}</strong> Monitored Hubs</span>
          </span>
          <span className="px-2.5 py-1 rounded bg-surface-muted border border-hairline text-rose-700 font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            <span><strong>{interceptedVolume}</strong> Intercepted</span>
          </span>
        </div>
      </div>

      {/* Main Dedicated Visualizer Canvas Area */}
      <div
        ref={containerRef}
        className={`w-full ${
          isFullscreen
            ? "fixed inset-0 z-50 bg-[#f8f9fc] p-4 flex flex-col h-screen overflow-auto"
            : "h-[calc(100vh-12rem)] min-h-[700px] flex flex-col"
        }`}
      >
        {isFullscreen && (
          <div className="flex items-center justify-between pb-3 mb-2 border-b border-hairline">
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-ink-900 text-lg">
                SAMPATI Fraud Mesh Topology (Fullscreen Mode)
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-muted border border-hairline text-muted">
                Mode: {viewMode.toUpperCase()}
              </span>
            </div>
            <button
              type="button"
              onClick={handleToggleFullscreen}
              className="btn-secondary text-xs flex items-center gap-1 px-3 py-1"
            >
              <span>✕</span>
              <span>Exit Fullscreen</span>
            </button>
          </div>
        )}

        {viewMode === "constellation" && (
          <div className="flex-1 w-full h-full bg-white rounded-xl border border-hairline shadow-xs overflow-hidden relative min-h-[650px]">
            <NetworkConstellation cases={cases} onSelectCase={openCase} />
          </div>
        )}

        {viewMode === "geomap" && (
          <div className="flex-1 w-full h-full bg-white rounded-xl border border-hairline shadow-xs overflow-hidden relative min-h-[650px]">
            <GeoMuleMap cases={cases} onSelectCase={openCase} />
          </div>
        )}

        {viewMode === "dual" && (
          <div className="flex-1 w-full h-full grid grid-cols-1 xl:grid-cols-2 gap-4 min-h-[650px]">
            {/* Left Column: Network Constellation Physics Mesh */}
            <div className="bg-white rounded-xl border border-hairline shadow-xs overflow-hidden relative flex flex-col min-h-[480px]">
              <div className="px-3.5 py-2 border-b border-hairline bg-surface-muted/60 flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2 font-bold text-ink-900">
                  <span className="text-saffron">☍</span>
                  <span>Constellation Force Graph</span>
                </div>
                <span className="text-[11px] text-muted">{cases.length} Clusters</span>
              </div>
              <div className="flex-1 relative overflow-hidden">
                <NetworkConstellation cases={cases} onSelectCase={openCase} />
              </div>
            </div>

            {/* Right Column: Geographic India Mule Corridors */}
            <div className="bg-white rounded-xl border border-hairline shadow-xs overflow-hidden relative flex flex-col min-h-[480px]">
              <div className="px-3.5 py-2 border-b border-hairline bg-surface-muted/60 flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2 font-bold text-ink-900">
                  <span className="text-indigo-600">🗺️</span>
                  <span>India Mule Corridors</span>
                </div>
                <span className="text-[11px] text-muted">{INDIAN_HUBS?.length || 9} Hubs Monitored</span>
              </div>
              <div className="flex-1 relative overflow-hidden">
                <GeoMuleMap cases={cases} onSelectCase={openCase} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
