import React, { useState, useMemo } from "react";

/**
 * Geodetically Calibrated Indian Financial & Threat Hubs
 * Coordinates calibrated from app/engine/upi_rules.py CITY_COORDINATES
 * Projected to SVG coordinates on viewBox="0 0 650 720"
 */
export const INDIAN_HUBS = [
  {
    id: "DELHI",
    name: "Delhi NCR",
    state: "NCR",
    lat: 28.7041,
    lon: 77.1025,
    x: 212.3,
    y: 218.7,
    role: "High-Value Target Inflow",
    activeCases: 14,
    volume: "₹1.42 Cr",
    isTarget: true,
    labelAnchor: "start",
    labelOffsetX: 10,
    labelOffsetY: 3.5,
  },
  {
    id: "MEWAT",
    name: "Mewat",
    state: "Haryana",
    lat: 28.0626,
    lon: 76.9951,
    x: 208.1,
    y: 232.5,
    role: "SIM-Swap Syndicate Epicenter",
    activeCases: 29,
    volume: "₹1.85 Cr",
    isHotspot: true,
    labelAnchor: "end",
    labelOffsetX: -10,
    labelOffsetY: 3.5,
  },
  {
    id: "JAMTARA",
    name: "Jamtara",
    state: "Jharkhand",
    lat: 24.004,
    lon: 86.7851,
    x: 407.4,
    y: 323.7,
    role: "Phishing Origin & Mule Sinks",
    activeCases: 42,
    volume: "₹3.10 Cr",
    isHotspot: true,
    labelAnchor: "start",
    labelOffsetX: 10,
    labelOffsetY: 3.5,
  },
  {
    id: "MUMBAI",
    name: "Mumbai",
    state: "Maharashtra",
    lat: 19.076,
    lon: 72.8777,
    x: 123.2,
    y: 436.1,
    role: "Financial Clearing / Cash-Out",
    activeCases: 38,
    volume: "₹2.65 Cr",
    isTarget: true,
    labelAnchor: "end",
    labelOffsetX: -10,
    labelOffsetY: 3.5,
  },
  {
    id: "AHMEDABAD",
    name: "Ahmedabad",
    state: "Gujarat",
    lat: 23.0225,
    lon: 72.5714,
    x: 118.0,
    y: 344.8,
    role: "Layering & Smurfing Conduit",
    activeCases: 18,
    volume: "₹92 L",
    labelAnchor: "end",
    labelOffsetX: -10,
    labelOffsetY: 3.5,
  },
  {
    id: "KOLKATA",
    name: "Kolkata",
    state: "West Bengal",
    lat: 22.5726,
    lon: 88.3639,
    x: 439.2,
    y: 355.0,
    role: "Eastern Aggregation Gateway",
    activeCases: 16,
    volume: "₹78 L",
    labelAnchor: "start",
    labelOffsetX: 10,
    labelOffsetY: 3.5,
  },
  {
    id: "HYDERABAD",
    name: "Hyderabad",
    state: "Telangana",
    lat: 17.385,
    lon: 78.4867,
    x: 238.3,
    y: 472.0,
    role: "P2P Relay Node",
    activeCases: 12,
    volume: "₹64 L",
    labelAnchor: "start",
    labelOffsetX: 10,
    labelOffsetY: 3.5,
  },
  {
    id: "BENGALURU",
    name: "Bengaluru",
    state: "Karnataka",
    lat: 12.9716,
    lon: 77.5946,
    x: 220.1,
    y: 571.6,
    role: "Tech Account Siphon Destination",
    activeCases: 22,
    volume: "₹1.55 Cr",
    isTarget: true,
    labelAnchor: "end",
    labelOffsetX: -10,
    labelOffsetY: 3.5,
  },
  {
    id: "CHENNAI",
    name: "Chennai",
    state: "Tamil Nadu",
    lat: 13.0827,
    lon: 80.2707,
    x: 274.6,
    y: 569.1,
    role: "Southern Switch Node",
    activeCases: 11,
    volume: "₹52 L",
    labelAnchor: "start",
    labelOffsetX: 10,
    labelOffsetY: 3.5,
  },
];

