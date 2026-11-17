import React, { useEffect, useRef, useMemo } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// ─── Hub definitions with geodetic lat/lon ─────────────────────────────────────
export const INDIAN_HUBS = [
  { id: "DELHI",     name: "Delhi NCR",  lat: 28.70, lon: 77.10, isTarget:  true,  role: "High-Value Target Inflow",         activeCases: 14, volume: "₹1.42 Cr" },
  { id: "MEWAT",    name: "Mewat",       lat: 28.06, lon: 76.99, isHotspot: true,  role: "SIM-Swap Syndicate Epicenter",     activeCases: 29, volume: "₹1.85 Cr" },
  { id: "JAMTARA",  name: "Jamtara",     lat: 24.00, lon: 86.79, isHotspot: true,  role: "Phishing Origin & Mule Sinks",     activeCases: 42, volume: "₹3.10 Cr" },
  { id: "MUMBAI",   name: "Mumbai",      lat: 19.08, lon: 72.88, isTarget:  true,  role: "Financial Gateway & PSP Node",     activeCases: 8,  volume: "₹0.98 Cr" },
  { id: "BENGALURU",name: "Bengaluru",   lat: 12.97, lon: 77.59, isTarget:  true,  role: "Tech Hub — Device Farm Activity",  activeCases: 6,  volume: "₹0.74 Cr" },
  { id: "KOLKATA",  name: "Kolkata",     lat: 22.57, lon: 88.36, isHotspot: true,  role: "Eastern Mule Relay Node",          activeCases: 11, volume: "₹1.12 Cr" },
  { id: "AHMEDABAD",name: "Ahmedabad",   lat: 23.02, lon: 72.57,                   role: "Structuring Hub",                  activeCases: 5,  volume: "₹0.61 Cr" },
  { id: "HYDERABAD",name: "Hyderabad",   lat: 17.38, lon: 78.49,                   role: "Coordinator Node",                 activeCases: 7,  volume: "₹0.82 Cr" },
  { id: "CHENNAI",  name: "Chennai",     lat: 13.08, lon: 80.27,                   role: "Southern Inflow Sink",             activeCases: 4,  volume: "₹0.53 Cr" },
];

export const MULE_CORRIDORS = [
  { from: "JAMTARA",   to: "DELHI",     risk: "CRITICAL", label: "Phishing → Primary Target" },
  { from: "MEWAT",     to: "DELHI",     risk: "CRITICAL", label: "SIM-Swap → Primary Target" },
  { from: "JAMTARA",   to: "KOLKATA",   risk: "HIGH",     label: "Eastern Relay"             },
  { from: "KOLKATA",   to: "MUMBAI",    risk: "HIGH",     label: "Cross-Regional Laundering" },
  { from: "MUMBAI",    to: "AHMEDABAD", risk: "HIGH",     label: "Structuring Route"          },
  { from: "HYDERABAD", to: "CHENNAI",   risk: "HIGH",     label: "Southern Corridor"          },
  { from: "DELHI",     to: "MUMBAI",    risk: "HIGH",     label: "Hub-to-Gateway"             },
  { from: "BENGALURU", to: "HYDERABAD", risk: "HIGH",     label: "Tech-Hub Relay"             },
  { from: "JAMTARA",   to: "HYDERABAD", risk: "HIGH",     label: "Central Relay"              },
];

const HUB_MAP = Object.fromEntries(INDIAN_HUBS.map((h) => [h.id, h]));

/**
 * Calculates Mercator screen bearing angle in degrees from (lat1, lon1) to (lat2, lon2)
 */
function calculateBearing(lat1, lon1, lat2, lon2) {
  const radLat1 = (lat1 * Math.PI) / 180;
  const radLat2 = (lat2 * Math.PI) / 180;
  const radDlon = ((lon2 - lon1) * Math.PI) / 180;
  const y1 = Math.log(Math.tan(Math.PI / 4 + radLat1 / 2));
  const y2 = Math.log(Math.tan(Math.PI / 4 + radLat2 / 2));
  const dy = -(y2 - y1);
  const dx = radDlon;
  return (Math.atan2(dy, dx) * 180) / Math.PI;
}

