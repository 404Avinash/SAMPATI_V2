import React, { useState } from "react";
import { useAppState } from "../context/AppStateContext";

export default function ControlBar({ onSimulate, onFederate, busy }) {
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

  return (
    <div className="panel overflow-hidden">
      {/* Header */}
      <div className="panel-header flex flex-wrap items-center justify-between gap-3">
        <div className="panel-title">
          <div className="text-[11px] uppercase tracking-wide text-muted font-mono">
            Console &amp; Traffic Generator
          </div>
          <div className="font-serif font-semibold text-ink-900">
            Traffic &amp; Autonomous Intelligence Controls
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
        {/* Top Control Strip: Autonomous Live Feed vs Manual Simulation */}
        <div className="p-3 bg-surface-muted/60 rounded-lg border border-hairline flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <div className="text-[10px] uppercase font-mono font-semibold text-muted">
                Autonomous Stream
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

          {/* Auto-Feed Start / Stop Toggle Button */}
          <button
            onClick={toggleAutoFeed}
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-mono text-xs font-bold transition-all shadow-sm ${
              autoFeedActive
                ? "bg-rose-600 hover:bg-rose-700 text-white ring-2 ring-rose-300"
                : "bg-emerald-600 hover:bg-emerald-700 text-white hover:shadow-glow"
            }`}
          >
            {autoFeedActive ? (
              <>
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                <span>⏹ Stop Live Auto-Feed</span>
              </>
            ) : (
              <>
                <span>⚡ Start Live Auto-Feed ({tpsConfig} tx/s)</span>
              </>
            )}
          </button>
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
              onChange={(e) => setCount(Number(e.target.value))}
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
              onClick={() => onSimulate && onSimulate(count, fraud / 100)}
              className="btn-primary disabled:opacity-50 text-xs font-semibold"
            >
              {busy ? "Running…" : "▶ Run batch simulation"}
            </button>
            <button
              disabled={busy}
              onClick={onFederate}
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
