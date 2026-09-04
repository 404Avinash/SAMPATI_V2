import React, { useState, useMemo } from "react";

/**
 * Calibrated Indian Financial & Threat Hubs
 * SVG Coordinates normalized to viewBox 0 0 600 680
 */
export const INDIAN_HUBS = [
  {
    id: "DELHI",
    name: "Delhi NCR",
    state: "NCR",
    x: 235,
    y: 195,
    role: "High-Value Target Inflow",
    activeCases: 14,
    volume: "₹1.42 Cr",
    isTarget: true,
  },
  {
    id: "MEWAT",
    name: "Mewat",
    state: "Haryana",
    x: 230,
    y: 225,
    role: "SIM-Swap Syndicate Epicenter",
    activeCases: 29,
    volume: "₹1.85 Cr",
    isHotspot: true,
  },
  {
    id: "JAMTARA",
    name: "Jamtara",
    state: "Jharkhand",
    x: 420,
    y: 325,
    role: "Phishing Origin & Mule Sinks",
    activeCases: 42,
    volume: "₹3.10 Cr",
    isHotspot: true,
  },
  {
    id: "MUMBAI",
    name: "Mumbai",
    state: "Maharashtra",
    x: 155,
    y: 430,
    role: "Financial Clearing / Cash-Out",
    activeCases: 38,
    volume: "₹2.65 Cr",
    isTarget: true,
  },
  {
    id: "AHMEDABAD",
    name: "Ahmedabad",
    state: "Gujarat",
    x: 140,
    y: 345,
    role: "Layering & Smurfing Conduit",
    activeCases: 18,
    volume: "₹92 L",
  },
  {
    id: "KOLKATA",
    name: "Kolkata",
    state: "West Bengal",
    x: 450,
    y: 365,
    role: "Eastern Aggregation Gateway",
    activeCases: 16,
    volume: "₹78 L",
  },
  {
    id: "HYDERABAD",
    name: "Hyderabad",
    state: "Telangana",
    x: 265,
    y: 475,
    role: "P2P Relay Node",
    activeCases: 12,
    volume: "₹64 L",
  },
  {
    id: "BENGALURU",
    name: "Bengaluru",
    state: "Karnataka",
    x: 245,
    y: 570,
    role: "Tech Account Siphon Destination",
    activeCases: 22,
    volume: "₹1.55 Cr",
    isTarget: true,
  },
  {
    id: "CHENNAI",
    name: "Chennai",
    state: "Tamil Nadu",
    x: 290,
    y: 575,
    role: "Southern Switch Node",
    activeCases: 11,
    volume: "₹52 L",
  },
];

/**
 * Active Inter-City Mule Corridors
 * Quadratic Bezier Curves with Animated Particles
 */
export const MULE_CORRIDORS = [
  {
    id: "jamtara-mumbai",
    name: "Jamtara ➔ Mumbai Clearing Rail",
    from: "JAMTARA",
    to: "MUMBAI",
    d: "M 420 325 Q 275 335 155 430",
    risk: "CRITICAL",
    type: "KYC Phishing Siphon",
    volume: "₹2.10 Cr / 24h",
    color: "#dc2626",
    duration: "3.2s",
  },
  {
    id: "jamtara-bengaluru",
    name: "Jamtara ➔ Bengaluru Task Funnel",
    from: "JAMTARA",
    to: "BENGALURU",
    d: "M 420 325 Q 350 450 245 570",
    risk: "CRITICAL",
    type: "Telegram Task Scam",
    volume: "₹1.45 Cr / 24h",
    color: "#dc2626",
    duration: "3.8s",
  },
  {
    id: "mewat-delhi",
    name: "Mewat ➔ Delhi NCR Extortion Corridor",
    from: "MEWAT",
    to: "DELHI",
    d: "M 230 225 Q 220 205 235 195",
    risk: "CRITICAL",
    type: "SIM Cloning & Extortion",
    volume: "₹1.15 Cr / 24h",
    color: "#dc2626",
    duration: "2.5s",
  },
  {
    id: "kolkata-jamtara",
    name: "Kolkata ➔ Jamtara Smurfing Inflow",
    from: "KOLKATA",
    to: "JAMTARA",
    d: "M 450 365 Q 440 340 420 325",
    risk: "HIGH",
    type: "Mule Account Recruitment",
    volume: "₹68 L / 24h",
    color: "#d97706",
    duration: "2.8s",
  },
  {
    id: "ahmedabad-mumbai",
    name: "Ahmedabad ➔ Mumbai Rapid Layering",
    from: "AHMEDABAD",
    to: "MUMBAI",
    d: "M 140 345 Q 130 390 155 430",
    risk: "HIGH",
    type: "Rapid Cash-Out Layering",
    volume: "₹84 L / 24h",
    color: "#d97706",
    duration: "3.0s",
  },
  {
    id: "delhi-hyderabad",
    name: "Delhi NCR ➔ Hyderabad P2P Relay",
    from: "DELHI",
    to: "HYDERABAD",
    d: "M 235 195 Q 270 330 265 475",
    risk: "ELEVATED",
    type: "P2P Smurfing Dispersal",
    volume: "₹56 L / 24h",
    color: "#4f46e5",
    duration: "4.2s",
  },
];

