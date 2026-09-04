import React, { useState, useEffect, useMemo, useRef } from "react";

// ─── Mercator projection helpers ──────────────────────────────────────────────
// India bounding box: lat 6.4°N – 35.7°N, lon 68.1°E – 97.4°E
const MAP_W = 700;
const MAP_H = 720;
const LAT_MIN = 6.4, LAT_MAX = 36.0;
const LON_MIN = 68.0, LON_MAX = 97.5;

function project(lat, lon) {
  const x = ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * MAP_W;
  // Mercator — flip Y (SVG 0 is top)
  const y = ((LAT_MAX - lat) / (LAT_MAX - LAT_MIN)) * MAP_H;
  return { x, y };
}

// ─── Real India boundary using approximate Mercator projected lat/lon ──────────
// This uses actual geographic coordinates for a recognisable India silhouette
const INDIA_GEO_POINTS = [
  [35.5, 76.8], [35.0, 77.6], [34.6, 78.2], [34.1, 78.8], [33.5, 79.1],
  [32.7, 79.5], [32.2, 80.2], [31.5, 80.0], [31.1, 81.3], [30.5, 81.9],
  [30.2, 82.6], [29.6, 83.2], [29.2, 84.1], [28.7, 84.9], [28.2, 85.7],
  [27.8, 86.5], [27.4, 87.1], [27.0, 88.0], [26.7, 88.8], [26.5, 89.6],
  [26.8, 90.4], [26.9, 91.3], [26.7, 92.0], [26.2, 93.2], [25.8, 94.0],
  [25.3, 94.7], [24.8, 95.3], [24.2, 95.9], [23.6, 96.5], [22.9, 97.3],
  [22.0, 97.4], [21.4, 96.8], [20.8, 96.2], [20.5, 95.4], [20.2, 94.6],
  [19.9, 93.8], [19.4, 93.1], [18.8, 92.6], [18.2, 92.1], [17.7, 92.4],
  [17.3, 93.2], [16.9, 94.0], [16.3, 94.6], [15.7, 95.1], [15.1, 95.5],
  [14.5, 95.2], [14.0, 94.6], [13.4, 94.0], [12.8, 93.3], [12.2, 92.7],
  [11.6, 92.2], [11.1, 91.6], [10.7, 91.0], [10.3, 90.2], [10.0, 89.3],
  [9.7, 88.3], [9.4, 87.3], [9.2, 86.2], [9.0, 85.0], [8.9, 83.8],
  [8.5, 82.7], [8.2, 81.6], [8.0, 80.5], [8.1, 79.4], [8.4, 78.3],
  [8.9, 77.2], [9.5, 76.3], [10.2, 75.5], [10.9, 76.0], [11.5, 76.7],
  [11.8, 77.5], [11.6, 78.4], [11.0, 79.2], [10.5, 80.2], [10.2, 81.1],
  [10.0, 82.0], [9.8, 82.9], [9.5, 83.8], [9.2, 84.7], [8.9, 85.6],
  [8.1, 77.5], [8.4, 77.0], [9.0, 76.5], [9.8, 76.2], [10.5, 76.0],
  [11.2, 75.7], [12.0, 75.0], [12.8, 74.7], [13.5, 74.8], [14.2, 74.3],
  [14.8, 74.1], [15.3, 73.9], [15.9, 73.7], [16.5, 73.5], [17.1, 73.4],
  [17.7, 73.0], [18.3, 72.8], [18.9, 72.7], [19.5, 72.6], [20.1, 72.8],
  [20.7, 73.0], [21.3, 73.0], [21.8, 72.6], [22.3, 72.2], [22.7, 71.5],
  [23.0, 70.7], [23.3, 70.0], [23.5, 69.2], [23.7, 68.3], [24.0, 68.2],
  [24.6, 68.1], [25.2, 68.5], [25.7, 69.0], [26.1, 69.8], [26.5, 70.6],
  [27.0, 71.3], [27.6, 72.0], [28.1, 72.7], [28.6, 73.5], [29.1, 74.2],
  [29.6, 74.9], [30.2, 75.5], [30.8, 75.9], [31.4, 76.4], [32.0, 76.6],
  [32.6, 76.8], [33.2, 76.5], [33.7, 76.0], [34.2, 75.5], [34.7, 75.1],
  [35.2, 76.0], [35.5, 76.8],
];

