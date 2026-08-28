import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { formatINR } from "../services/api";

export default function CaseDrawer({ caseData, onClose, onFeedback }) {
  return (
    <AnimatePresence>
      {caseData && (
        <motion.div
          className="fixed inset-0 z-40 flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-ink-900/40" onClick={onClose} />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 260 }}
            className="relative w-full max-w-xl bg-white h-full shadow-2xl overflow-y-auto"
          >
            <div className="sticky top-0 bg-white border-b border-hairline px-5 py-4 flex items-center justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-wide text-muted">Case File</div>
                <div className="font-serif font-semibold text-ink-900">{caseData.case_id}</div>
              </div>
              <button onClick={onClose} className="text-muted hover:text-ink-900 text-xl leading-none">
                ×
              </button>
            </div>

            <div className="p-5 space-y-5">
              {caseData.token_economy && (
                <div className="grid grid-cols-3 gap-2 text-center">
                  <Stat label="Raw tokens" value={caseData.token_economy.raw_tokens} />
                  <Stat label="Vision tokens" value={caseData.token_economy.vision_tokens} />
                  <Stat
                    label="Compression"
                    value={`${(caseData.token_economy.compression_ratio || 0).toFixed(1)}×`}
                  />
                </div>
              )}

              <div>
                <div className="text-[11px] uppercase tracking-wide text-muted mb-1">Trigger transaction</div>
                <div className="text-sm bg-surface-muted rounded p-3 font-mono">
                  {caseData.trigger_txn?.payer_vpa} → {caseData.trigger_txn?.payee_vpa}
                  <br />
                  {formatINR(caseData.trigger_txn?.amount)} · risk {caseData.risk_score}
                </div>
              </div>

              {caseData.sar_markdown && (
                <div className="prose prose-sm max-w-none sar">
                  <ReactMarkdown>{caseData.sar_markdown}</ReactMarkdown>
                </div>
              )}

              <div className="flex gap-2 pt-2 border-t border-hairline">
                <button
                  onClick={() => onFeedback(caseData.case_id, true)}
                  className="btn-primary flex-1"
                >
                  Confirm fraud
                </button>
                <button
                  onClick={() => onFeedback(caseData.case_id, false)}
                  className="btn-secondary flex-1"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-surface-muted rounded p-2">
      <div className="font-serif font-semibold text-ink-900">{value ?? "—"}</div>
      <div className="text-[10px] uppercase text-muted">{label}</div>
    </div>
  );
}
