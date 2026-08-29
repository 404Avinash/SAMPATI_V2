import React, { useState } from "react";
import { api } from "../../services/api";

export default function ForensicImageViewer({ caseId }) {
  const [zoomed, setZoomed] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [loading, setLoading] = useState(true);

  if (!caseId) return null;
  const imgUrl = api.caseGraphUrl(caseId);

  return (
    <div className="panel overflow-hidden border border-hairline bg-surface-muted/30">
      <div className="panel-header flex items-center justify-between bg-white">
        <div className="panel-title">
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            Layer 4 · Visual Forensics
          </div>
          <div className="font-serif font-bold text-sm text-ink-900">
            4-Panel Forensic Graph Summary
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!loadError && (
            <button
              onClick={() => setZoomed(true)}
              className="text-xs font-mono text-muted hover:text-ink-900 flex items-center gap-1 px-2.5 py-1 rounded bg-surface-muted hover:bg-white border border-hairline transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
                />
              </svg>
              <span>Lightbox Zoom</span>
            </button>
          )}
        </div>
      </div>

      <div className="p-3 flex items-center justify-center min-h-[260px] bg-white relative">
        {loading && !loadError && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="flex items-center gap-2 text-xs font-mono text-muted">
              <span className="w-3 h-3 rounded-full border-2 border-ink-900 border-t-transparent animate-spin" />
              <span>Rendering visual graph…</span>
            </div>
          </div>
        )}

        {loadError ? (
          <div className="py-8 px-4 text-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-muted mx-auto flex items-center justify-center font-mono">
              ◈
            </div>
            <div className="text-xs font-mono text-muted">
              Visual forensics PNG pending or generated on demand
            </div>
            <button
              onClick={() => {
                setLoadError(false);
                setLoading(true);
              }}
              className="text-xs text-saffron underline font-mono"
            >
              Retry loading image
            </button>
          </div>
        ) : (
          <img
            src={imgUrl}
            alt={`Forensic summary for case ${caseId}`}
            onLoad={() => setLoading(false)}
            onError={() => {
              setLoading(false);
              setLoadError(true);
            }}
            onClick={() => setZoomed(true)}
            className="w-full max-h-[420px] object-contain rounded cursor-zoom-in hover:opacity-95 transition-opacity"
          />
        )}
      </div>

      {/* Lightbox Zoom Modal */}
      {zoomed && !loadError && (
        <div
          className="fixed inset-0 z-50 bg-ink-900/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-8"
          onClick={() => setZoomed(false)}
        >
          <div
            className="relative max-w-5xl w-full max-h-[92vh] bg-white rounded-xl shadow-2xl p-4 overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-hairline">
              <div className="font-serif font-bold text-ink-900">
                4-Panel Forensic Evidence Dossier · {caseId}
              </div>
              <button
                onClick={() => setZoomed(false)}
                className="w-8 h-8 rounded-md flex items-center justify-center text-muted hover:text-ink-900 text-xl font-bold leading-none"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-2 flex items-center justify-center">
              <img
                src={imgUrl}
                alt="Forensic Evidence High Res"
                className="max-w-full max-h-[80vh] object-contain rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
