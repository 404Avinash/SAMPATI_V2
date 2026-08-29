import React from "react";
import { getVerdictTone } from "../../services/api";

export function VerdictBadge({ verdict, className = "", showPulse = true }) {
  const tone = getVerdictTone(verdict);
  const isBlock = verdict === "BLOCK";

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full border text-[11px] font-sans font-bold tracking-wide ${
        tone.badge
      } ${isBlock && showPulse ? "animate-pulse-ring" : ""} ${className}`}
    >
      {tone.label}
    </span>
  );
}

export function StatusBadge({ status, className = "" }) {
  const s = (status || "OPEN").toUpperCase();

  let styles = "bg-slate-100 text-slate-700 border-slate-200";

  switch (s) {
    case "OPEN":
      styles = "bg-sky-50 text-sky-700 border-sky-200";
      break;
    case "REVIEWED":
    case "INVESTIGATED":
      styles = "bg-indigo-50 text-indigo-700 border-indigo-200";
      break;
    case "ESCALATED":
      styles = "bg-purple-50 text-purple-700 border-purple-200";
      break;
    case "RESOLVED":
      styles = "bg-emerald-50 text-emerald-700 border-emerald-200";
      break;
    case "DISMISSED":
      styles = "bg-gray-100 text-gray-600 border-gray-200";
      break;
    default:
      styles = "bg-slate-100 text-slate-700 border-slate-200";
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md border text-[10px] font-mono font-semibold uppercase tracking-wider ${styles} ${className}`}
    >
      {s}
    </span>
  );
}

export function RiskScoreBadge({ score, className = "" }) {
  const num = typeof score === "number" ? score : parseFloat(score) || 0;

  let bg = "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (num >= 75) bg = "bg-rose-50 text-rose-700 border-rose-200 font-bold";
  else if (num >= 40) bg = "bg-amber-50 text-amber-700 border-amber-200";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border font-mono text-xs ${bg} ${className}`}
    >
      <span className="text-[10px] text-muted uppercase">Risk</span>
      <span>{num}</span>
    </span>
  );
}
