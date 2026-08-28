import React, { useState } from "react";

export default function ControlBar({ onSimulate, onFederate, busy }) {
  const [count, setCount] = useState(300);
  const [fraud, setFraud] = useState(15);

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <div className="text-[11px] uppercase tracking-wide text-muted">Console</div>
          <div className="font-serif font-semibold text-ink-900">Traffic &amp; Intelligence Controls</div>
        </div>
      </div>
      <div className="flex flex-wrap items-end gap-6 px-4 py-4">
        <div>
          <label className="block text-[11px] uppercase text-muted mb-1">Transactions</label>
          <input
            type="number"
            value={count}
            min={10}
            max={2000}
            onChange={(e) => setCount(Number(e.target.value))}
            className="w-28 border border-hairline rounded px-2 py-1.5 text-sm font-mono"
          />
        </div>
        <div className="min-w-[220px]">
          <label className="block text-[11px] uppercase text-muted mb-1">
            Fraud injection <span className="font-mono">{fraud}%</span>
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
            onClick={() => onSimulate(count, fraud / 100)}
            className="btn-primary disabled:opacity-50"
          >
            {busy ? "Running…" : "▶ Run simulation"}
          </button>
          <button disabled={busy} onClick={onFederate} className="btn-secondary disabled:opacity-50">
            ⟲ Federation round
          </button>
        </div>
      </div>
    </div>
  );
}