function makeMarkerHtml(hub) {
  const color = hub.isHotspot ? "#dc2626" : hub.isTarget ? "#3b82f6" : "#6366f1";
  const pulseHtml = hub.isHotspot
    ? `<span style="
        position:absolute;
        inset:-6px;
        border-radius:50%;
        border:2px solid ${color};
        opacity:0.6;
        animation:ping 1.8s cubic-bezier(0,0,0.2,1) infinite;
        pointer-events:none;
      "></span>`
    : "";

  return `
    <div style="position:relative;width:16px;height:16px;display:flex;align-items:center;justify-content:center;cursor:pointer;">
      ${pulseHtml}
      <div style="
        width:14px;
        height:14px;
        background:${color};
        border:2.5px solid #ffffff;
        border-radius:50%;
        box-shadow:0 0 0 2px ${color}55, 0 2px 8px rgba(0,0,0,0.3);
      "></div>
    </div>
  `;
}

function makePopupHtml(hub) {
  const color = hub.isHotspot ? "#dc2626" : hub.isTarget ? "#3b82f6" : "#6366f1";
  const typeLabel = hub.isHotspot ? "HOTSPOT" : hub.isTarget ? "TARGET" : "SWITCH NODE";
  return `
    <div style="font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px;min-width:210px;padding:2px 0;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
        <span style="font-weight:700;font-size:13px;color:#0f172a;">${hub.name}</span>
        <span style="font-size:10px;font-weight:700;color:${color};background:${color}18;padding:1px 5px;border-radius:4px;border:1px solid ${color}44;">
          ${typeLabel}
        </span>
      </div>
      <div style="color:#64748b;margin-bottom:8px;font-size:11px;line-height:1.35;">${hub.role}</div>
      <div style="display:flex;justify-content:space-between;border-top:1px solid #e2e8f0;padding-top:6px;font-size:11px;">
        <span style="color:#334155;">Active Cases: <strong>${hub.activeCases}</strong></span>
        <span style="color:#dc2626;font-weight:700;">${hub.volume}</span>
      </div>
      <div style="margin-top:4px;font-size:10px;color:#94a3b8;">
        Coord: ${hub.lat.toFixed(2)}°N, ${hub.lon.toFixed(2)}°E
      </div>
    </div>
  `;
}