const INDIA_SVG_PATH = (() => {
  const pts = INDIA_GEO_POINTS.map(([lat, lon]) => project(lat, lon));
  return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ") + " Z";
})();

// ─── City hubs ────────────────────────────────────────────────────────────────
const HUBS = [
  { id: "DELHI",     name: "Delhi NCR",  lat: 28.70, lon: 77.10, role: "High-Value Target Inflow",         isTarget: true,  activeCases: 14, volume: "₹1.42 Cr" },
  { id: "MEWAT",     name: "Mewat",      lat: 28.06, lon: 76.99, role: "SIM-Swap Syndicate Epicenter",     isHotspot: true, activeCases: 29, volume: "₹1.85 Cr" },
  { id: "JAMTARA",   name: "Jamtara",    lat: 24.00, lon: 86.79, role: "Phishing Origin & Mule Sinks",     isHotspot: true, activeCases: 42, volume: "₹3.10 Cr" },
  { id: "MUMBAI",    name: "Mumbai",     lat: 19.08, lon: 72.88, role: "Financial Gateway & PSP Node",     isTarget: true,  activeCases: 8,  volume: "₹0.98 Cr" },
  { id: "BENGALURU", name: "Bengaluru",  lat: 12.97, lon: 77.59, role: "Tech Hub — Device Farm Activity", isTarget: true,  activeCases: 6,  volume: "₹0.74 Cr" },
  { id: "KOLKATA",   name: "Kolkata",    lat: 22.57, lon: 88.36, role: "Eastern Mule Relay Node",         isHotspot: true, activeCases: 11, volume: "₹1.12 Cr" },
  { id: "AHMEDABAD", name: "Ahmedabad",  lat: 23.02, lon: 72.57, role: "Structuring Hub",                 activeCases: 5,  volume: "₹0.61 Cr" },
  { id: "HYDERABAD", name: "Hyderabad",  lat: 17.38, lon: 78.49, role: "Coordinator Node",                activeCases: 7,  volume: "₹0.82 Cr" },
  { id: "CHENNAI",   name: "Chennai",    lat: 13.08, lon: 80.27, role: "Southern Inflow Sink",            activeCases: 4,  volume: "₹0.53 Cr" },
].map(h => ({ ...h, ...project(h.lat, h.lon) }));

// Named export alias for backward compatibility with TopologyPage
export const INDIAN_HUBS = HUBS;


// ─── Mule corridors ───────────────────────────────────────────────────────────
const CORRIDORS = [
  { from: "JAMTARA",   to: "DELHI",     risk: "CRITICAL", label: "Phishing → Target" },
  { from: "MEWAT",     to: "DELHI",     risk: "CRITICAL", label: "SIM-Swap → Target" },
  { from: "JAMTARA",   to: "KOLKATA",   risk: "HIGH",     label: "Eastern Relay"     },
  { from: "KOLKATA",   to: "MUMBAI",    risk: "HIGH",     label: "Cross-Regional"    },
  { from: "MUMBAI",    to: "AHMEDABAD", risk: "HIGH",     label: "Structuring Route" },
  { from: "HYDERABAD", to: "CHENNAI",   risk: "HIGH",     label: "Southern Corridor" },
  { from: "DELHI",     to: "MUMBAI",    risk: "HIGH",     label: "Hub-to-Gateway"    },
  { from: "BENGALURU", to: "HYDERABAD", risk: "HIGH",     label: "Tech-Hub Relay"    },
  { from: "JAMTARA",   to: "HYDERABAD", risk: "HIGH",     label: "Central Relay"     },
];

function getHub(id) { return HUBS.find(h => h.id === id); }

function quadraticBezierMid(x1, y1, x2, y2, bend = 0.35) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  return { cx: mx - dy * bend, cy: my + dx * bend };
}

