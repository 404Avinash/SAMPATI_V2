import React, { useState, useMemo } from "react";
import { formatINR, shortVpa, getDmvTone } from "../../services/api";

const DEFAULT_TOP_DMV = [
  {
    vpa: "dormant.cashout.hub88@okhdfcbank",
    bank: "HDFC Bank",
    dmv_score: 94.2,
    dormancy_days: 84,
    outflow_rate: "98% in 6m",
    amount: 1850000,
    case_id: "CASE_DMV_942_01",
  },
  {
    vpa: "mule.revival.node01@icici",
    bank: "ICICI Bank",
    dmv_score: 88.6,
    dormancy_days: 62,
    outflow_rate: "95% in 11m",
    amount: 1420000,
    case_id: "CASE_DMV_886_02",
  },
  {
    vpa: "silent.sleeper.fund@oksbi",
    bank: "State Bank of India",
    dmv_score: 81.0,
    dormancy_days: 51,
    outflow_rate: "91% in 15m",
    amount: 980000,
    case_id: "CASE_DMV_810_03",
  },
  {
    vpa: "rapid.drain.syndicate@okaxis",
    bank: "Axis Bank",
    dmv_score: 76.4,
    dormancy_days: 43,
    outflow_rate: "89% in 18m",
    amount: 750000,
    case_id: "CASE_DMV_764_04",
  },
  {
    vpa: "burst.transfers.hub@paytm",
    bank: "Paytm Payments Bank",
    dmv_score: 68.2,
    dormancy_days: 28,
    outflow_rate: "74% in 25m",
    amount: 480000,
    case_id: "CASE_DMV_682_05",
  },
  {
    vpa: "smurf.inflow.collector@ybl",
    bank: "Yes Bank",
    dmv_score: 59.5,
    dormancy_days: 21,
    outflow_rate: "65% in 30m",
    amount: 320000,
    case_id: "CASE_DMV_595_06",
  },
  {
    vpa: "mule.staging.acc44@kotak",
    bank: "Kotak Mahindra",
    dmv_score: 46.8,
    dormancy_days: 14,
    outflow_rate: "52% in 40m",
    amount: 210000,
    case_id: "CASE_DMV_468_07",
  },
];

