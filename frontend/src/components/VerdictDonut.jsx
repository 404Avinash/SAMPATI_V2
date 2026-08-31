import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = { Allowed: "#0f7a3d", Held: "#a8660a", Blocked: "#b3261e" };

export default function VerdictDonut({ allowed, held, blocked }) {
  const total = allowed + held + blocked;
  const data = [
    { name: "Allowed", value: allowed },
    { name: "Held", value: held },
    { name: "Blocked", value: blocked },
  ];

  return (
    <div className="flex items-center gap-4">
      <div className="w-32 h-32 relative shrink-0">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              innerRadius={40}
              outerRadius={58}
              paddingAngle={2}
              isAnimationActive={true}
              animationDuration={800}
            >
              {data.map((d) => (
                <Cell key={d.name} fill={COLORS[d.name]} />
              ))}
            </Pie>
            <Tooltip formatter={(v, n) => [v, n]} />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="font-serif text-lg font-semibold">{total}</div>
          <div className="text-[10px] text-muted uppercase">Total</div>
        </div>
      </div>
      <div className="space-y-1.5 text-sm">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[d.name] }} />
            <span className="text-body w-16">{d.name}</span>
            <span className="font-mono text-muted">{d.value}</span>
            <span className="font-mono text-muted text-xs">
              {total ? `${Math.round((d.value / total) * 100)}%` : "0%"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
