import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useToast } from "../../context/ToastContext";

function ToastIcon({ type }) {
  switch (type) {
    case "success":
      return (
        <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    case "error":
      return (
        <div className="w-8 h-8 rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    case "warning":
      return (
        <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
      );
    case "info":
    default:
      return (
        <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      );
  }
}

function getBorderAccent(type) {
  switch (type) {
    case "success":
      return "border-emerald-500/40 shadow-emerald-950/40";
    case "error":
      return "border-rose-500/40 shadow-rose-950/40";
    case "warning":
      return "border-amber-500/40 shadow-amber-950/40";
    case "info":
    default:
      return "border-cyan-500/40 shadow-cyan-950/40";
  }
}

function getProgressBarColor(type) {
  switch (type) {
    case "success":
      return "bg-emerald-400";
    case "error":
      return "bg-rose-400";
    case "warning":
      return "bg-amber-400";
    case "info":
    default:
      return "bg-cyan-400";
  }
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0"
      role="region"
      aria-live="polite"
      aria-label="Notifications"
    >
      <AnimatePresence mode="sync">
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            layout
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, y: 10, transition: { duration: 0.15 } }}
            transition={{ type: "spring", stiffness: 380, damping: 25 }}
            className={`pointer-events-auto relative overflow-hidden rounded-xl bg-slate-900/95 backdrop-blur-md text-slate-100 p-3.5 shadow-2xl border ${getBorderAccent(
              t.type
            )} flex flex-col gap-1`}
          >
            <div className="flex items-start gap-3">
              <ToastIcon type={t.type} />
              <div className="flex-1 min-w-0 pr-1">
                {t.title && (
                  <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                    {t.title}
                  </div>
                )}
                <div className="text-sm font-medium text-slate-100 break-words leading-snug">
                  {t.message}
                </div>
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-slate-400 hover:text-slate-200 transition-colors p-1 -mr-1 -mt-1 rounded leading-none"
                title="Dismiss"
                aria-label="Close notification"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Timed Progress Indicator */}
            {t.duration && t.duration > 0 && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-800">
                <motion.div
                  initial={{ width: "100%" }}
                  animate={{ width: "0%" }}
                  transition={{ duration: t.duration / 1000, ease: "linear" }}
                  className={`h-full ${getProgressBarColor(t.type)}`}
                />
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
