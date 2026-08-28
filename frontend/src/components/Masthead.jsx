import React from "react";
import { motion } from "framer-motion";

export default function Masthead({ sensitivity, live }) {
  return (
    <header className="relative bg-white border-b border-hairline">
      <div className="h-1 w-full bg-gradient-to-r from-saffron via-white to-verdict-allow" />
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <motion.div
            initial={{ rotate: -8, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            className="w-11 h-11 rounded-md bg-ink-900 flex items-center justify-center shadow-glow"
          >
            <img src="/shield.svg" alt="" className="w-7 h-7" />
          </motion.div>
          <div>
            <h1 className="font-serif text-xl font-semibold text-ink-900 flex items-baseline gap-2">
              SAMPATI
              <span className="text-saffron text-sm font-sans font-semibold tracking-wide">
                AEGIS · UPI
              </span>
            </h1>
            <p className="text-xs text-muted">
              Real-time UPI Mule-Network Interception &amp; Explainability Fabric · complementing RBI DPIP
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[11px] uppercase text-muted tracking-wide">Adaptive Sensitivity</div>
            <div className="font-mono font-semibold text-ink-900">{sensitivity.toFixed(3)}</div>
          </div>
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
              live
                ? "bg-verdict-allowBg text-verdict-allow border-verdict-allow/30"
                : "bg-surface-muted text-muted border-hairline"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${live ? "bg-verdict-allow animate-pulse" : "bg-muted"}`}
            />
            {live ? "LIVE FEED" : "IDLE"}
          </span>
        </div>
      </div>
    </header>
  );
}
