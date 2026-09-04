import React, { useEffect, useRef, useState } from "react";

// ─── Hub definitions with real lat/lon ────────────────────────────────────────
const HUBS = [
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

export const INDIAN_HUBS = HUBS;

const CORRIDORS = [
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

const HUB_MAP = Object.fromEntries(HUBS.map(h => [h.id, h]));

function loadLeaflet() {
  return new Promise((resolve) => {
    if (window.L) { resolve(window.L); return; }

    // CSS
    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }

    // JS
    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = () => resolve(window.L);
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
}

function makeMarkerHtml(hub) {
  const color = hub.isHotspot ? "#dc2626" : hub.isTarget ? "#3b82f6" : "#6366f1";
  return `<div style="
    width:14px;height:14px;
    background:${color};
    border:2.5px solid white;
    border-radius:50%;
    box-shadow:0 0 0 3px ${color}44, 0 0 12px ${color}99;
    cursor:pointer;
  "></div>`;
}

function makePopupHtml(hub) {
  const color = hub.isHotspot ? "#dc2626" : hub.isTarget ? "#3b82f6" : "#6366f1";
  return `
    <div style="font-family:monospace;font-size:12px;min-width:200px;padding:4px 0">
      <div style="font-weight:700;font-size:14px;color:${color};margin-bottom:4px">${hub.name}</div>
      <div style="color:#6b7280;margin-bottom:8px;font-size:11px;line-height:1.4">${hub.role}</div>
      <div style="display:flex;justify-content:space-between;border-top:1px solid #e5e7eb;padding-top:6px">
        <span style="color:#374151">Cases: <strong>${hub.activeCases}</strong></span>
        <span style="color:#dc2626;font-weight:700">${hub.volume}</span>
      </div>
    </div>`;
}

export default function GeoMuleMap() {
  const containerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [leafletLoaded, setLeafletLoaded] = useState(!!window.L);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    loadLeaflet().then((L) => {
      if (cancelled || !L || !containerRef.current || mapInstanceRef.current) return;

      setLeafletLoaded(true);

      // Initialise map centred on India
      const map = L.map(containerRef.current, {
        center: [22.5, 80.5],
        zoom: 5,
        zoomControl: true,
        attributionControl: true,
        scrollWheelZoom: true,
      });

      // OpenStreetMap tiles — Carto Light Nolabels for a clean fintech look
      L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
          subdomains: "abcd",
          maxZoom: 19,
        }
      ).addTo(map);

      mapInstanceRef.current = map;

      // ── City markers ─────────────────────────────────────────────────────
      HUBS.forEach((hub) => {
        const icon = L.divIcon({
          className: "",
          html: makeMarkerHtml(hub),
          iconSize: [14, 14],
          iconAnchor: [7, 7],
          popupAnchor: [0, -10],
        });

        L.marker([hub.lat, hub.lon], { icon })
          .bindPopup(makePopupHtml(hub), { maxWidth: 240 })
          .addTo(map);
      });

      // ── Fraud corridors ───────────────────────────────────────────────────
      CORRIDORS.forEach((c) => {
        const f = HUB_MAP[c.from];
        const t = HUB_MAP[c.to];
        if (!f || !t) return;

        const isCritical = c.risk === "CRITICAL";
        const line = L.polyline(
          [[f.lat, f.lon], [t.lat, t.lon]],
          {
            color: isCritical ? "#dc2626" : "#c8641e",
            weight: isCritical ? 3 : 2,
            opacity: isCritical ? 0.85 : 0.65,
            dashArray: isCritical ? null : "10 6",
          }
        )
          .bindTooltip(
            `<span style="font-family:monospace;font-size:11px">
              <strong style="color:${isCritical ? "#dc2626" : "#c8641e"}">[${c.risk}]</strong> ${c.label}<br/>
              <span style="color:#6b7280">${f.name} → ${t.name}</span>
            </span>`,
            { sticky: true }
          )
          .addTo(map);
      });
    }).catch(() => {
      if (!cancelled) setLoadError(true);
    });

    return () => {
      cancelled = true;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="w-full flex flex-col bg-white rounded-lg border border-hairline overflow-hidden shadow-xs" style={{ minHeight: 520 }}>

      {/* Header strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-gray-50 border-b border-gray-200 text-xs font-mono">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-gray-500 font-semibold">Corridors:</span>
            <span className="font-bold text-gray-900">{CORRIDORS.length} Active</span>
          </span>
          <span className="text-gray-500">Hubs: <span className="font-bold text-gray-900">{HUBS.length} Monitored</span></span>
          <span className="text-gray-500">Intercepted: <span className="font-bold text-rose-600">₹6.78 Cr</span></span>
          <span className="text-gray-500">Live Rings: <span className="font-bold text-indigo-700">50</span></span>
        </div>

        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block" /> Phishing Epicentre</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" /> Target Network</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block" /> Switch Node</span>
        </div>
      </div>

      {/* Loading state */}
      {!leafletLoaded && !loadError && (
        <div className="flex-1 flex items-center justify-center text-xs font-mono text-gray-400 min-h-[460px]">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse mr-2" />
          Loading map tiles…
        </div>
      )}

      {loadError && (
        <div className="flex-1 flex items-center justify-center text-xs font-mono text-rose-500 min-h-[460px]">
          ⚠ Map tiles unavailable — check network connectivity.
        </div>
      )}

      {/* Map container — always in DOM so Leaflet can attach */}
      <div
        ref={containerRef}
        style={{ flex: 1, minHeight: 460, display: leafletLoaded ? "block" : "none" }}
      />
    </div>
  );
}
