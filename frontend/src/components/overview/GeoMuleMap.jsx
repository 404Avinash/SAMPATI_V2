import React, { useState, useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Line,
} from "react-simple-maps";
import indiaTopo from "../../data/india-topo.json";

// ─── Calibrated Hub Definitions with Real Lat/Lon ─────────────────────────────
export const INDIAN_HUBS = [
  {
    id: "DELHI",
    name: "Delhi NCR",
    lat: 28.70,
    lon: 77.10,
    isTarget: true,
    role: "High-Value Target Inflow",
    activeCases: 14,
    volume: "₹1.42 Cr",
    labelOffsetX: 12,
    labelOffsetY: 3.5,
    labelAnchor: "start",
  },
  {
    id: "MEWAT",
    name: "Mewat",
    lat: 28.06,
    lon: 76.99,
    isHotspot: true,
    role: "SIM-Swap Syndicate Epicenter",
    activeCases: 29,
    volume: "₹1.85 Cr",
    labelOffsetX: -12,
    labelOffsetY: 3.5,
    labelAnchor: "end",
  },
  {
    id: "JAMTARA",
    name: "Jamtara",
    lat: 24.00,
    lon: 86.79,
    isHotspot: true,
    role: "Phishing Origin & Mule Sinks",
    activeCases: 42,
    volume: "₹3.10 Cr",
    labelOffsetX: 12,
    labelOffsetY: 3.5,
    labelAnchor: "start",
  },
  {
    id: "MUMBAI",
    name: "Mumbai",
    lat: 19.08,
    lon: 72.88,
    isTarget: true,
    role: "Financial Gateway & PSP Node",
    activeCases: 8,
    volume: "₹0.98 Cr",
    labelOffsetX: -12,
    labelOffsetY: 3.5,
    labelAnchor: "end",
  },
  {
    id: "BENGALURU",
    name: "Bengaluru",
    lat: 12.97,
    lon: 77.59,
    isTarget: true,
    role: "Tech Hub — Device Farm Activity",
    activeCases: 6,
    volume: "₹0.74 Cr",
    labelOffsetX: -12,
    labelOffsetY: 3.5,
    labelAnchor: "end",
  },
  {
    id: "KOLKATA",
    name: "Kolkata",
    lat: 22.57,
    lon: 88.36,
    isHotspot: true,
    role: "Eastern Mule Relay Node",
    activeCases: 11,
    volume: "₹1.12 Cr",
    labelOffsetX: 12,
    labelOffsetY: 3.5,
    labelAnchor: "start",
  },
  {
    id: "AHMEDABAD",
    name: "Ahmedabad",
    lat: 23.02,
    lon: 72.57,
    role: "Structuring Hub",
    activeCases: 5,
    volume: "₹0.61 Cr",
    labelOffsetX: -12,
    labelOffsetY: 3.5,
    labelAnchor: "end",
  },
  {
    id: "HYDERABAD",
    name: "Hyderabad",
    lat: 17.38,
    lon: 78.49,
    role: "Coordinator Node",
    activeCases: 7,
    volume: "₹0.82 Cr",
    labelOffsetX: 12,
    labelOffsetY: 3.5,
    labelAnchor: "start",
  },
  {
    id: "CHENNAI",
    name: "Chennai",
    lat: 13.08,
    lon: 80.27,
    role: "Southern Inflow Sink",
    activeCases: 4,
    volume: "₹0.53 Cr",
    labelOffsetX: 12,
    labelOffsetY: 3.5,
    labelAnchor: "start",
  },
];

const HUB_MAP = Object.fromEntries(INDIAN_HUBS.map((h) => [h.id, h]));

// ─── Calibrated Inter-State Mule Corridors ────────────────────────────────────
export const MULE_CORRIDORS = [
  { id: "JAM-DEL", from: "JAMTARA",   to: "DELHI",     risk: "CRITICAL", label: "Phishing → Primary Target",  curve: -0.16 },
  { id: "MEW-DEL", from: "MEWAT",     to: "DELHI",     risk: "CRITICAL", label: "SIM-Swap → Primary Target",  curve: 0.20  },
  { id: "JAM-KOL", from: "JAMTARA",   to: "KOLKATA",   risk: "HIGH",     label: "Eastern Relay",              curve: 0.18  },
  { id: "KOL-MUM", from: "KOLKATA",   to: "MUMBAI",    risk: "HIGH",     label: "Cross-Regional Laundering",  curve: -0.14 },
  { id: "MUM-AHM", from: "MUMBAI",    to: "AHMEDABAD", risk: "HIGH",     label: "Structuring Route",          curve: 0.18  },
  { id: "HYD-CHE", from: "HYDERABAD", to: "CHENNAI",   risk: "HIGH",     label: "Southern Corridor",          curve: -0.15 },
  { id: "DEL-MUM", from: "DELHI",     to: "MUMBAI",    risk: "HIGH",     label: "Hub-to-Gateway",             curve: -0.12 },
  { id: "BLR-HYD", from: "BENGALURU", to: "HYDERABAD", risk: "HIGH",     label: "Tech-Hub Relay",             curve: 0.16  },
  { id: "JAM-HYD", from: "JAMTARA",   to: "HYDERABAD", risk: "HIGH",     label: "Central Relay",              curve: 0.14  },
];

