import React, { useState } from "react";
import { useAppState } from "../../context/AppStateContext";

export default function StatusTransitionActions({ caseData, onActionComplete }) {
  const { updateCaseStatus, handleFeedback } = useAppState();
  const [notes, setNotes] = useState("");
  const [loadingAction, setLoadingAction] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState(null);

  if (!caseData) return null;
  const currentStatus = (caseData.status || "OPEN").toUpperCase();

  const handleStatusChange = async (targetStatus, isFeedback = null, publishDpip = false) => {
    setLoadingAction(targetStatus);
    setFeedbackSuccess(null);
    try {
      if (isFeedback !== null) {
        await handleFeedback(caseData.case_id, isFeedback);
      }
      await updateCaseStatus(caseData.case_id, {
        status: targetStatus.toLowerCase(),
        notes: notes || `Analyst action: ${targetStatus}`,
        resolution_notes: notes,
        resolution:
          targetStatus === "DISMISSED"
            ? "RESOLVED_LEGITIMATE"
            : targetStatus === "ESCALATED"
            ? "ESCALATED_RBI_DPIP"
            : "REVIEWED_COMPLIANCE",
        escalate_to_dpip: publishDpip,
      });

      setFeedbackSuccess(`Case updated to ${targetStatus}`);
      onActionComplete?.(targetStatus);
    } catch (err) {
      console.error("Failed status action", err);
      alert(`Error updating case: ${err.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="panel p-5 bg-surface-muted/30 border border-hairline space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase text-muted">Triage Workflow</div>
          <div className="font-serif font-bold text-sm text-ink-900">
            Investigator Actions &amp; Status Transitions
          </div>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-white border border-hairline text-muted">
          Current Status: <strong className="text-ink-900">{currentStatus}</strong>
        </span>
      </div>

      {/* Analyst Notes Input */}
      <div>
        <label className="block text-xs font-mono text-muted mb-1 uppercase">
          Analyst Review Notes / Resolution Rationale:
        </label>
        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Enter investigation findings, DPIP intelligence references, or justification…"
          className="w-full text-xs font-sans p-2.5 rounded border border-hairline bg-white focus:outline-none focus:ring-1 focus:ring-ink-900"
        />
      </div>

      {/* Action Buttons Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-1">
        {/* 1. Mark Reviewed */}
        <button
          disabled={loadingAction !== null || currentStatus === "REVIEWED"}
          onClick={() => handleStatusChange("REVIEWED")}
          className="px-3 py-2 rounded-md bg-white border border-hairline text-xs font-semibold text-ink-900 hover:bg-slate-50 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-sm"
        >
          <span>✓</span>
          <span>{loadingAction === "REVIEWED" ? "Updating…" : "Mark as Reviewed"}</span>
        </button>

        {/* 2. Escalate to DPIP */}
        <button
          disabled={loadingAction !== null || currentStatus === "ESCALATED"}
          onClick={() => handleStatusChange("ESCALATED", null, true)}
          className="px-3 py-2 rounded-md bg-purple-700 hover:bg-purple-800 text-white text-xs font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-sm"
        >
          <span>⇄</span>
          <span>{loadingAction === "ESCALATED" ? "Publishing…" : "Escalate to DPIP"}</span>
        </button>

        {/* 3. Confirm Mule Ring */}
        <button
          disabled={loadingAction !== null}
          onClick={() => handleStatusChange("RESOLVED", true)}
          className="px-3 py-2 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-sm"
        >
          <span>✕</span>
          <span>{loadingAction === "RESOLVED" ? "Recording…" : "Confirm Fraud / Mule"}</span>
        </button>

        {/* 4. Dismiss as False Positive */}
        <button
          disabled={loadingAction !== null || currentStatus === "DISMISSED"}
          onClick={() => handleStatusChange("DISMISSED", false)}
          className="px-3 py-2 rounded-md bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 text-xs font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-sm"
        >
          <span>⊘</span>
          <span>{loadingAction === "DISMISSED" ? "Dismissing…" : "Dismiss False Pos"}</span>
        </button>
      </div>

      {feedbackSuccess && (
        <div className="text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-2 text-center">
          ✓ {feedbackSuccess}
        </div>
      )}
    </div>
  );
}
