import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { formatINR } from "../../services/api";

const BANK_COLORS = [
  "#0b1f3a", // Navy (ICICI / Axis)
  "#c8641e", // Saffron (HDFC)
  "#0f7a3d", // Green (SBI)
  "#a8660a", // Amber (Paytm)
  "#7c3aed", // Purple (PhonePe/YBL)
  "#0284c7", // Sky (Others)
];

function CustomPieTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0]?.payload || {};

  return (
    <div className="bg-ink-900 text-white px-3 py-2 rounded shadow-xl text-xs font-mono border border-white/10 space-y-1">
      <div className="font-bold text-white flex items-center justify-between gap-3">
        <span>{data.bank || data.name}</span>
        <span>{data.count || data.value} cases</span>
      </div>
      {data.percentage != null && (
        <div className="text-saffron-light">
          Share: {Number(data.percentage).toFixed(1)}%
        </div>
      )}
      {data.flagged_amount != null && (
        <div className="text-emerald-400">
          Amount: {formatINR(data.flagged_amount)}
        </div>
      )}
    </div>
  );
}

export default function BankDistributionChart({ data = [] }) {
  const chartData = data.length > 0 ? data : [
    { bank: "ICICI", count: 42, percentage: 35.0, flagged_amount: 1450000 },
    { bank: "HDFC", count: 32, percentage: 26.7, flagged_amount: 1100000 },
    { bank: "Paytm", count: 24, percentage: 20.0, flagged_amount: 820000 },
    { bank: "PhonePe", count: 14, percentage: 11.7, flagged_amount: 480000 },
    { bank: "SBI", count: 8, percentage: 6.6, flagged_amount: 270000 },
  ];

  const total = chartData.reduce((acc, d) => acc + (d.count || d.value || 0), 0);

  return (
    <div className="panel p-5">
      <div className="panel-title mb-4">
        <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
          Ecosystem Exposure
        </div>
        <div className="font-serif font-bold text-ink-900">
          Bank &amp; PSP Distribution
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="w-40 h-40 relative shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="count"
                nameKey="bank"
                innerRadius={45}
                outerRadius={68}
                paddingAngle={3}
                isAnimationActive={true}
                animationDuration={800}
              >
                {chartData.map((d, idx) => (
                  <Cell key={idx} fill={BANK_COLORS[idx % BANK_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <div className="font-serif text-lg font-bold text-ink-900">{total}</div>
            <div className="text-[10px] font-mono text-muted uppercase">Cases</div>
          </div>
        </div>

        <div className="space-y-2 flex-1 w-full text-xs font-mono">
          {chartData.map((d, idx) => (
            <div key={d.bank || idx} className="flex items-center justify-between gap-2 border-b border-hairline/60 pb-1">
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: BANK_COLORS[idx % BANK_COLORS.length] }}
                />
                <span className="font-semibold text-body truncate max-w-[120px]">
                  {d.bank || d.name}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-ink-900">{d.count || d.value}</span>
                <span className="text-muted text-[11px] w-12 text-right">
                  {total ? `${Math.round(((d.count || d.value) / total) * 100)}%` : "0%"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