export default function GeoMuleMap({ cases = [] } = {}) {
  const containerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  const activeRingsCount = useMemo(() => {
    return Array.isArray(cases) && cases.length > 0 ? cases.length : 50;
  }, [cases]);

  useEffect(() => {
    if (!containerRef.current || mapInstanceRef.current) return;

    // Prevent re-initialization error if DOM node was reused before garbage collection
    if (containerRef.current._leaflet_id) {
      delete containerRef.current._leaflet_id;
    }

    // Initialise Leaflet map instance centred on India with stable boundary limits
    const map = L.map(containerRef.current, {
      center: [22.6, 79.8],
      zoom: 5,
      minZoom: 4,
      maxZoom: 9,
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      dragging: true,
      boxZoom: false,
      maxBounds: [
        [4.0, 62.0],
        [38.0, 102.0],
      ],
      maxBoundsViscosity: 0.85,
    });

    // Clean World Light Gray Base tiles — immediate initialization
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      {
        attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        maxZoom: 18,
        minZoom: 4,
      }
    ).addTo(map);

    // Stop propagation on map click to prevent parent container shifts or drawer triggers
    map.on("click", (e) => {
      if (e?.originalEvent) {
        L.DomEvent.stopPropagation(e.originalEvent);
      }
    });

    mapInstanceRef.current = map;

    // ─── Render Fraud Corridors with Directional Flow Arrows ────────────────
    MULE_CORRIDORS.forEach((c) => {
      const f = HUB_MAP[c.from];
      const t = HUB_MAP[c.to];
      if (!f || !t) return;

      const isCritical = c.risk === "CRITICAL";
      const color = isCritical ? "#dc2626" : "#d97706";
      const weight = isCritical ? 3.5 : 2.5;
      const opacity = isCritical ? 0.9 : 0.75;

      // 1. Transaction flow polyline
      const line = L.polyline(
        [
          [f.lat, f.lon],
          [t.lat, t.lon],
        ],
        {
          color,
          weight,
          opacity,
          dashArray: isCritical ? undefined : "8 6",
        }
      )
        .bindTooltip(
          `<span style="font-family:ui-monospace,SFMono-Regular,monospace;font-size:11px">
            <strong style="color:${color}">[${c.risk}]</strong> ${c.label}<br/>
            <span style="color:#64748b">${f.name} ➔ ${t.name}</span>
          </span>`,
          { sticky: true }
        )
        .addTo(map);

      line.on("click", (e) => {
        if (e?.originalEvent) {
          L.DomEvent.stopPropagation(e.originalEvent);
        }
      });

      // 2. Directional flow arrow placed along the corridor vector (55% offset)
      const bearing = calculateBearing(f.lat, f.lon, t.lat, t.lon);
      const arrowLat = f.lat + (t.lat - f.lat) * 0.55;
      const arrowLon = f.lon + (t.lon - f.lon) * 0.55;

      const arrowIcon = L.divIcon({
        className: "mule-flow-arrow",
        html: `
          <div style="
            width: 22px;
            height: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            transform: rotate(${bearing.toFixed(1)}deg);
            pointer-events: none;
          ">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" style="filter: drop-shadow(0 1px 2px rgba(0,0,0,0.45));">
              <path d="M 3 3 L 17 10 L 3 17 L 7 10 Z"
                    fill="${color}"
                    stroke="#ffffff"
                    stroke-width="1.5"
                    stroke-linejoin="round" />
            </svg>
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });

      L.marker([arrowLat, arrowLon], {
        icon: arrowIcon,
        interactive: false,
        keyboard: false,
      }).addTo(map);
    });

    // ─── Render City Hub Markers with Non-sliding AutoPan-disabled Popups ───
    INDIAN_HUBS.forEach((hub) => {
      const icon = L.divIcon({
        className: "mule-hub-marker",
        html: makeMarkerHtml(hub),
        iconSize: [16, 16],
        iconAnchor: [8, 8],
        popupAnchor: [0, -10],
      });

      const marker = L.marker([hub.lat, hub.lon], { icon })
        .bindPopup(makePopupHtml(hub), {
          maxWidth: 260,
          autoPan: false, // CRITICAL: disables map view sliding when popup opens
          closeButton: true,
        })
        .addTo(map);

      // Stop propagation on originalEvent to prevent any parent container shift or drawer triggers
      marker.on("click", (e) => {
        if (e?.originalEvent) {
          L.DomEvent.stopPropagation(e.originalEvent);
        }
      });
    });

    // Trigger immediate and tick-based size invalidation to avoid blank/grey tiles
    map.whenReady(() => {
      map.invalidateSize();
    });
    const timer1 = setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 60);
    const timer2 = setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 300);

    // Responsive observer to continuously ensure proper tile alignment
    const currentContainer = containerRef.current;
    const resizeObserver = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    });
    if (currentContainer) {
      resizeObserver.observe(currentContainer);
    }

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      if (currentContainer) {
        resizeObserver.unobserve(currentContainer);
      }
      resizeObserver.disconnect();
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div
      className="w-full h-full flex flex-col bg-white rounded-lg border border-hairline overflow-hidden shadow-xs relative"
      style={{ minHeight: 520 }}
    >
      {/* Telemetry Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-gray-50 border-b border-gray-200 text-xs font-mono select-none">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-gray-500 font-semibold">Corridors:</span>
            <span className="font-bold text-gray-900">{MULE_CORRIDORS.length} Active</span>
          </span>
          <span className="text-gray-500">
            Hubs: <span className="font-bold text-gray-900">{INDIAN_HUBS.length} Monitored</span>
          </span>
          <span className="text-gray-500">
            Intercepted: <span className="font-bold text-rose-600">₹6.78 Cr</span>
          </span>
          <span className="text-gray-500">
            Live Rings: <span className="font-bold text-indigo-700">{activeRingsCount}</span>
          </span>
        </div>

        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block" />
            <span>Phishing Epicentre</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
            <span>Target Network</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block" />
            <span>Switch Node</span>
          </span>
        </div>
      </div>

      {/* Interactive Leaflet Map Viewport Container — Always visible & sized */}
      <div
        ref={containerRef}
        className="flex-1 w-full relative z-0"
        style={{ minHeight: 460, height: "100%", width: "100%" }}
      />
    </div>
  );
}