const RISK_COLORS = {
  CRITICAL: { stroke: "#dc2626", glow: "#ef4444", label: "text-rose-600" },
  HIGH:     { stroke: "#c8641e", glow: "#f97316", label: "text-orange-600" },
};

export default function GeoMuleMap({ cases = [] }) {
  const [hoveredHub, setHoveredHub] = useState(null);
  const [hoveredCorridor, setHoveredCorridor] = useState(null);
  const [filter, setFilter] = useState("ALL");
  const [tick, setTick] = useState(0);

  // Animate particles
  useEffect(() => {
    const id = setInterval(() => setTick(t => (t + 1) % 100), 80);
    return () => clearInterval(id);
  }, []);

  const visibleCorridors = useMemo(() =>
    filter === "ALL" ? CORRIDORS : CORRIDORS.filter(c => c.risk === filter),
    [filter]
  );

  const hovered = hoveredHub ? HUBS.find(h => h.id === hoveredHub) : null;

  return (
    <div className="relative w-full flex flex-col bg-white rounded-lg border border-hairline overflow-hidden shadow-xs select-none" style={{ minHeight: 520 }}>

      {/* Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-gray-50 border-b border-hairline text-xs font-mono">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-gray-500 font-semibold">Corridors:</span>
            <span className="font-bold text-gray-900">{visibleCorridors.length} Active</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-gray-500">Hubs:</span>
            <span className="font-bold text-gray-900">{HUBS.length} Monitored</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-gray-500">Intercepted:</span>
            <span className="font-bold text-rose-600">₹6.78 Cr</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-gray-500">Live Rings:</span>
            <span className="font-bold text-indigo-700">50</span>
          </span>
        </div>
        <div className="flex items-center gap-1 bg-white border border-gray-200 rounded p-0.5 text-[10px]">
          {["ALL", "CRITICAL", "HIGH"].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 rounded font-semibold transition-all ${filter === f ? "bg-gray-900 text-white" : "text-gray-500 hover:text-gray-900"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Map SVG */}
      <div className="relative flex-1 flex items-center justify-center p-4 bg-slate-50">
        <svg
          viewBox={`0 0 ${MAP_W} ${MAP_H}`}
          className="w-full h-full"
          style={{ maxHeight: 460 }}
        >
          <defs>
            <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <filter id="softglow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            {/* Grid lines */}
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" strokeWidth="0.5" />
            </pattern>
          </defs>

          {/* Background grid */}
          <rect width={MAP_W} height={MAP_H} fill="url(#grid)" />

          {/* India map border — filled with a very light tint */}
          <path
            d={INDIA_SVG_PATH}
            fill="#f1f5f9"
            stroke="#94a3b8"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />

          {/* Corridor arcs */}
          {visibleCorridors.map((c, i) => {
            const f = getHub(c.from);
            const t = getHub(c.to);
            if (!f || !t) return null;
            const { cx, cy } = quadraticBezierMid(f.x, f.y, t.x, t.y, 0.3);
            const col = RISK_COLORS[c.risk];
            const isHovered = hoveredCorridor === i;

            // Particle position along bezier (parametric t = tick/100)
            const pt = (tick / 100 + i * 0.15) % 1;
            const px = (1 - pt) * (1 - pt) * f.x + 2 * (1 - pt) * pt * cx + pt * pt * t.x;
            const py = (1 - pt) * (1 - pt) * f.y + 2 * (1 - pt) * pt * cy + pt * pt * t.y;

            return (
              <g key={i} onMouseEnter={() => setHoveredCorridor(i)} onMouseLeave={() => setHoveredCorridor(null)} style={{ cursor: "pointer" }}>
                {/* Glow trail */}
                <path
                  d={`M ${f.x} ${f.y} Q ${cx} ${cy} ${t.x} ${t.y}`}
                  fill="none"
                  stroke={col.glow}
                  strokeWidth={isHovered ? 5 : 3}
                  strokeOpacity={0.15}
                  filter="url(#glow)"
                />
                {/* Main line */}
                <path
                  d={`M ${f.x} ${f.y} Q ${cx} ${cy} ${t.x} ${t.y}`}
                  fill="none"
                  stroke={col.stroke}
                  strokeWidth={isHovered ? 2.5 : 1.5}
                  strokeOpacity={isHovered ? 1 : 0.7}
                  strokeDasharray={c.risk === "CRITICAL" ? "none" : "6 4"}
                />
                {/* Traveling particle */}
                <circle cx={px} cy={py} r={isHovered ? 5 : 3.5} fill={col.glow} opacity={0.9} filter="url(#softglow)" />

                {/* Corridor label on hover */}
                {isHovered && (
                  <text
                    x={cx}
                    y={cy - 10}
                    textAnchor="middle"
                    fontSize={10}
                    fill={col.stroke}
                    fontFamily="monospace"
                    fontWeight="bold"
                    style={{ pointerEvents: "none" }}
                  >
                    {c.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* City hub dots */}
          {HUBS.map(hub => {
            const isHov = hoveredHub === hub.id;
            const nodeColor = hub.isHotspot ? "#dc2626" : hub.isTarget ? "#3b82f6" : "#6366f1";
            return (
              <g
                key={hub.id}
                onMouseEnter={() => setHoveredHub(hub.id)}
                onMouseLeave={() => setHoveredHub(null)}
                style={{ cursor: "pointer" }}
              >
                {/* Pulse ring */}
                {(hub.isHotspot || hub.isTarget) && (
                  <circle
                    cx={hub.x} cy={hub.y}
                    r={isHov ? 22 : 16}
                    fill="none"
                    stroke={nodeColor}
                    strokeWidth={1}
                    strokeOpacity={isHov ? 0.35 : 0.2}
                    strokeDasharray="3 3"
                  />
                )}
                {/* Node dot */}
                <circle
                  cx={hub.x} cy={hub.y}
                  r={isHov ? 10 : hub.isHotspot || hub.isTarget ? 8 : 6}
                  fill={nodeColor}
                  opacity={isHov ? 1 : 0.85}
                  filter={isHov ? "url(#softglow)" : undefined}
                />
                {/* Inner dot */}
                <circle cx={hub.x} cy={hub.y} r={2.5} fill="white" opacity={0.9} />

                {/* City label */}
                <text
                  x={hub.x + 12}
                  y={hub.y + 4}
                  fontSize={isHov ? 11 : 9.5}
                  fill={isHov ? nodeColor : "#374151"}
                  fontFamily="monospace"
                  fontWeight={isHov ? "bold" : "600"}
                  style={{ pointerEvents: "none" }}
                >
                  {hub.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover tooltip */}
        {hovered && (
          <div className="absolute top-4 right-4 w-60 bg-white border border-gray-200 rounded-xl shadow-xl p-4 text-xs font-mono z-10">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2.5 h-2.5 rounded-full ${hovered.isHotspot ? "bg-rose-500" : hovered.isTarget ? "bg-blue-500" : "bg-indigo-500"}`} />
              <span className="font-bold text-gray-900 text-sm">{hovered.name}</span>
            </div>
            <div className="text-gray-500 mb-2 leading-relaxed">{hovered.role}</div>
            <div className="flex justify-between border-t border-gray-100 pt-2 mt-1">
              <div>
                <div className="text-gray-400 text-[10px] uppercase tracking-wide">Active Cases</div>
                <div className="font-bold text-gray-900">{hovered.activeCases}</div>
              </div>
              <div>
                <div className="text-gray-400 text-[10px] uppercase tracking-wide">Intercepted</div>
                <div className="font-bold text-rose-600">{hovered.volume}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 px-4 py-2.5 bg-gray-50 border-t border-gray-200 text-xs font-mono">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-rose-600" />
          <span className="text-gray-600">Phishing Epicentre</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-gray-600">Target Network</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-indigo-500" />
          <span className="text-gray-600">Switch Node</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-6 border-t-2 border-rose-600" />
          <span className="text-gray-600">Critical</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-6 border-t-2 border-orange-500 border-dashed" />
          <span className="text-gray-600">High</span>
        </span>
      </div>
    </div>
  );
}
