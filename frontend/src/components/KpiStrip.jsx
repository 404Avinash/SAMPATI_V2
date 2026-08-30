import React from "react";
import { motion } from "framer-motion";
import { useCountUp } from "../hooks/useCountUp";

const TILES = [
  { key: "evaluated", label: "Evaluated", icon: "⌁", tone: "text-ink-800 bg-ink-900/5" },
  { key: "allowed", label: "Allowed", icon: "✓", tone: "text-verdict-allow bg-verdict-allowBg" },
  { key: "held", label: "Held", icon: "⚑", tone: "text-verdict-hold bg-verdict-holdBg" },
  { key: "blocked", label: "Blocked", icon: "✕", tone: "text-verdict-block bg-verdict-blockBg" },
  { key: "honeypot_hits", label: "Honeypot Hits (24h)", icon: "🍯", tone: "text-amber-800 bg-amber-50" },
  { key: "rings", label: "Mule rings", icon: "◈", tone: "text-purple-700 bg-purple-50" },
  { key: "dpip", label: "Sent to DPIP", icon: "⇄", tone: "text-ink-800 bg-ink-900/5" },
];

export default function KpiStrip({ stats = {} }) {
  const getTileValue = (key) => {
    if (key === "honeypot_hits") {
      return (
        stats.honeypot_hits ??
        stats.honeypot_hits_24h ??
        stats.honeypots?.total_hits ??
        stats.honeypots?.hits_24h ??
        0
      );
    }
    return stats[key] ?? 0;
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
      {TILES.map((tile) => (
        <Tile key={tile.key} tile={tile} value={getTileValue(tile.key)} />
      ))}
    </div>
  );
}

function Tile({ tile, value }) {
  const animated = useCountUp(value);
  const pulse = (tile.key === "blocked" || tile.key === "honeypot_hits") && value > 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`panel flex items-center gap-3 px-4 py-3 ${pulse ? "shadow-glow-red" : ""}`}
    >
      <div className={`w-9 h-9 rounded-md flex items-center justify-center text-lg ${tile.tone}`}>
        {tile.icon}
      </div>
      <div>
        <div className="font-serif text-xl font-semibold tabular-nums leading-none">{animated}</div>
        <div className="text-[11px] uppercase tracking-wide text-muted mt-1">{tile.label}</div>
      </div>
    </motion.div>
  );
}