// India Stylized Silhouette Path (viewBox 0 0 600 680)
const INDIA_PATH =
  "M 230,45 C 240,40 260,40 270,55 C 280,70 290,95 285,115 C 295,130 330,150 370,185 C 410,195 445,200 480,210 C 515,205 540,215 555,235 C 565,255 545,275 515,280 C 490,285 470,290 465,305 C 460,320 470,345 460,365 C 450,385 435,415 425,435 C 400,470 370,505 340,545 C 315,580 295,615 270,650 C 255,670 245,670 235,650 C 215,615 205,580 195,540 C 180,490 165,450 150,420 C 135,395 110,380 95,355 C 80,330 95,305 125,290 C 150,280 165,260 170,240 C 175,215 185,170 195,140 C 205,110 215,75 230,45 Z";

/**
 * GeoMuleMap component renders a vector map of India displaying
 * calibrated hubs, animated bezier arcs for active mule corridors,
 * pulsing radar hotspots for epicenters, and interactive telemetry cards.
 */
export default function GeoMuleMap({ cases = [], onSelectCase }) {
  const [hoveredHub, setHoveredHub] = useState(null);
  const [hoveredCorridor, setHoveredCorridor] = useState(null);
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const filteredCorridors = useMemo(() => {
    if (severityFilter === "ALL") return MULE_CORRIDORS;
    return MULE_CORRIDORS.filter((c) => c.risk === severityFilter);
  }, [severityFilter]);

  // Aggregate live stats
  const totalVolumeDisplay = "₹6.78 Cr";
  const activeHubsCount = INDIAN_HUBS.length;
  const activeCorridorsCount = filteredCorridors.length;

  return (
    <div className="relative w-full h-full min-h-[440px] flex flex-col bg-white rounded-lg border border-hairline overflow-hidden shadow-xs select-none">
      {/* Top Telemetry Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-surface-muted/90 border-b border-hairline text-xs font-mono">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-muted font-semibold">Mesh Corridors:</span>
            <span className="font-bold text-ink-900">{activeCorridorsCount} Active</span>
          </div>
          <div className="hidden sm:flex items-center gap-1.5">
            <span className="text-muted">Hubs:</span>
            <span className="font-bold text-ink-900">{activeHubsCount} Monitored</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-muted">Intercepted:</span>
            <span className="font-bold text-rose-600">{totalVolumeDisplay}</span>
          </div>
          {cases.length > 0 && (
            <div className="hidden md:flex items-center gap-1.5">
              <span className="text-muted">Live Rings:</span>
              <span className="font-bold text-indigo-700">{cases.length}</span>
            </div>
          )}
        </div>

        {/* Corridor Risk Filter */}
        <div className="flex items-center gap-1 bg-white p-0.5 rounded border border-hairline text-[10px]">
          {["ALL", "CRITICAL", "HIGH"].map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilter(sev)}
              className={`px-2 py-0.5 rounded font-semibold transition-all ${
                severityFilter === sev
                  ? "bg-ink-900 text-white shadow-xs"
                  : "text-muted hover:text-ink-900"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Map Canvas */}
      <div className="relative flex-1 min-h-[380px] w-full flex items-center justify-center p-2 bg-[#fcfdfe]">
        <svg
          viewBox="0 0 600 680"
          className="w-full h-full max-h-[440px] drop-shadow-sm"
          style={{ overflow: "visible" }}
        >
          <defs>
            {/* Soft Radial Gradients for Epicenter Radar */}
            <radialGradient id="radarRed" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#dc2626" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#dc2626" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="radarAmber" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#d97706" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
            </radialGradient>

            {/* Subtle Grid Pattern */}
            <pattern id="radarGrid" width="30" height="30" patternUnits="userSpaceOnUse">
              <circle cx="15" cy="15" r="0.75" fill="#cbd5e1" opacity="0.6" />
            </pattern>
          </defs>

          {/* Background Coordinates Grid */}
          <rect width="600" height="680" fill="url(#radarGrid)" opacity="0.8" />

          {/* Subtle Latitude & Longitude Guidelines */}
          {[120, 220, 320, 420, 520, 620].map((y) => (
            <line
              key={`lat-${y}`}
              x1="40"
              y1={y}
              x2="560"
              y2={y}
              stroke="#e2e8f0"
              strokeDasharray="2 4"
              strokeWidth="0.75"
            />
          ))}
          {[120, 220, 320, 420, 520].map((x) => (
            <line
              key={`lon-${x}`}
              x1={x}
              y1="40"
              x2={x}
              y2="660"
              stroke="#e2e8f0"
              strokeDasharray="2 4"
              strokeWidth="0.75"
            />
          ))}

          {/* Calibrated Latitude / Longitude Labels */}
          <text x="45" y="195" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            28° N · Northern Corridor
          </text>
          <text x="45" y="430" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            19° N · Western Financial Rail
          </text>
          <text x="45" y="570" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            13° N · Southern Tech Mesh
          </text>

          {/* India Boundary Silhouette */}
          <path
            d={INDIA_PATH}
            fill="#f1f5f9"
            stroke="#cbd5e1"
            strokeWidth="1.75"
            strokeLinejoin="round"
            className="transition-colors duration-300"
          />

          {/* Internal Region Divisions (Subtle Guidelines) */}
          <path
            d="M 230,225 Q 320,280 420,325 M 235,195 Q 180,260 140,345 M 155,430 Q 200,450 265,475 M 265,475 Q 255,520 245,570"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="1"
            strokeDasharray="3 3"
          />

          {/* Active Corridor Bezier Arcs */}
          {filteredCorridors.map((c) => {
            const isHovered = hoveredCorridor?.id === c.id;
            return (
              <g key={c.id} className="cursor-pointer">
                {/* Wider invisible hit-test stroke */}
                <path
                  d={c.d}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="14"
                  onMouseEnter={() => setHoveredCorridor(c)}
                  onMouseLeave={() => setHoveredCorridor(null)}
                />
                {/* Glow Underlay */}
                <path
                  d={c.d}
                  fill="none"
                  stroke={c.color}
                  strokeWidth={isHovered ? "4.5" : "3"}
                  strokeOpacity={isHovered ? "0.45" : "0.22"}
                  strokeLinecap="round"
                />
                {/* Core Arc Line with Flow Dash */}
                <path
                  d={c.d}
                  fill="none"
                  stroke={c.color}
                  strokeWidth={isHovered ? "2.6" : "1.8"}
                  strokeDasharray="6 4"
                  strokeLinecap="round"
                />

                {/* Hardware-Accelerated Flow Particle */}
                <circle r={isHovered ? "4" : "3"} fill={c.color}>
                  <animateMotion
                    path={c.d}
                    dur={c.duration}
                    repeatCount="indefinite"
                  />
                </circle>
              </g>
            );
          })}

          {/* Hotspot Radar Pulse Rings (Jamtara, Mewat, Mumbai) */}
          {INDIAN_HUBS.filter((h) => h.isHotspot).map((h) => (
            <g key={`radar-${h.id}`} pointerEvents="none">
              <circle cx={h.x} cy={h.y} r="18" fill="url(#radarRed)" />
              <circle
                cx={h.x}
                cy={h.y}
                r="10"
                fill="none"
                stroke="#dc2626"
                strokeWidth="1.2"
                opacity="0.7"
              >
                <animate
                  attributeName="r"
                  values="6;26"
                  dur="2.4s"
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  values="0.8;0"
                  dur="2.4s"
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          ))}

          {/* Hub Markers */}
          {INDIAN_HUBS.map((hub) => {
            const isHovered = hoveredHub?.id === hub.id;
            const isHotspot = hub.isHotspot;
            const isTarget = hub.isTarget;

            const hubColor = isHotspot
              ? "#dc2626"
              : isTarget
              ? "#4f46e5"
              : "#0f7a3d";

            return (
              <g
                key={hub.id}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredHub(hub)}
                onMouseLeave={() => setHoveredHub(null)}
                onClick={() => onSelectCase && onSelectCase({ hub_id: hub.id, hub: hub.name })}
              >
                {/* Outer Ring */}
                <circle
                  cx={hub.x}
                  cy={hub.y}
                  r={isHovered ? "8" : isHotspot ? "6.5" : "5"}
                  fill="white"
                  stroke={hubColor}
                  strokeWidth={isHovered ? "2.5" : "1.8"}
                  className="transition-all duration-150 shadow-sm"
                />
                {/* Inner Core Dot */}
                <circle
                  cx={hub.x}
                  cy={hub.y}
                  r={isHovered ? "4" : isHotspot ? "3.2" : "2.4"}
                  fill={hubColor}
                />

                {/* Hub Label */}
                <text
                  x={hub.x + 9}
                  y={hub.y + 3.5}
                  fontSize={isHovered ? "11" : "9.5"}
                  fontWeight={isHotspot || isHovered ? "bold" : "600"}
                  fill={isHotspot ? "#991b1b" : isTarget ? "#312e81" : "#0f172a"}
                  fontFamily="monospace"
                  className="transition-all duration-150 pointer-events-none drop-shadow-xs"
                >
                  {hub.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Interactive Hover Tooltip for Hub */}
        {hoveredHub && (
          <div
            className="absolute z-20 pointer-events-none bg-ink-900 text-white p-2.5 rounded-lg shadow-xl text-xs font-mono border border-white/10 max-w-xs space-y-1"
            style={{
              left: `${Math.min(420, Math.max(20, (hoveredHub.x / 600) * 100))}%`,
              top: `${Math.min(320, Math.max(20, (hoveredHub.y / 680) * 100))}%`,
              transform: "translate(-50%, -120%)",
            }}
          >
            <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-1">
              <span className="font-bold text-amber-400">{hoveredHub.name}</span>
              <span className="text-[10px] text-white/60 uppercase">{hoveredHub.state}</span>
            </div>
            <div className="text-[11px] text-white/80">{hoveredHub.role}</div>
            <div className="flex items-center justify-between gap-4 pt-1 text-[10px] border-t border-white/10">
              <span className="text-white/60">Active Cases: {hoveredHub.activeCases}</span>
              <span className="font-bold text-rose-400">Vol: {hoveredHub.volume}</span>
            </div>
          </div>
        )}

        {/* Interactive Hover Tooltip for Corridor */}
        {hoveredCorridor && !hoveredHub && (
          <div className="absolute bottom-3 left-3 z-20 pointer-events-none bg-ink-900 text-white p-3 rounded-lg shadow-xl text-xs font-mono border border-white/10 space-y-1 max-w-sm">
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-1">
              <span className="font-bold text-amber-400">{hoveredCorridor.name}</span>
              <span
                className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                  hoveredCorridor.risk === "CRITICAL"
                    ? "bg-rose-900/80 text-rose-200 border border-rose-700"
                    : "bg-amber-900/80 text-amber-200 border border-amber-700"
                }`}
              >
                {hoveredCorridor.risk}
              </span>
            </div>
            <div className="text-[11px] text-white/80">{hoveredCorridor.type}</div>
            <div className="text-[10px] text-rose-300 font-semibold">
              Estimated Inflow Rate: {hoveredCorridor.volume}
            </div>
          </div>
        )}

        {/* Map Legend HUD */}
        <div className="absolute bottom-3 right-3 flex items-center gap-3 text-[10px] font-mono text-muted bg-white/95 backdrop-blur px-2.5 py-1.5 rounded-lg border border-hairline shadow-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#dc2626]" />
            <span>Phishing Epicenter</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#4f46e5]" />
            <span>Target Metro</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#0f7a3d]" />
            <span>Switch Node</span>
          </div>
        </div>
      </div>
    </div>
  );
}
