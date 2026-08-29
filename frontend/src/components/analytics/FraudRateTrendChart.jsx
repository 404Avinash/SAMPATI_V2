import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts";

function CustomFraudRateTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const val = payload[0]?.value;

  return (
    <div className="bg-ink-900 text-white px-3 py-2 rounded shadow-xl text-xs font-mono border border-white/10 space-y-1">
      <div className="text-white/60 text-[10px] pb-1 border-b border-white/10">
        TIME: {label}
      </div>
      <div className="flex items-center justify-between gap-3 text-rose-400">
        <span>Fraud Rate:</span>
        <span className="font-bold">{Number(val).toFixed(2)}%</span>
      </div>
      <div className="text-[10px] text-muted">
        Target SLA: &lt; 5.00%
      </div>
    </div>
  );
}

export default function FraudRateTrendChart({ data = [] }) {
  return (
    <div className="panel">
      <div className="panel-header flex items-center justify-between">
        <div className="panel-title">
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            Operational Risk SLA
          </div>
          <div className="font-serif font-bold text-ink-900">
            Fraud Rate Trend vs. 5% SLA Target
          </div>
        </div>
        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
          SLA Limit: 5.0%
        </span>
      </div>

      <div className="p-4 pt-2">
        <div className="h-[240px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
              <XAxis
                dataKey="bucket"
                tick={{ fontSize: 10, fill: "#6b7280", fontFamily: "monospace" }}
                axisLine={{ stroke: "#e5e7eb" }}
                tickLine={false}
              />
              <YAxis
                unit="%"
                domain={[0, "auto"]}
                tick={{ fontSize: 10, fill: "#6b7280", fontFamily: "monospace" }}
                axisLine={{ stroke: "#e5e7eb" }}
                tickLine={false}
              />
              <Tooltip content={<CustomFraudRateTooltip />} />
              <ReferenceLine
                y={5.0}
                label={{
                  value: "5.0% SLA Threshold",
                  fill: "#b3261e",
                  fontSize: 10,
                  fontFamily: "monospace",
                  position: "top",
                }}
                stroke="#b3261e"
                strokeDasharray="4 4"
                strokeWidth={1.5}
              />
              <Line
                type="monotone"
                dataKey="fraud_rate_pct"
                name="Fraud Rate %"
                stroke="#c8641e"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#c8641e" }}
                activeDot={{ r: 5, fill: "#0b1f3a" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