/**
 * Active Inter-City Mule Corridors
 * Anchored to geodetically calibrated hub coordinates
 * Dual-layer glowing bezier curves with hardware-accelerated animated particles
 */
export const MULE_CORRIDORS = [
  {
    id: "jamtara-mumbai",
    name: "Jamtara ➔ Mumbai Clearing Rail",
    from: "JAMTARA",
    to: "MUMBAI",
    d: "M 407.4 323.7 Q 265 340 123.2 436.1",
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
    d: "M 407.4 323.7 Q 345 450 220.1 571.6",
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
    d: "M 208.1 232.5 Q 200 222 212.3 218.7",
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
    d: "M 439.2 355.0 Q 430 335 407.4 323.7",
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
    d: "M 118.0 344.8 Q 110 390 123.2 436.1",
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
    d: "M 212.3 218.7 Q 255 345 238.3 472.0",
    risk: "ELEVATED",
    type: "P2P Smurfing Dispersal",
    volume: "₹56 L / 24h",
    color: "#4f46e5",
    duration: "4.2s",
  },
];

/**
 * Authentic 139-Vertex India Vector Cartography
 * Calibrated geographic boundary covering Kashmir & Ladakh, Indo-Nepal border,
 * Sikkim, Arunachal McMahon line, Purvanchal & Seven Sisters, Bengal Delta & Sundarbans,
 * Coromandel Coast, Kanyakumari apex, Konkan/Malabar Coast, and Gujarat Kathiawar & Kutch peninsulas.
 */
export const INDIA_139_VERTICES_COUNT = 139;

export const INDIA_PATH =
  "M 205.1 61.6 L 224.5 65.4 L 238.7 72.1 L 253.0 87.8 L 248.9 110.3 L 259.1 128.3 L 246.9 144.0 L 240.8 155.3 L 253.0 166.5 L 289.6 184.5 L 271.3 213.7 L 291.7 224.9 L 320.2 245.1 L 350.7 247.4 L 375.1 260.9 L 407.7 267.6 L 434.2 263.1 L 435.2 240.6 L 444.3 232.8 L 450.5 238.4 L 450.5 248.5 L 470.8 258.6 L 503.4 260.9 L 515.6 256.4 L 513.6 242.9 L 529.9 236.2 L 550.2 229.4 L 570.6 220.4 L 595.0 211.4 L 623.5 229.4 L 619.4 233.9 L 607.2 251.9 L 595.0 260.9 L 578.7 278.8 L 570.6 296.8 L 560.4 319.3 L 542.1 337.3 L 529.9 371.0 L 519.7 350.8 L 499.3 346.3 L 499.3 323.8 L 517.6 314.8 L 509.5 296.8 L 483.0 299.1 L 468.8 285.6 L 452.5 274.4 L 448.4 269.9 L 438.2 274.4 L 434.2 301.3 L 444.3 321.5 L 448.4 341.8 L 454.5 364.2 L 448.4 376.6 L 422.0 377.7 L 409.7 384.5 L 410.8 397.9 L 405.7 406.9 L 387.3 418.2 L 377.2 421.5 L 369.0 429.4 L 348.7 451.9 L 336.5 465.4 L 316.1 487.8 L 287.6 508.1 L 269.3 539.5 L 273.3 559.7 L 274.8 569.2 L 272.3 582.2 L 265.2 594.6 L 266.2 620.4 L 267.2 631.6 L 248.9 642.9 L 255.0 654.1 L 231.6 665.3 L 219.4 681.5 L 206.2 672.1 L 200.1 663.1 L 193.9 649.6 L 193.1 640.0 L 186.8 624.9 L 182.8 610.3 L 174.6 595.7 L 167.5 582.2 L 163.4 573.2 L 161.4 563.1 L 156.3 541.8 L 149.6 530.5 L 143.1 519.3 L 142.0 512.5 L 132.9 492.3 L 132.9 481.1 L 128.8 463.1 L 125.8 451.9 L 124.3 445.1 L 123.1 437.3 L 122.7 429.4 L 120.7 414.3 L 122.7 404.7 L 122.7 389.0 L 118.6 375.5 L 109.5 375.5 L 102.3 386.7 L 85.6 397.9 L 72.8 393.5 L 57.6 377.7 L 44.3 363.1 L 66.7 357.5 L 79.9 350.8 L 69.8 346.3 L 53.5 350.8 L 37.2 340.6 L 34.1 330.5 L 29.1 329.4 L 41.3 321.5 L 61.6 317.0 L 87.1 312.6 L 92.2 305.8 L 90.1 290.1 L 82.0 274.4 L 84.0 258.6 L 104.4 238.4 L 116.6 222.7 L 144.1 191.2 L 149.2 180.0 L 155.3 168.7 L 159.3 153.0 L 167.5 142.9 L 177.7 138.4 L 163.4 128.3 L 153.2 121.6 L 151.2 113.7 L 149.2 104.7 L 147.1 96.8 L 148.1 90.1 L 153.2 84.5 L 167.5 86.7 L 189.9 85.6 L 202.1 76.6 L 204.1 69.9 Z";