/**
 * GeoMuleMap renders the high-fidelity geographic fraud mesh topology of India
 * utilizing react-simple-maps with embedded offline TopoJSON cartography.
 *
 * Requirements satisfied:
 * - R1: 100% offline vector boundary rendering via react-simple-maps + TopoJSON.
 * - R2: Accurate geodetic coordinate plotting [lon, lat] of hubs, glowing bezier
 *       corridors, animated particle flows, pulsating radar epicenters, and interactive triage.
 */
export default function GeoMuleMap({ cases = [], onSelectCase }) {
  const [hoveredHub, setHoveredHub] = useState(null);
  const [hoveredCorridor, setHoveredCorridor] = useState(null);
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const safeCases = Array.isArray(cases) ? cases : [];

  const filteredCorridors = useMemo(() => {
    if (severityFilter === "ALL") return MULE_CORRIDORS;
    return MULE_CORRIDORS.filter((c) => c.risk === severityFilter);
  }, [severityFilter]);

  const activeCorridorsCount = filteredCorridors.length;
  const liveCasesCount = safeCases.length || 50;

  return (
    <div
      className="relative w-full h-full min-h-[520px] flex flex-col bg-white rounded-lg border border-hairline overflow-hidden shadow-xs select-none"
    >
      {/* Top Telemetry Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-surface-muted/90 border-b border-hairline text-xs font-mono">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-muted font-medium">Corridors:</span>
            <span className="font-bold text-ink-900">{activeCorridorsCount} Active</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            <span className="text-muted font-medium">Hubs:</span>
            <span className="font-bold text-ink-900">{INDIAN_HUBS.length} Monitored</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            <span className="text-muted font-medium">Intercepted:</span>
            <span className="font-bold text-rose-700">₹6.78 Cr</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span className="text-muted font-medium">Live Rings:</span>
            <span className="font-bold text-amber-700">{liveCasesCount}</span>
          </div>
        </div>

        {/* Right Controls & Legend */}
        <div className="flex items-center gap-4">
          {/* Severity Filter Toggle */}
          <div className="flex items-center gap-1 bg-white px-1.5 py-0.5 rounded border border-hairline text-[11px]">
            <span className="text-muted mr-1">Filter:</span>
            {["ALL", "CRITICAL", "HIGH"].map((sev) => (
              <button
                key={sev}
                type="button"
                onClick={() => setSeverityFilter(sev)}
                className={`px-1.5 py-0.5 rounded transition-colors ${
                  severityFilter === sev
                    ? "bg-slate-800 text-white font-bold"
                    : "text-muted hover:text-ink-900"
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Node Category Legend */}
          <div className="hidden lg:flex items-center gap-3 text-[11px]">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block ring-2 ring-rose-200" />
              <span className="text-muted">Phishing Epicentre</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block ring-2 ring-blue-200" />
              <span className="text-muted">Target Network</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block ring-2 ring-indigo-200" />
              <span className="text-muted">Switch Node</span>
            </span>
          </div>
        </div>
      </div>

      {/* Map Canvas Area */}
      <div className="relative flex-1 w-full bg-[#f8fafc]/50 flex items-center justify-center p-2 min-h-[480px]">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 1050,
            center: [82.5, 21.5],
          }}
          width={700}
          height={720}
          viewBox="0 0 700 720"
          className="w-full h-full max-h-[640px]"
          style={{ overflow: "visible" }}
        >
          <defs>
            {/* Dual-layer glowing arc SVG filter */}
            <filter id="arcGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Radar gradient for hotspot pulse rings */}
            <radialGradient id="radarRed" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#dc2626" stopOpacity="0.45" />
              <stop offset="60%" stopColor="#dc2626" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#dc2626" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Coordinate Graticule Guidelines & Degree Labels */}
          <g opacity="0.3" pointerEvents="none">
            <line x1="40" y1="214" x2="660" y2="214" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="40" y1="334" x2="660" y2="334" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="40" y1="407" x2="660" y2="407" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="40" y1="522" x2="660" y2="522" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="174" y1="40" x2="174" y2="680" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="251" y1="40" x2="251" y2="680" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="428" y1="40" x2="428" y2="680" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />
            <line x1="457" y1="40" x2="457" y2="680" stroke="#94a3b8" strokeDasharray="3 4" strokeWidth="0.8" />

            <text x="45" y="210" fill="#64748b" fontSize="9" fontFamily="monospace">
              28.7° N · Northern Corridor
            </text>
            <text x="45" y="330" fill="#64748b" fontSize="9" fontFamily="monospace">
              23.5° N · Tropic of Cancer
            </text>
            <text x="45" y="403" fill="#64748b" fontSize="9" fontFamily="monospace">
              19.1° N · Western Financial Rail
            </text>
            <text x="45" y="518" fill="#64748b" fontSize="9" fontFamily="monospace">
              13.0° N · Southern Tech Mesh
            </text>
          </g>

          {/* Authentic Offline TopoJSON India Cartographic Boundaries */}
          <Geographies geography={indiaTopo}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey || geo.id || "india-boundary"}
                  geography={geo}
                  fill="#f8fafc"
                  stroke="#94a3b8"
                  strokeWidth={1.6}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  className="transition-colors duration-300 drop-shadow-xs"
                  style={{
                    default: { outline: "none" },
                    hover: { fill: "#f1f5f9", outline: "none" },
                    pressed: { outline: "none" },
                  }}
                />
              ))
            }
          </Geographies>

          {/* Fraud Corridors via react-simple-maps Line component */}
          {filteredCorridors.map((c) => {
            const f = HUB_MAP[c.from];
            const t = HUB_MAP[c.to];
            if (!f || !t) return null;

            const isCritical = c.risk === "CRITICAL";
            const corridorColor = isCritical ? "#dc2626" : "#c8641e";
            const isHovered = hoveredCorridor?.id === c.id;

            return (
              <Line
                key={c.id}
                from={[f.lon, f.lat]}
                to={[t.lon, t.lat]}
                curve={c.curve}
              >
                {({ d }) => (
                  <g
                    className="cursor-pointer"
                    onMouseEnter={() => setHoveredCorridor(c)}
                    onMouseLeave={() => setHoveredCorridor(null)}
                  >
                    {/* Wider transparent hit-test stroke for smooth hovering */}
                    <path
                      d={d}
                      fill="none"
                      stroke="transparent"
                      strokeWidth="16"
                    />

                    {/* Dual-layer glowing underlay filter */}
                    <path
                      d={d}
                      fill="none"
                      stroke={corridorColor}
                      filter="url(#arcGlow)"
                      strokeWidth={isHovered ? "5.5" : "3.5"}
                      strokeOpacity={isHovered ? "0.65" : "0.32"}
                      strokeLinecap="round"
                    />

                    {/* Core directional arc line */}
                    <path
                      d={d}
                      fill="none"
                      stroke={corridorColor}
                      strokeWidth={isHovered ? "2.5" : "1.8"}
                      strokeDasharray={isCritical ? undefined : "6 4"}
                      strokeLinecap="round"
                    />

                    {/* Hardware-accelerated kinetic flow particle */}
                    <circle r={isHovered ? "4.5" : "3.2"} fill={corridorColor}>
                      <animateMotion
                        path={d}
                        dur={isCritical ? "2.2s" : "3.4s"}
                        repeatCount="indefinite"
                      />
                    </circle>
                  </g>
                )}
              </Line>
            );
          })}

          {/* Hub Markers via react-simple-maps Marker component */}
          {INDIAN_HUBS.map((hub) => {
            const isHovered = hoveredHub?.id === hub.id;
            const isHotspot = hub.isHotspot;
            const isTarget = hub.isTarget;
            const hubColor = isHotspot ? "#dc2626" : isTarget ? "#3b82f6" : "#6366f1";

            return (
              <Marker
                key={hub.id}
                coordinates={[hub.lon, hub.lat]}
                className="cursor-pointer select-none"
                onMouseEnter={() => setHoveredHub(hub)}
                onMouseLeave={() => setHoveredHub(null)}
                onClick={() => onSelectCase && onSelectCase({ hub_id: hub.id, hub: hub.name })}
              >
                {/* Radar pulse rings for hotspot epicenters (Jamtara, Mewat) */}
                {isHotspot && (
                  <g pointerEvents="none">
                    <circle cx={0} cy={0} r={20} fill="url(#radarRed)" />
                    <circle
                      cx={0}
                      cy={0}
                      r={6}
                      fill="none"
                      stroke="#dc2626"
                      strokeWidth={1.2}
                      opacity={0.75}
                    >
                      <animate
                        attributeName="r"
                        values="6;26"
                        dur="2.4s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.85;0"
                        dur="2.4s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  </g>
                )}

                {/* Outer concentric ring */}
                <circle
                  cx={0}
                  cy={0}
                  r={isHovered ? 8.5 : isHotspot ? 7 : 5.5}
                  fill="white"
                  stroke={hubColor}
                  strokeWidth={isHovered ? 2.5 : 1.8}
                  className="transition-all duration-150 shadow-sm"
                />

                {/* Inner semantic core dot */}
                <circle
                  cx={0}
                  cy={0}
                  r={isHovered ? 4.5 : isHotspot ? 3.5 : 2.5}
                  fill={hubColor}
                />

                {/* Calibrated monospace city label */}
                <text
                  x={hub.labelOffsetX}
                  y={hub.labelOffsetY}
                  textAnchor={hub.labelAnchor}
                  fontSize={isHovered ? 11 : 9.5}
                  fontWeight={isHotspot || isHovered ? "bold" : "600"}
                  fill={isHotspot ? "#991b1b" : isTarget ? "#312e81" : "#0f172a"}
                  fontFamily="monospace"
                  className="transition-all duration-150 drop-shadow-xs"
                  pointerEvents="none"
                >
                  {hub.name}
                </text>
              </Marker>
            );
          })}
        </ComposableMap>

        {/* Floating Telemetry Tooltip for Hovered Hub */}
        {hoveredHub && (
          <div
            className="absolute z-20 pointer-events-none bg-slate-900/95 text-white p-2.5 rounded-lg shadow-xl text-xs font-mono border border-white/10 max-w-xs space-y-1 backdrop-blur-xs top-4 left-4"
          >
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-1">
              <span className="font-bold text-white text-sm">{hoveredHub.name}</span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  hoveredHub.isHotspot
                    ? "bg-rose-900/80 text-rose-200 border border-rose-700"
                    : hoveredHub.isTarget
                    ? "bg-blue-900/80 text-blue-200 border border-blue-700"
                    : "bg-indigo-900/80 text-indigo-200 border border-indigo-700"
                }`}
              >
                {hoveredHub.isHotspot ? "HOTSPOT" : hoveredHub.isTarget ? "TARGET" : "NODE"}
              </span>
            </div>
            <div className="text-muted text-[11px]">{hoveredHub.role}</div>
            <div className="flex items-center justify-between pt-1 text-[11px]">
              <span className="text-slate-400">Coordinates:</span>
              <span className="text-slate-200">{hoveredHub.lat}° N, {hoveredHub.lon}° E</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Active Rings:</span>
              <span className="font-bold text-amber-400">{hoveredHub.activeCases}</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Intercepted 24h:</span>
              <span className="font-bold text-rose-400">{hoveredHub.volume}</span>
            </div>
            <div className="pt-1 text-[10px] text-slate-400 border-t border-white/10 flex items-center gap-1">
              <span>👉 Click hub to inspect active syndicate cases</span>
            </div>
          </div>
        )}

        {/* Floating Telemetry Tooltip for Hovered Corridor */}
        {hoveredCorridor && (
          <div
            className="absolute z-20 pointer-events-none bg-slate-900/95 text-white p-2.5 rounded-lg shadow-xl text-xs font-mono border border-white/10 max-w-xs space-y-1 backdrop-blur-xs bottom-4 right-4"
          >
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-1">
              <span className="font-bold text-amber-400">{hoveredCorridor.label}</span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  hoveredCorridor.risk === "CRITICAL"
                    ? "bg-rose-900/80 text-rose-200 border border-rose-700"
                    : "bg-amber-900/80 text-amber-200 border border-amber-700"
                }`}
              >
                [{hoveredCorridor.risk}]
              </span>
            </div>
            <div className="text-[11px] text-slate-300">
              Vector:{" "}
              <strong className="text-white">
                {HUB_MAP[hoveredCorridor.from]?.name}
              </strong>{" "}
              ➔{" "}
              <strong className="text-white">
                {HUB_MAP[hoveredCorridor.to]?.name}
              </strong>
            </div>
            <div className="flex items-center justify-between pt-1 text-[11px]">
              <span className="text-slate-400">Transit Type:</span>
              <span className="text-slate-200">Layering & Siphoning Corridors</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">SLA Interception:</span>
              <span className="text-emerald-400 font-bold">&lt; 450ms Real-Time</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