export default function TopDmvAccountsTable({ accounts = [], onSelectAccount }) {
  const [sortField, setSortField] = useState("dmv_score");
  const [sortAsc, setSortAsc] = useState(false);

  const rawList = Array.isArray(accounts) && accounts.length > 0 ? accounts : DEFAULT_TOP_DMV;

  const sortedList = useMemo(() => {
    const arr = [...rawList];
    arr.sort((a, b) => {
      let valA, valB;
      switch (sortField) {
        case "vpa":
          valA = (a.vpa || "").toLowerCase();
          valB = (b.vpa || "").toLowerCase();
          break;
        case "bank":
          valA = (a.bank || "").toLowerCase();
          valB = (b.bank || "").toLowerCase();
          break;
        case "dmv_score":
          valA = Number(a.dmv_score ?? a.score ?? 0);
          valB = Number(b.dmv_score ?? b.score ?? 0);
          break;
        case "dormancy_days":
          valA = Number(a.dormancy_days ?? 0);
          valB = Number(b.dormancy_days ?? 0);
          break;
        case "outflow_rate":
          valA = parseFloat(a.outflow_rate ?? 0) || 0;
          valB = parseFloat(b.outflow_rate ?? 0) || 0;
          break;
        case "amount":
          valA = Number(a.amount ?? a.total_flagged_amount ?? a.total_amount ?? 0);
          valB = Number(b.amount ?? b.total_flagged_amount ?? b.total_amount ?? 0);
          break;
        default:
          valA = Number(a.dmv_score ?? a.score ?? 0);
          valB = Number(b.dmv_score ?? b.score ?? 0);
      }

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
    return arr;
  }, [rawList, sortField, sortAsc]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc((prev) => !prev);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const renderSortIndicator = (field) => {
    if (sortField !== field) {
      return <span className="text-[9px] opacity-30 ml-1 inline-block">↕</span>;
    }
    return (
      <span className="text-[10px] text-ink-900 font-bold ml-1 inline-block">
        {sortAsc ? "▲" : "▼"}
      </span>
    );
  };

  return (
    <div className="panel overflow-hidden">
      {/* Header */}
      <div className="panel-header flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            Mule Signature Metric · Dormancy vs Sudden Outflow
          </div>
          <div className="font-serif font-bold text-ink-900 text-base sm:text-lg">
            Top VPAs by Dormant-to-Active Velocity (DAV)
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-semibold">
            {sortedList.length} High-Velocity VPAs
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs border-collapse">
          <thead>
            <tr className="bg-surface-muted/70 text-muted uppercase text-[10px] border-b border-hairline tracking-wider select-none">
              <th className="py-3 px-4 font-semibold w-12 text-center">Rank</th>
              <th
                onClick={() => handleSort("vpa")}
                className="py-3 px-4 font-semibold cursor-pointer hover:text-ink-900 transition-colors"
              >
                <div className="flex items-center">
                  <span>VPA Identifier</span>
                  {renderSortIndicator("vpa")}
                </div>
              </th>
              <th
                onClick={() => handleSort("bank")}
                className="py-3 px-4 font-semibold cursor-pointer hover:text-ink-900 transition-colors"
              >
                <div className="flex items-center">
                  <span>Banking Entity</span>
                  {renderSortIndicator("bank")}
                </div>
              </th>
              <th
                onClick={() => handleSort("dmv_score")}
                className="py-3 px-4 font-semibold text-center cursor-pointer hover:text-ink-900 transition-colors"
              >
                <div className="flex items-center justify-center">
                  <span>DMV Score</span>
                  {renderSortIndicator("dmv_score")}
                </div>
              </th>
              <th
                onClick={() => handleSort("dormancy_days")}
                className="py-3 px-4 font-semibold text-center cursor-pointer hover:text-ink-900 transition-colors"
              >
                <div className="flex items-center justify-center">
                  <span>Dormancy</span>
                  {renderSortIndicator("dormancy_days")}
                </div>
              </th>
              <th
                onClick={() => handleSort("outflow_rate")}
                className="py-3 px-4 font-semibold text-center cursor-pointer hover:text-ink-900 transition-colors"
              >
                <div className="flex items-center justify-center">
                  <span>Drain Velocity</span>
                  {renderSortIndicator("outflow_rate")}
                </div>
              </th>
              <th
                onClick={() => handleSort("amount")}
                className="py-3 px-4 font-semibold text-right cursor-pointer hover:text-ink-900 transition-colors"
              >
                <div className="flex items-center justify-end">
                  <span>Protected Volume</span>
                  {renderSortIndicator("amount")}
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {sortedList.map((item, idx) => {
              const score = Number(item.dmv_score ?? item.score ?? 75);
              const tone = getDmvTone(score);

              return (
                <tr
                  key={item.vpa || idx}
                  onClick={() => onSelectAccount && onSelectAccount(item)}
                  className={`hover:bg-surface-muted/60 transition-colors ${
                    onSelectAccount ? "cursor-pointer" : ""
                  }`}
                >
                  {/* Rank */}
                  <td className="py-3 px-4 text-center font-bold text-muted">
                    <span
                      className={`inline-block w-5 h-5 rounded-full text-[10px] leading-5 text-center ${
                        idx < 3 ? "bg-ink-900 text-white" : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {idx + 1}
                    </span>
                  </td>

                  {/* VPA */}
                  <td className="py-3 px-4 font-bold text-ink-900 truncate max-w-[200px]" title={item.vpa}>
                    {shortVpa(item.vpa)}
                  </td>

                  {/* Bank */}
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-semibold border border-slate-200 inline-block">
                      {item.bank || (item.vpa?.includes("@") ? item.vpa.split("@")[1] : "UPI Rail")}
                    </span>
                  </td>

                  {/* DMV Score Badge with Inline Mini Progress Bar */}
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-12 sm:w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60 shrink-0">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            score > 70 ? "bg-rose-600" : score >= 40 ? "bg-amber-500" : "bg-emerald-600"
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                        />
                      </div>
                      <div className="inline-flex items-center gap-1">
                        <span
                          className={`px-1.5 py-0.5 rounded font-bold border text-xs ${tone.bg} ${tone.text} ${tone.border}`}
                        >
                          {score.toFixed(1)}
                        </span>
                        <span className="text-[9px] text-muted hidden 2xl:inline">{tone.label}</span>
                      </div>
                    </div>
                  </td>

                  {/* Dormancy */}
                  <td className="py-3 px-4 text-center text-slate-700 font-semibold">
                    {item.dormancy_days != null ? `${item.dormancy_days}d` : "—"}
                  </td>

                  {/* Drain Velocity */}
                  <td className="py-3 px-4 text-center text-slate-600">
                    <span className="px-1.5 py-0.5 rounded bg-slate-50 border border-slate-200 text-[11px]">
                      {item.outflow_rate || "—"}
                    </span>
                  </td>

                  {/* Protected Amount */}
                  <td className="py-3 px-4 text-right font-bold text-ink-900 tabular-nums">
                    {formatINR(item.amount ?? item.total_flagged_amount ?? item.total_amount)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer info strip */}
      <div className="px-4 py-2 bg-surface-muted/50 border-t border-hairline flex items-center justify-between text-[11px] font-mono text-muted">
        <span>DMV Formula: Score = 0.5 × DormancyFactor + 0.5 × OutflowVelocityFactor</span>
        <div className="flex items-center gap-3">
          <span className="text-emerald-700 font-bold">&lt;40 Normal</span>
          <span className="text-amber-700 font-bold">40-70 Elevated</span>
          <span className="text-rose-700 font-bold">&gt;70 Critical Mule</span>
        </div>
      </div>
    </div>
  );
}
