import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

function CustomTimeSeriesTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0]?.payload || {};

  return (
    <div className="bg-ink-900 text-white px-3 py-2 rounded shadow-xl text-xs font-mono border border-white/10 space-y-1 z-50">
      <div className="text-white/60 text-[10px] pb-1 border-b border-white/10 flex justify-between gap-4">
        <span>BUCKET: {label}</span>
        <span>TOTAL: {(data.allow || 0) + (data.hold || 0) + (data.block || 0)}</span>
      </div>
      <div className="flex items-center justify-between gap-3 text-emerald-400">
        <span>ALLOW:</span>
        <span className="font-bold">{data.allow || 0}</span>
      </div>
      <div className="flex items-center justify-between gap-3 text-amber-400">
        <span>HOLD:</span>
        <span className="font-bold">{data.hold || 0}</span>
      </div>
      <div className="flex items-center justify-between gap-3 text-rose-400">
        <span>BLOCK:</span>
        <span className="font-bold">{data.block || 0}</span>
      </div>
      {data.fraud_rate_pct != null && (
        <div className="pt-1 border-t border-white/10 text-[10px] text-saffron-light">
          Fraud Rate: {Number(data.fraud_rate_pct).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

export default function TimeSeriesVerdictChart({ timeSeriesData = [], interval, onIntervalChange }) {
  const [viewMode, setViewMode] = useState("stacked");

  return (
    <div className="panel">
      <div className="panel-header flex flex-wrap items-center justify-between gap-3">
        <div className="panel-title">
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            Time-Series Breakdown
          </div>
          <div className="font-serif font-bold text-ink-900">
            Hourly / Daily Verdict Volume
          </div>
        </div>

        {/* Interval Toggles */}
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md border border-hairline p-0.5 bg-surface-muted text-xs font-mono">
            <button
              onClick={() => onIntervalChange?.("hourly")}
              className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                interval === "hourly"
                  ? "bg-white text-ink-900 shadow-sm"
                  : "text-muted hover:text-ink-900"
              }`}
            >
              Hourly (24h)
            </button>
            <button
              onClick={() => onIntervalChange?.("daily")}
              className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                interval === "daily"
                  ? "bg-white text-ink-900 shadow-sm"
                  : "text-muted hover:text-ink-900"
              }`}
            >
              Daily (30d)
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 pt-2">
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timeSeriesData} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
              <XAxis
                dataKey="bucket"
                tick={{ fontSize: 10, fill: "#6b7280", fontFamily: "monospace" }}
                axisLine={{ stroke: "#e5e7eb" }}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 10, fill: "#6b7280", fontFamily: "monospace" }}
                axisLine={{ stroke: "#e5e7eb" }}
                tickLine={false}
              />
              <Tooltip content={<CustomTimeSeriesTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                height={28}
                iconSize={8}
                formatter={(value) => (
                  <span className="text-[11px] font-mono text-muted uppercase font-medium mr-2">
                    {value}
                  </span>
                )}
              />
              <Bar dataKey="allow" name="ALLOW" stackId="a" fill="#0f7a3d" radius={[0, 0, 0, 0]} />
              <Bar dataKey="hold" name="HOLD" stackId="a" fill="#a8660a" radius={[0, 0, 0, 0]} />
              <Bar dataKey="block" name="BLOCK" stackId="a" fill="#b3261e" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
