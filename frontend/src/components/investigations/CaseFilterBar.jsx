import React from "react";

export default function CaseFilterBar({
  search,
  onSearchChange,
  verdictFilter,
  onVerdictFilterChange,
  statusFilter,
  onStatusFilterChange,
  minRisk,
  onMinRiskChange,
  sortBy,
  onSortByChange,
  onReset,
  totalCount,
  filteredCount,
}) {
  const VERDICTS = ["ALL", "HOLD", "BLOCK", "ALLOW"];
  const STATUSES = ["ALL", "OPEN", "ESCALATED", "DISMISSED", "REVIEWED", "RESOLVED"];

  const getStatusActiveClass = (st) => {
    switch (st) {
      case "OPEN":
        return "bg-sky-600 text-white border-sky-600 shadow-sm";
      case "ESCALATED":
        return "bg-purple-700 text-white border-purple-700 shadow-sm";
      case "DISMISSED":
        return "bg-slate-600 text-white border-slate-600 shadow-sm";
      case "REVIEWED":
        return "bg-indigo-600 text-white border-indigo-600 shadow-sm";
      case "RESOLVED":
        return "bg-emerald-600 text-white border-emerald-600 shadow-sm";
      case "ALL":
      default:
        return "bg-ink-900 text-white border-ink-900 shadow-sm";
    }
  };

  const getVerdictActiveClass = (v) => {
    switch (v) {
      case "HOLD":
        return "bg-verdict-hold text-white border-transparent shadow-sm";
      case "BLOCK":
        return "bg-verdict-block text-white border-transparent shadow-sm";
      case "ALLOW":
        return "bg-verdict-allow text-white border-transparent shadow-sm";
      case "ALL":
      default:
        return "bg-ink-900 text-white border-transparent shadow-sm";
    }
  };

  return (
    <div className="panel p-4 space-y-3 bg-white border border-hairline rounded-xl shadow-xs">
      {/* Top row: Search input + Sort Dropdown + Reset */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[260px]">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </span>
          <input
            type="text"
            placeholder="Search Case ID, Payer VPA, Payee VPA, Ring Hash…"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-hairline rounded-md text-sm font-sans focus:outline-none focus:ring-2 focus:ring-ink-900/20 focus:border-ink-900"
          />
          {search && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-muted hover:text-ink-900"
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        {/* Sort selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-mono uppercase text-muted font-semibold">Sort:</label>
          <select
            value={sortBy}
            onChange={(e) => onSortByChange(e.target.value)}
            className="border border-hairline rounded-md px-3 py-2 text-xs font-mono font-medium bg-white focus:outline-none focus:ring-1 focus:ring-ink-900"
          >
            <option value="newest">Newest First</option>
            <option value="risk_desc">Highest Risk</option>
            <option value="amount_desc">Highest Amount</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>

        {/* Reset button */}
        {(search || verdictFilter !== "ALL" || statusFilter !== "ALL" || minRisk > 0) && (
          <button
            onClick={onReset}
            className="text-xs text-saffron hover:underline font-mono px-2 py-1 ml-auto font-semibold"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Interactive Status Badges Filter Bar */}
      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-hairline">
        <span className="text-xs font-mono uppercase text-muted font-semibold mr-1">Status:</span>
        <div className="flex flex-wrap items-center gap-1.5">
          {STATUSES.map((st) => {
            const active = statusFilter === st;
            return (
              <button
                key={st}
                onClick={() => onStatusFilterChange(st)}
                className={`px-3 py-1 rounded-full text-xs font-semibold font-mono transition-all border ${
                  active
                    ? getStatusActiveClass(st)
                    : "bg-surface-muted text-muted border-hairline hover:bg-white hover:text-ink-900"
                }`}
              >
                {st}
              </button>
            );
          })}
        </div>
      </div>

      {/* Verdict Pills + Risk Score Range Slider + Counter */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-hairline">
        {/* Verdict Pills */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-mono uppercase text-muted font-semibold mr-1">Verdict:</span>
          {VERDICTS.map((v) => {
            const active = verdictFilter === v;
            return (
              <button
                key={v}
                onClick={() => onVerdictFilterChange(v)}
                className={`px-3 py-1 rounded-full text-xs font-semibold font-mono transition-all border ${
                  active
                    ? getVerdictActiveClass(v)
                    : "bg-surface-muted text-muted border-hairline hover:bg-white hover:text-ink-900"
                }`}
              >
                {v}
              </button>
            );
          })}
        </div>

        {/* Risk Threshold Slider */}
        <div className="flex items-center gap-3 min-w-[200px]">
          <span className="text-xs font-mono uppercase text-muted font-semibold">
            Min Risk: <strong className="text-ink-900 font-bold">{minRisk}</strong>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={minRisk}
            onChange={(e) => onMinRiskChange(Number(e.target.value))}
            className="w-28 accent-saffron"
          />
        </div>

        {/* Counter readout */}
        <div className="text-xs font-mono text-muted">
          Showing <span className="font-bold text-ink-900">{filteredCount}</span> of{" "}
          <span className="font-bold text-ink-900">{totalCount}</span> cases
        </div>
      </div>
    </div>
  );
}
