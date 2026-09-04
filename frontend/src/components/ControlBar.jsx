import React, { useState } from "react";
import { useAppState } from "../context/AppStateContext";
import { useToast } from "../context/ToastContext";

export default function ControlBar({ onSimulate, onFederate, busy }) {
  const { toast } = useToast();
  const {
    autoFeedActive,
    autoFeedTps,
    autoFeedStats,
    toggleAutoFeed,
    setAutoFeedTps,
  } = useAppState();

  const [count, setCount] = useState(300);
  const [fraud, setFraud] = useState(15);
  const [tpsConfig, setTpsConfig] = useState(autoFeedTps || 10);

  const handleTpsChange = (val) => {
    const num = Math.max(1, Math.min(50, Number(val)));
    setTpsConfig(num);
    if (setAutoFeedTps) setAutoFeedTps(num);
  };

  const handleCountChange = (val) => {
    const num = Number(val);
    const clamped = isNaN(num) ? 10 : Math.max(10, Math.min(2000, num));
    setCount(clamped);
  };

  const handleToggleAutoFeed = async () => {
    const nextState = !autoFeedActive;
    try {
      await toggleAutoFeed();
      if (nextState) {
        toast.success("Live Auto-Feed active at " + tpsConfig + " tx/s");
      } else {
        toast.info("Live Auto-Feed paused");
      }
    } catch (err) {
      toast.error(err.message || "Failed to toggle Auto-Feed");
    }
  };

  const handleSimulate = async () => {
    if (onSimulate) {
      toast.success("Batch simulation started (" + count + " txns, " + fraud + "% fraud)");
      try {
        await onSimulate(count, fraud / 100);
      } catch (err) {
        toast.error(err.message || "Batch simulation failed");
      }
    }
  };

  const handleFederate = async () => {
    if (onFederate) {
      toast.success("Federation intelligence round dispatched");
      try {
        await onFederate();
      } catch (err) {
        toast.error(err.message || "Federation round failed");
      }
    }
  };

  return (
    <div className="panel overflow-hidden">
      {/* Header */}
      <div className="panel-header flex flex-wrap items-center justify-between gap-3">
        <div className="panel-title">
          <div className="text-[11px] uppercase tracking-wide text-muted font-mono">
            Console &amp; Traffic Generator
          </div>
          <div className="font-serif font-semibold text-ink-900">
            Traffic Generation &amp; Pipeline Controls
          </div>
        </div>

        {/* Live Auto-Feed Status Badge */}
        <div className="flex items-center gap-2">
          {autoFeedActive ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-300 font-mono text-xs font-bold shadow-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>LIVE AUTO-FEED: {autoFeedStats?.rate_tps ?? tpsConfig} tx/s</span>
              {autoFeedStats?.total_generated ? (
                <span className="text-[10px] text-emerald-800 font-normal">
                  ({autoFeedStats.total_generated} txns)
                </span>
              ) : null}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-muted text-muted border border-hairline font-mono text-xs">
              <span className="w-2 h-2 rounded-full bg-slate-400" />
              <span>AUTO-FEED IDLE</span>
            </div>
          )}
        </div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Top Control Strip: Live Feed vs Manual Simulation */}
        <div className="p-3 bg-surface-muted/60 rounded-lg border border-hairline flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <div className="text-[10px] uppercase font-mono font-semibold text-muted">
                Continuous Stream
              </div>
              <div className="text-xs font-semibold text-ink-900">
                Continuous UPI Transaction Rail
              </div>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <label className="text-muted text-[11px]">TPS Target:</label>
              <input
                type="number"
                min={1}
                max={50}
                value={tpsConfig}
                disabled={autoFeedActive}
                onChange={(e) => handleTpsChange(e.target.value)}
                className="w-16 border border-hairline rounded px-2 py-1 bg-white text-xs font-bold disabled:bg-slate-100"
              />
              <span className="text-muted text-[10px]">tx/s (Max 50)</span>
            </div>
          </div>

          {/* Indicator, Live TPS Counter & Toggle Button */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white border border-hairline font-mono text-xs shadow-xs">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  autoFeedActive ? "bg-emerald-500 animate-pulse" : "bg-slate-300"
                }`}
              />
              <span className="text-muted text-[11px] uppercase font-semibold">Live TPS:</span>
              <span className={`font-bold ${autoFeedActive ? "text-emerald-700" : "text-slate-600"}`}>
                {autoFeedActive ? (autoFeedStats?.rate_tps ?? tpsConfig) : 0} tx/s
              </span>
            </div>

            <button
              onClick={handleToggleAutoFeed}
              className={`flex items-center gap-2 px-4 py-2 rounded-md font-mono text-xs font-bold transition-all shadow-sm ${
                autoFeedActive
                  ? "bg-rose-600 hover:bg-rose-700 text-white ring-2 ring-rose-300"
                  : "bg-emerald-600 hover:bg-emerald-700 text-white hover:shadow-glow"
              }`}
            >
              {autoFeedActive ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  <span>Stop Live Feed</span>
                </>
              ) : (
                <>
                  <span>⚡ Start Live Feed</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Bottom Manual Controls: Batched Simulation & Federation */}
        <div className="flex flex-wrap items-end gap-6 pt-1">
          <div>
            <label className="block text-[11px] uppercase text-muted mb-1 font-mono">
              Batch Transactions
            </label>
            <input
              type="number"
              value={count}
              min={10}
              max={2000}
              onChange={(e) => handleCountChange(e.target.value)}
              className="w-28 border border-hairline rounded px-2 py-1.5 text-sm font-mono bg-white"
            />
          </div>

          <div className="min-w-[220px]">
            <label className="block text-[11px] uppercase text-muted mb-1 font-mono">
              Fraud injection rate: <span className="font-bold text-ink-900">{fraud}%</span>
            </label>
            <input
              type="range"
              min={0}
              max={60}
              value={fraud}
              onChange={(e) => setFraud(Number(e.target.value))}
              className="w-full accent-saffron"
            />
          </div>

          <div className="flex gap-2 ml-auto">
            <button
              disabled={busy}
              onClick={handleSimulate}
              className="btn-primary disabled:opacity-50 text-xs font-semibold"
            >
              {busy ? "Running…" : "▶ Run batch simulation"}
            </button>
            <button
              disabled={busy}
              onClick={handleFederate}
              className="btn-secondary disabled:opacity-50 text-xs font-semibold"
            >
              ⟲ Federation round
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
