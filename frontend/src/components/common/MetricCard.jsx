import React from "react";
import { useCountUp } from "../../hooks/useCountUp";

export default function MetricCard({
  label,
  value,
  icon,
  trend,
  subtext,
  tone = "default",
  isNumeric = true,
  className = "",
}) {
  const _counted = useCountUp(typeof value === "number" ? value : 0);
  const animatedValue = isNumeric && typeof value === "number" ? _counted : value;

  const toneStyles = {
    default: "text-ink-900 bg-white border-hairline",
    emerald: "text-emerald-900 bg-white border-emerald-200 shadow-sm",
    amber: "text-amber-900 bg-white border-amber-200 shadow-sm",
    rose: "text-rose-900 bg-white border-rose-200 shadow-sm",
    purple: "text-purple-900 bg-white border-purple-200 shadow-sm",
    sky: "text-sky-900 bg-white border-sky-200 shadow-sm",
  };

  const iconTones = {
    default: "bg-surface-muted text-muted",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600",
    purple: "bg-purple-50 text-purple-600",
    sky: "bg-sky-50 text-sky-600",
  };

  return (
    <div
      className={`panel p-4 flex flex-col justify-between transition-all duration-200 hover:shadow-md ${
        toneStyles[tone] || toneStyles.default
      } ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-mono uppercase tracking-wider text-muted font-medium truncate">
          {label}
        </span>
        {icon && (
          <div
            className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 text-sm font-bold ${
              iconTones[tone] || iconTones.default
            }`}
          >
            {icon}
          </div>
        )}
      </div>

      <div>
        <div className="font-serif text-2xl font-bold tracking-tight text-ink-900 tabular-nums">
          {animatedValue != null ? animatedValue : "—"}
        </div>
        {(subtext || trend) && (
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted">
            {trend && (
              <span
                className={`font-semibold font-mono text-[11px] ${
                  trend.startsWith("+")
                    ? "text-rose-600"
                    : trend.startsWith("-")
                    ? "text-emerald-600"
                    : "text-muted"
                }`}
              >
                {trend}
              </span>
            )}
            {subtext && <span className="truncate">{subtext}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
