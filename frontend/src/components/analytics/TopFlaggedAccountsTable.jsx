import React from "react";
import { formatINR, shortVpa } from "../../services/api";
import { RiskScoreBadge } from "../common/StatusBadge";

export default function TopFlaggedAccountsTable({ accounts = [] }) {
  return (
    <div className="panel overflow-hidden">
      <div className="panel-header flex items-center justify-between">
        <div className="panel-title">
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            High-Risk Entities
          </div>
          <div className="font-serif font-bold text-ink-900">
            Top Flagged Mule &amp; Collector Accounts
          </div>
        </div>
        <span className="text-xs font-mono text-muted">{accounts.length} Entities</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs border-collapse">
          <thead>
            <tr className="bg-surface-muted/70 text-muted uppercase text-[10px] border-b border-hairline tracking-wider">
              <th className="py-3 px-4 font-semibold">Rank</th>
              <th className="py-3 px-4 font-semibold">VPA Identifier</th>
              <th className="py-3 px-4 font-semibold">Bank / PSP</th>
              <th className="py-3 px-4 font-semibold text-center">Flagged Cases</th>
              <th className="py-3 px-4 font-semibold text-right">Total Protected Volume</th>
              <th className="py-3 px-4 font-semibold text-center">Avg Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {accounts.map((acc, index) => (
              <tr key={acc.vpa || acc.account_id || index} className="hover:bg-surface-muted/50 transition-colors">
                <td className="py-3 px-4 font-bold text-muted">#{index + 1}</td>
                <td className="py-3 px-4 font-bold text-ink-900 truncate max-w-[200px]" title={acc.vpa}>
                  {shortVpa(acc.vpa || acc.account_id)}
                </td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-semibold border border-slate-200">
                    {acc.bank || acc.psp || "UPI-PSP"}
                  </span>
                </td>
                <td className="py-3 px-4 text-center">
                  <span className="inline-flex items-center gap-1.5 font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                    <span>{acc.flagged_count || (acc.hold_count || 0) + (acc.block_count || 0)}</span>
                    <span className="text-[10px] text-muted">
                      ({acc.block_count || 0} blk)
                    </span>
                  </span>
                </td>
                <td className="py-3 px-4 text-right font-bold text-ink-900 tabular-nums">
                  {formatINR(acc.total_flagged_amount ?? (acc.flagged_count || 1) * 45000)}
                </td>
                <td className="py-3 px-4 text-center">
                  <RiskScoreBadge score={acc.avg_risk_score || 85} />
                </td>
              </tr>
            ))}

            {accounts.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-muted font-mono text-xs">
                  No high-risk mule or aggregator accounts identified in the current evaluation window.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
