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
  const STATUSES = ["ALL", "OPEN", "REVIEWED", "ESCALATED", "DISMISSED", "RESOLVED"];

  return (
    <div className="panel p-4 space-y-4">
      {/* Top row: Search input + Status Dropdown + Sort + Reset */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
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
            >
              ✕
            </button>
          )}
        </div>

        {/* Status Dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-mono uppercase text-muted">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="border border-hairline rounded-md px-3 py-2 text-xs font-mono font-medium bg-white focus:outline-none focus:ring-1 focus:ring-ink-900"
          >
            {STATUSES.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>

        {/* Sort selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-mono uppercase text-muted">Sort:</label>
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
            className="text-xs text-saffron hover:underline font-mono px-2 py-1 ml-auto"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Bottom row: Verdict Pills + Risk Score Range Slider */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-hairline">
        {/* Verdict Pills */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-mono uppercase text-muted mr-1.5">Verdict:</span>
          {VERDICTS.map((v) => {
            const active = verdictFilter === v;
            let activeColor = "bg-ink-900 text-white";
            if (active && v === "HOLD") activeColor = "bg-verdict-hold text-white";
            if (active && v === "BLOCK") activeColor = "bg-verdict-block text-white";
            if (active && v === "ALLOW") activeColor = "bg-verdict-allow text-white";

            return (
              <button
                key={v}
                onClick={() => onVerdictFilterChange(v)}
                className={`px-3 py-1 rounded-full text-xs font-semibold font-mono transition-colors border ${
                  active
                    ? `${activeColor} border-transparent shadow-sm`
                    : "bg-surface-muted text-muted border-hairline hover:bg-white hover:text-ink-900"
                }`}
              >
                {v}
              </button>
            );
          })}
        </div>

        {/* Risk Threshold Slider */}
        <div className="flex items-center gap-3 min-w-[220px]">
          <span className="text-xs font-mono uppercase text-muted">
            Min Risk: <strong className="text-ink-900 font-bold">{minRisk}</strong>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={minRisk}
            onChange={(e) => onMinRiskChange(Number(e.target.value))}
            className="w-32 accent-saffron"
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
