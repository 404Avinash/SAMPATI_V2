import React, { useState, useMemo, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useAppState } from "../context/AppStateContext";
import CaseFilterBar from "../components/investigations/CaseFilterBar";
import { VerdictBadge, StatusBadge, RiskScoreBadge } from "../components/common/StatusBadge";
import { formatINR, relativeTime, formatDateTime, shortVpa } from "../services/api";

export default function InvestigationsPage() {
  const { cases, openCase, runSimulation, busy } = useAppState();
  const { caseId } = useParams();

  // Filters State
  const [search, setSearch] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [minRisk, setMinRisk] = useState(0);
  const [sortBy, setSortBy] = useState("newest");

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);

  // Sync route param :caseId with openCase drawer
  useEffect(() => {
    if (caseId) {
      const found = cases.find((c) => c.case_id === caseId);
      if (found) {
        openCase(found);
      } else {
        openCase(caseId);
      }
    }
  }, [caseId, cases, openCase]);

  // Handle case selection -> opens CaseDrawer
  const handleSelectCase = (c) => {
    openCase(c);
  };

  // Filter and sort logic
  const filteredCases = useMemo(() => {
    let result = Array.isArray(cases) ? [...cases] : [];

    // Search filter
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter((c) => {
        const id = (c.case_id || "").toLowerCase();
        const payer = (c.trigger_txn?.payer_vpa || c.payer_vpa || "").toLowerCase();
        const payee = (c.trigger_txn?.payee_vpa || c.payee_vpa || "").toLowerCase();
        const ring = (c.ring_hash || "").toLowerCase();
        return id.includes(q) || payer.includes(q) || payee.includes(q) || ring.includes(q);
      });
    }

    // Verdict filter
    if (verdictFilter !== "ALL") {
      result = result.filter((c) => (c.verdict || "HOLD").toUpperCase() === verdictFilter);
    }

    // Status filter
    if (statusFilter !== "ALL") {
      result = result.filter((c) => (c.status || "OPEN").toUpperCase() === statusFilter);
    }

    // Min Risk filter
    if (minRisk > 0) {
      result = result.filter((c) => (c.risk_score || 0) >= minRisk);
    }

    // Sort
    result.sort((a, b) => {
      if (sortBy === "risk_desc") {
        return (b.risk_score || 0) - (a.risk_score || 0);
      }
      if (sortBy === "amount_desc") {
        const amtA = a.trigger_txn?.amount ?? a.amount ?? 0;
        const amtB = b.trigger_txn?.amount ?? b.amount ?? 0;
        return amtB - amtA;
      }
      if (sortBy === "oldest") {
        return new Date(a.created_at || 0) - new Date(b.created_at || 0);
      }
      // newest
      return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    });

    return result;
  }, [cases, search, verdictFilter, statusFilter, minRisk, sortBy]);

  // Pagination slicing
  const totalPages = Math.max(1, Math.ceil(filteredCases.length / pageSize));
  const paginatedCases = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCases.slice(start, start + pageSize);
  }, [filteredCases, currentPage, pageSize]);

  const handleResetFilters = () => {
    setSearch("");
    setVerdictFilter("ALL");
    setStatusFilter("ALL");
    setMinRisk(0);
    setSortBy("newest");
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl font-bold text-ink-900">
            Case Management &amp; Triage Console
          </h2>
          <p className="text-xs text-muted">
            Inspect flagged high-risk transactions, review AI SAR narratives, and dispatch RBI DPIP alerts.
          </p>
        </div>

        <button
          disabled={busy}
          onClick={() => runSimulation(250, 0.20)}
          className="btn-primary flex items-center gap-2"
        >
          <span>▶</span>
          <span>{busy ? "Simulating…" : "Generate Fraud Stream"}</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <CaseFilterBar
        search={search}
        onSearchChange={(val) => {
          setSearch(val);
          setCurrentPage(1);
        }}
        verdictFilter={verdictFilter}
        onVerdictFilterChange={(val) => {
          setVerdictFilter(val);
          setCurrentPage(1);
        }}
        statusFilter={statusFilter}
        onStatusFilterChange={(val) => {
          setStatusFilter(val);
          setCurrentPage(1);
        }}
        minRisk={minRisk}
        onMinRiskChange={(val) => {
          setMinRisk(val);
          setCurrentPage(1);
        }}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        onReset={handleResetFilters}
        totalCount={cases.length}
        filteredCount={filteredCases.length}
      />

      {/* Flagged Cases Table Panel */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-sans text-xs">
            <thead>
              <tr className="bg-surface-muted/70 text-muted uppercase text-[10px] font-mono border-b border-hairline tracking-wider">
                <th className="py-3 px-4 font-semibold">Case ID</th>
                <th className="py-3 px-4 font-semibold">Detected</th>
                <th className="py-3 px-4 font-semibold">Transaction Flow</th>
                <th className="py-3 px-4 font-semibold text-right">Amount</th>
                <th className="py-3 px-4 font-semibold text-center">Verdict</th>
                <th className="py-3 px-4 font-semibold text-center">Risk Score</th>
                <th className="py-3 px-4 font-semibold text-center">Status</th>
                <th className="py-3 px-4 font-semibold">Primary Signals</th>
                <th className="py-3 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {paginatedCases.map((c) => {
                const trigger = c.trigger_txn || {};
                const reasons = Array.isArray(c.reasons) ? c.reasons : [];
                const verdict = c.verdict || "HOLD";

                return (
                  <tr
                    key={c.case_id}
                    onClick={() => handleSelectCase(c)}
                    className="cursor-pointer hover:bg-surface-muted/60 transition-colors group"
                  >
                    {/* Case ID */}
                    <td className="py-3 px-4 font-mono font-bold text-ink-900 whitespace-nowrap">
                      <span className="group-hover:text-saffron transition-colors">
                        {c.case_id}
                      </span>
                    </td>

                    {/* Timestamp */}
                    <td className="py-3 px-4 text-muted whitespace-nowrap font-mono" title={formatDateTime(c.created_at)}>
                      {relativeTime(c.created_at)}
                    </td>

                    {/* Flow */}
                    <td className="py-3 px-4 whitespace-nowrap font-mono">
                      <span className="text-body font-medium">
                        {shortVpa(trigger.payer_vpa || c.payer_vpa)}
                      </span>
                      <span className="text-muted mx-1.5">→</span>
                      <span className="text-ink-900 font-semibold">
                        {shortVpa(trigger.payee_vpa || c.payee_vpa)}
                      </span>
                    </td>

                    {/* Amount */}
                    <td className="py-3 px-4 text-right font-mono font-bold text-ink-900 whitespace-nowrap">
                      {formatINR(trigger.amount ?? c.amount)}
                    </td>

                    {/* Verdict */}
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <VerdictBadge verdict={verdict} />
                    </td>

                    {/* Risk Score */}
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <RiskScoreBadge score={c.risk_score} />
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <StatusBadge status={c.status} />
                    </td>

                    {/* Signals */}
                    <td className="py-3 px-4 text-muted font-mono truncate max-w-[200px]" title={reasons.join(", ")}>
                      {reasons.slice(0, 2).join(", ") || "—"}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectCase(c);
                        }}
                        className="px-2.5 py-1 rounded bg-ink-900 text-white font-mono text-[11px] font-semibold hover:bg-ink-800 transition-colors shadow-sm"
                      >
                        View Dossier →
                      </button>
                    </td>
                  </tr>
                );
              })}

              {paginatedCases.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-muted font-mono space-y-3">
                    <div className="text-base font-serif text-ink-900">No matching cases found</div>
                    <p className="text-xs">Adjust your search parameters or run a new simulation batch.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-4 py-3 bg-surface-muted/40 border-t border-hairline flex flex-wrap items-center justify-between gap-4 font-mono text-xs text-muted">
          {/* Page size select */}
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="border border-hairline rounded px-2 py-1 bg-white"
            >
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </div>

          {/* Page nav */}
          <div className="flex items-center gap-3">
            <span>
              Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong> ({filteredCases.length} records)
            </span>
            <div className="flex items-center gap-1">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 rounded border border-hairline bg-white hover:bg-surface-muted disabled:opacity-40"
              >
                ‹ Prev
              </button>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 rounded border border-hairline bg-white hover:bg-surface-muted disabled:opacity-40"
              >
                Next ›
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
