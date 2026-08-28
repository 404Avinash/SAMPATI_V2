import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { formatINR, relativeTime, shortVpa } from "../services/api";

const VERDICT_STYLE = {
  ALLOW: "bg-verdict-allowBg text-verdict-allow border-verdict-allow/30",
  HOLD: "bg-verdict-holdBg text-verdict-hold border-verdict-hold/30",
  BLOCK: "bg-verdict-blockBg text-verdict-block border-verdict-block/30",
};

export default function LiveFeed({ cases, onSelect }) {
  const rows = (cases || []).slice(0, 40);

  return (
    <div className="relative h-full overflow-y-auto font-mono text-[13px]">
      <div className="pointer-events-none absolute inset-0 opacity-[0.03] animate-scan bg-[linear-gradient(transparent_95%,rgba(11,31,58,0.6)_100%)] bg-[length:100%_4px]" />
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-white z-10">
          <tr className="text-left text-[11px] uppercase tracking-wide text-muted border-b border-hairline">
            <th className="py-2 px-3 font-medium">Time</th>
            <th className="py-2 px-3 font-medium">Flow (payer → payee)</th>
            <th className="py-2 px-3 font-medium text-right">Amount</th>
            <th className="py-2 px-3 font-medium">Verdict</th>
            <th className="py-2 px-3 font-medium text-right">Score</th>
            <th className="py-2 px-3 font-medium">Signals</th>
          </tr>
        </thead>
        <tbody>
          <AnimatePresence initial={false}>
            {rows.map((c, i) => {
              const t = c.trigger_txn || {};
              const verdict = c.verdict || "HOLD";
              return (
                <motion.tr
                  key={c.case_id}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.35, delay: Math.min(i, 10) * 0.02 }}
                  onClick={() => onSelect?.(c)}
                  className={`cursor-pointer border-b border-hairline/70 hover:bg-surface-muted transition-colors ${
                    verdict === "BLOCK" ? "shadow-[inset_3px_0_0_0_#b3261e]" : verdict === "HOLD" ? "shadow-[inset_3px_0_0_0_#a8660a]" : ""
                  }`}
                >
                  <td className="py-2 px-3 text-muted whitespace-nowrap">{relativeTime(c.created_at)}</td>
                  <td className="py-2 px-3 whitespace-nowrap">
                    <span className="text-body">{shortVpa(t.payer_vpa)}</span>
                    <span className="text-muted mx-1">→</span>
                    <span className="text-body">{shortVpa(t.payee_vpa)}</span>
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums">{formatINR(t.amount ?? c.amount)}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-sans font-semibold ${
                        VERDICT_STYLE[verdict] || VERDICT_STYLE.HOLD
                      } ${verdict === "BLOCK" ? "animate-pulse-ring" : ""}`}
                    >
                      {verdict}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums">{c.risk_score ?? "—"}</td>
                  <td className="py-2 px-3 text-muted truncate max-w-[220px]">
                    {(c.reasons || []).slice(0, 2).join(", ") || "—"}
                  </td>
                </motion.tr>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
      {rows.length === 0 && (
        <div className="p-8 text-center text-muted">No flagged activity yet — run a simulation.</div>
      )}
    </div>
  );
}
