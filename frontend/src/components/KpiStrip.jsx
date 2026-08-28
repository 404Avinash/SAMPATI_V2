import React from "react";
import { motion } from "framer-motion";
import { useCountUp } from "../hooks/useCountUp";

const TILES = [
  { key: "evaluated", label: "Evaluated", icon: "⌁", tone: "text-ink-800 bg-ink-900/5" },
  { key: "allowed", label: "Allowed", icon: "✓", tone: "text-verdict-allow bg-verdict-allowBg" },
  { key: "held", label: "Held", icon: "⚑", tone: "text-verdict-hold bg-verdict-holdBg" },
  { key: "blocked", label: "Blocked", icon: "✕", tone: "text-verdict-block bg-verdict-blockBg" },
  { key: "rings", label: "Mule rings", icon: "◈", tone: "text-purple-700 bg-purple-50" },
  { key: "dpip", label: "Sent to DPIP", icon: "⇄", tone: "text-ink-800 bg-ink-900/5" },
];

export default function KpiStrip({ stats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
      {TILES.map((tile) => (
        <Tile key={tile.key} tile={tile} value={stats[tile.key] || 0} />
      ))}
    </div>
  );
}

function Tile({ tile, value }) {
  const animated = useCountUp(value);
  const pulse = tile.key === "blocked" && value > 0;
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