/**
 * GeoMuleMap component renders high-fidelity vector cartography of India
 * displaying calibrated hubs, dual-layer glowing bezier arcs, hardware-accelerated
 * particle flows, pulsating radar hotspots, and interactive telemetry cards.
 */
export default function GeoMuleMap({ cases = [], onSelectCase }) {
  const [hoveredHub, setHoveredHub] = useState(null);
  const [hoveredCorridor, setHoveredCorridor] = useState(null);
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const filteredCorridors = useMemo(() => {
    if (severityFilter === "ALL") return MULE_CORRIDORS;
    return MULE_CORRIDORS.filter((c) => c.risk === severityFilter);
  }, [severityFilter]);

  // Aggregate live stats defensively guarding against null or undefined cases
  const totalVolumeDisplay = "₹6.78 Cr";
  const activeHubsCount = INDIAN_HUBS.length;
  const activeCorridorsCount = filteredCorridors.length;
  const liveCasesCount = (cases || []).length;

  return (
    <div className="relative w-full h-full min-h-[460px] flex flex-col bg-white rounded-lg border border-hairline overflow-hidden shadow-xs select-none">
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
          {liveCasesCount > 0 && (
            <div className="hidden md:flex items-center gap-1.5">
              <span className="text-muted">Live Rings:</span>
              <span className="font-bold text-indigo-700">{liveCasesCount}</span>
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
      <div className="relative flex-1 min-h-[400px] w-full flex items-center justify-center p-2 bg-[#fcfdfe]">
        <svg
          viewBox="0 0 650 720"
          className="w-full h-full max-h-[480px] drop-shadow-sm"
          style={{ overflow: "visible" }}
        >
          <defs>
            {/* Dual-Layer Glow Blur Filter */}
            <filter id="arcGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
            </filter>

            {/* Soft Radial Gradients for Epicenter Radar */}
            <radialGradient id="radarRed" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#dc2626" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#dc2626" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="radarAmber" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#d97706" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
            </radialGradient>

            {/* Subtle Coordinate Matrix Dot Pattern */}
            <pattern id="radarGrid" width="32" height="32" patternUnits="userSpaceOnUse">
              <circle cx="16" cy="16" r="0.8" fill="#cbd5e1" opacity="0.65" />
            </pattern>
          </defs>

          {/* Background Coordinates Grid */}
          <rect width="650" height="720" fill="url(#radarGrid)" opacity="0.85" />

          {/* Calibrated Latitude Guidelines */}
          {[140, 234, 336, 436, 571, 670].map((y) => (
            <line
              key={`lat-${y}`}
              x1="30"
              y1={y}
              x2="620"
              y2={y}
              stroke="#e2e8f0"
              strokeDasharray="2 4"
              strokeWidth="0.75"
            />
          ))}

          {/* Calibrated Longitude Meridians */}
          {[106, 210, 269, 432, 550].map((x) => (
            <line
              key={`lon-${x}`}
              x1={x}
              y1="30"
              x2={x}
              y2="690"
              stroke="#e2e8f0"
              strokeDasharray="2 4"
              strokeWidth="0.75"
            />
          ))}

          {/* Geodetic Latitude Annotations */}
          <text x="35" y="230" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            28° N · Northern Cyber Corridor
          </text>
          <text x="35" y="332" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            23.4° N · Tropic of Cancer
          </text>
          <text x="35" y="432" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            19° N · Western Financial Rail
          </text>
          <text x="35" y="567" fill="#94a3b8" fontSize="9" fontFamily="monospace">
            13° N · Southern Tech Mesh
          </text>

          {/* Authentic 139-Vertex India Vector Silhouette */}
          <path
            d={INDIA_PATH}
            fill="#f8fafc"
            stroke="#94a3b8"
            strokeWidth="1.6"
            strokeLinejoin="round"
            strokeLinecap="round"
            className="transition-colors duration-300 drop-shadow-xs"
          />

          {/* Internal Cyber-Routing Guidelines (Subtle Connectors) */}
          <path
            d="M 208.1,232.5 Q 310,280 407.4,323.7 M 212.3,218.7 Q 165,280 118.0,344.8 M 123.2,436.1 Q 180,455 238.3,472.0 M 238.3,472.0 Q 230,520 220.1,571.6"
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
                {/* Wider invisible hit-test stroke for smooth hover */}
                <path
                  d={c.d}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="16"
                  onMouseEnter={() => setHoveredCorridor(c)}
                  onMouseLeave={() => setHoveredCorridor(null)}
                />
                {/* Dual-Layer Glow Underlay with feGaussianBlur */}
                <path
                  d={c.d}
                  fill="none"
                  stroke={c.color}
                  filter="url(#arcGlow)"
                  strokeWidth={isHovered ? "5.5" : "3.5"}
                  strokeOpacity={isHovered ? "0.6" : "0.32"}
                  strokeLinecap="round"
                />
                {/* Core Arc Line with Directional Flow Dash */}
                <path
                  d={c.d}
                  fill="none"
                  stroke={c.color}
                  strokeWidth={isHovered ? "2.6" : "1.8"}
                  strokeDasharray="6 4"
                  strokeLinecap="round"
                />

                {/* Hardware-Accelerated Kinetic Flow Particle */}
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

          {/* Hotspot Radar Pulse Rings (Jamtara, Mewat) */}
          {INDIAN_HUBS.filter((h) => h.isHotspot).map((h) => (
            <g key={`radar-${h.id}`} pointerEvents="none">
              <circle cx={h.x} cy={h.y} r="20" fill="url(#radarRed)" />
              <circle
                cx={h.x}
                cy={h.y}
                r="10"
                fill="none"
                stroke="#dc2626"
                strokeWidth="1.2"
                opacity="0.75"
              >
                <animate
                  attributeName="r"
                  values="6;28"
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
          ))}

          {/* Hub Markers & Calibrated Monospace City Labels */}
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
                {/* Outer Concentric Ring */}
                <circle
                  cx={hub.x}
                  cy={hub.y}
                  r={isHovered ? "8.5" : isHotspot ? "7" : "5.5"}
                  fill="white"
                  stroke={hubColor}
                  strokeWidth={isHovered ? "2.5" : "1.8"}
                  className="transition-all duration-150 shadow-sm"
                />
                {/* Inner Semantic Core Dot */}
                <circle
                  cx={hub.x}
                  cy={hub.y}
                  r={isHovered ? "4" : isHotspot ? "3.2" : "2.4"}
                  fill={hubColor}
                />

                {/* Calibrated Monospace City Label */}
                <text
                  x={hub.x + hub.labelOffsetX}
                  y={hub.y + hub.labelOffsetY}
                  textAnchor={hub.labelAnchor}
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
              left: `${Math.min(88, Math.max(12, (hoveredHub.x / 650) * 100))}%`,
              top: `${Math.min(85, Math.max(15, (hoveredHub.y / 720) * 100))}%`,
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
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
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
