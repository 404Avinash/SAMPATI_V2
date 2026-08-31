# Frontend Architecture Survey & Implementation Guide: NetworkConstellation (R3) & Investigations / CaseDrawer / ForensicImageViewer (R4, R1)

## 1. Observation

### 1.1 NetworkConstellation Canvas & Timeline (`frontend/src/components/NetworkConstellation.jsx`)
* **File Location**: `frontend/src/components/NetworkConstellation.jsx` (925 lines)
* **Current Implementation Details**:
  * **Topology Extraction** (`lines 86–267`): `extractChronologicalTopology(cases, caseData)` parses cases and normalizes entities into nodes (`hub`, `victim`, `hop`, `cashout`) and chronologically sorted edges (`Fan-In Infiltration`, `Layering Hop`, `Cash-Out Exit`, `Trigger Interception`).
  * **Physics Engine** (`lines 464–514`): Main loop in `requestAnimationFrame` calculates:
    1. Center Gravity: `(width / 2 - n.x) * 0.0006`
    2. Pairwise Repulsion: `950 / distSq`
    3. Edge Spring Tension: `(dist - 95) * 0.006`
    4. Damping: `n.vx *= 0.88; n.vy *= 0.88`
    *Current Limitation*: When settled or paused, damping brings all node velocities to zero. Nodes freeze completely and edges remain rigid with no organic drift.
  * **Node Styling & Glow** (`lines 541–581`):
    * Pulsing glow is currently applied *only* if `n.kind === 'hub'` using `Math.sin(t * 3 + n.x) * 0.18` and hardcoded `#b3261e`.
    * Nodes are styled strictly by structural role (`hub`, `victim`, `hop`, `cashout`), ignoring verdict categories (`BLOCK`, `HOLD`, `ALLOW`).
  * **Edge Rendering & Particle Flow** (`lines 516–538`):
    * `getEdgeStroke(riskScore)` (`lines 24–45`) maps risk to slate (<40), amber (40–74), crimson (>=75).
    * Edges are drawn as plain dashed lines (`ctx.setLineDash([5, 5])`) moving with `ctx.lineDashOffset = -t * 26`.
    * *Missing*: Animated particle flow dots traveling along edges indicating active fund laundering.
  * **Timeline Playback & Auto-Play** (`lines 290–306`, `354–374`):
    * Defaults to `currentStep = totalSteps` and `isPlaying = false`. The user must manually click "Play" or drag the slider.
    * *Missing*: Auto-play on mount when cases exist, animating chronologically from $t=0$ to step $N$.
  * **Canvas Interaction (Zoom & Pan)** (`lines 595–705`):
    * Only basic mouse move/hover hit detection exists.
    * *Missing*: Canvas viewport transformation matrix, mouse wheel scroll-to-zoom (`scale`), and mouse click-drag-to-pan (`offsetX, offsetY`).
  * **Node Selection** (`lines 690–705`):
    * `handleClick` triggers `onSelectCase(hoveredNode.caseData || foundCase)`. In `OverviewPage.jsx`, this passes `openCase` from `AppStateContext`.

---

### 1.2 Investigations Page & Filter Bar (`frontend/src/pages/InvestigationsPage.jsx`, `frontend/src/components/investigations/CaseFilterBar.jsx`)
* **File Locations**:
  * `frontend/src/pages/InvestigationsPage.jsx` (326 lines)
  * `frontend/src/components/investigations/CaseFilterBar.jsx` (149 lines)
* **Current Implementation Details**:
  * `InvestigationsPage.jsx` (`lines 191–257`) attaches `onClick={() => handleSelectCase(c)}` to each table row `<tr>`, and has an explicit "View Dossier →" button.
  * **Modal vs. Drawer Conflict**: `InvestigationsPage.jsx` mounts `<CaseDetailModal>` (`line 318`), while `MainLayout.jsx` (`lines 57–61`) globally mounts `<CaseDrawer>`. Selecting a case triggers `openCase(c)`, which causes both the modal and the right-side drawer to appear simultaneously.
  * **Status Filtering** (`CaseFilterBar.jsx lines 55–68`): Status filtering is currently a `<select>` dropdown (`ALL`, `OPEN`, `REVIEWED`, `ESCALATED`, `DISMISSED`, `RESOLVED`), whereas Verdict uses quick-click pill badges (`lines 99–122`).

---

### 1.3 CaseDrawer (`frontend/src/components/CaseDrawer.jsx`)
* **File Location**: `frontend/src/components/CaseDrawer.jsx` (239 lines)
* **Current Implementation Details**:
  * **DMV Velocity Gauge** (`lines 97–151`): Renders a linear progress bar (`<div className="h-2.5 w-full bg-slate-100 rounded-full..."><div style={{ width: `${dmvScore}%` }} /></div>`).
    * *Missing*: An animated semi-circular arc/dial gauge with distinct color zones (green <40, amber 40–70, red >70) and an animating needle.
  * **Rule Breakdown**:
    * Currently has *no* rule hits breakdown component. `CaseDetailModal.jsx` previously had a basic pill list.
    * *Missing*: A sorted horizontal bar chart (by risk points) built with Recharts (`ResponsiveContainer`, `BarChart`, `YAxis`, `XAxis`, `Tooltip`, `Bar`, `Cell`).
  * **SAR PDF Export** (`lines 20–32`, `214–222`):
    * Calls `api.downloadSarPdf(caseData.case_id)`.
    * On error, falls back silently to `window.open(api.sarPdfUrl(caseData.case_id), "_blank")`.
    * *Missing*: Validation of PDF binary content-type, prevention of corrupt file downloads on 500/HTML errors, and inline user-facing error toast notification.

---

### 1.4 ForensicImageViewer (`frontend/src/components/investigations/ForensicImageViewer.jsx`)
* **File Location**: `frontend/src/components/investigations/ForensicImageViewer.jsx` (120 lines)
* **Current Implementation Details**:
  * Directly requests `api.caseGraphUrl(caseId)` (`/upi/cases/${caseId}/graph.png`).
  * On error (`onError` line 78), sets `loadError = true` and renders placeholder text: `"Visual forensics PNG pending or generated on demand"`.
  * *Missing*:
    1. Direct static fallback attempt to `/static/upi_cases/${caseId}_ring.png` on initial 404.
    2. Smooth image fade-in CSS transition (`opacity-0` -> `opacity-100`).
    3. In-browser SVG vector ring topology fallback generated from `case.topology` or `case.ring_members_vpas` when backend PNG rendering is unavailable.

---

### 1.5 API Services & Model Schema (`frontend/src/services/api.js`, `app/models/upi_models.py`)
* **File Locations**:
  * `frontend/src/services/api.js` (262 lines)
  * `app/models/upi_models.py` (lines 23–28: `RuleHit`)
* **Current Implementation Details**:
  * `api.caseGraphUrl(caseId)` returns `/upi/cases/${caseId}/graph.png`.
  * `api.downloadSarPdf(caseId)` creates a blob without verifying `res.headers.get("content-type")`.
  * Backend `caseData` payload provides:
    * `rule_hits`: `List[RuleHit]` where each hit contains `{ code: string, points: number, detail: string }`.
    * `dmv_score`: float `0.0 – 100.0`.
    * `verdict`: `"BLOCK" | "HOLD" | "ALLOW"`.
    * `topology`: `{ trigger_txn, fan_in, hops, fan_out, transactions, edges }`.

---

## 2. Logic Chain

### 2.1 Physics & Animation Dynamics for NetworkConstellation
1. **Continuous Physics Drift**:
   * *Observation*: Velocities approach zero due to `0.88` damping factor without continuous ambient energy injection.
   * *Inference*: Adding continuous micro-harmonic ambient forces (`Math.sin(t * 1.2 + n.y * 0.02) * 0.03`) and dynamic edge rest-length oscillation (`95 + Math.sin(t * 1.8) * 3.5`) maintains organic motion and elastic edge vibration even when timeline playback is paused. Damping tuned to `0.91` preserves equilibrium without unbounded drift.
2. **Node Pulsing Glow per Verdict**:
   * *Observation*: Fraud analysts require immediate visual distinction between `BLOCK`, `HOLD`, and `ALLOW` verdicts across network nodes.
   * *Inference*: In the node render pass, evaluate verdict:
     * `BLOCK`: Multi-stage crimson halo with radius $R \times (1.8 + 0.5 \sin(3.5t))$, fill `#dc2626`.
     * `HOLD`: Amber halo with radius $R \times (1.5 + 0.35 \sin(2.5t))$, fill `#d97706`.
     * `ALLOW`: Neutral subtle glow with radius $R \times 1.2$, fill `#059669`.
3. **Edge Risk Gradient & Particle Dot Flow**:
   * *Observation*: Fund flows along high-risk laundering conduits need to be intuitively readable in the direction of money transfer.
   * *Inference*: Apply 3-color tier: Low (<40) = Teal (`rgba(20, 184, 166)`), Med (40–70) = Amber (`rgba(245, 158, 11)`), High (>70) = Crimson (`rgba(220, 38, 38)`). For each active/high-risk edge, render animated traveling particle dots along $(px, py) = (1-u)A + uB$ where $u = (t \cdot \text{speed} + \text{offset}) \pmod 1$.
4. **Interactive Viewport (Zoom & Pan)**:
   * *Observation*: Fixed coordinate canvas restricts exploration of dense multi-case graphs.
   * *Inference*: Maintain `{ scale, offsetX, offsetY }`. Wrap rendering in `ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);`. Convert screen mouse $(sx, sy)$ to world $(wx, wy) = ((sx - \text{offsetX})/\text{scale}, (sy - \text{offsetY})/\text{scale})$ for hit testing and node click selection.

### 2.2 Case Management & Triage Console
1. **Interactive Case Table & Drawer Unification**:
   * *Observation*: Two conflicting modal/drawer components mount on case selection.
   * *Inference*: Standardize on `CaseDrawer.jsx` as the single full-featured slide-over dossier. Remove `CaseDetailModal.jsx` from `InvestigationsPage.jsx` and ensure row clicks directly invoke `openCase(c)`.
2. **Instant Status Badge Filtering**:
   * *Observation*: Dropdown filter is slow and inconsistent with the Verdict pill buttons.
   * *Inference*: Add interactive status pill badges (`ALL`, `OPEN`, `ESCALATED`, `DISMISSED`, `REVIEWED`, `RESOLVED`) to `CaseFilterBar.jsx` that immediately filter the memoized `filteredCases` array without network roundtrips or page reload.

### 2.3 CaseDrawer Visual Forensics & Telemetry
1. **Animated DMV Arc Dial**:
   * *Observation*: Linear progress bars fail to convey the non-linear risk threshold dynamics of Dead Money Velocity.
   * *Inference*: Render an SVG arc dial gauge ($180^\circ$ semicircle) partitioned into Green (<40), Amber (40–70), and Red (>70) arc sectors. An animated needle with spring transition pivots to the angle $\theta = 180 + (\text{dmvScore} / 100) \times 180^\circ$.
2. **Recharts Rule Breakdown Bar Chart**:
   * *Observation*: Rule points must be prioritized visually by contribution weight.
   * *Inference*: Map `caseData.rule_hits` to sorted descending array `[{ name: detail || code, points: points, code }]`. Render with `<BarChart layout="vertical">` using `<Cell fill={points >= 35 ? '#ef4444' : points >= 20 ? '#f59e0b' : '#10b981'} />` and smooth `<Bar isAnimationActive={true} animationDuration={800} />`.
3. **Multi-Tier Forensic Image & SVG Fallback**:
   * *Observation*: Container restarts wipe out rendered PNGs, causing 404s.
   * *Inference*: Structure loading pipeline:
     * Step 1: Request `/upi/cases/${caseId}/graph.png`.
     * Step 2: On 404, request `/static/upi_cases/${caseId}_ring.png`.
     * Step 3: If both fail, seamlessly render `<SvgRingTopology topology={caseData.topology} caseData={caseData} />`, plotting nodes and bezier fund-flow paths directly in SVG.
4. **SAR PDF Binary Download & Error Toast**:
   * *Observation*: Non-PDF error responses produce corrupt downloads or silent failures.
   * *Inference*: Inspect `Content-Type` header in `api.downloadSarPdf`. If not `application/pdf`, raise an error with server response details. In `CaseDrawer`, catch error and display a styled error toast notification with auto-dismiss.

---

## 3. Caveats & Edge Cases

1. **Empty Topology / Single-Case Mode**:
   * Cases generated via lightweight simulation might have only `payer_vpa` and `payee_vpa` without explicit `topology.hops`. The SVG fallback and `extractChronologicalTopology` must synthesize synthetic 2-hop conduits or display the direct transaction cleanly without NaN coordinates.
2. **ESLint React Hooks Exhaustive-Deps**:
   * As per repository guidelines in `AGENTS.md`, canvas animation loops and RAF refs must not directly access mutable refs in cleanup without proper closure capture or `eslint-disable-next-line react-hooks/exhaustive-deps`.
3. **Recharts Responsive Sizing in Drawer**:
   * `CaseDrawer` slides in with Framer Motion. `ResponsiveContainer` needs explicit min-height (e.g. `height={Math.max(160, hits.length * 36)}`) to prevent zero-height render during slide-in animation.
4. **Canvas HiDPI Retina Scaling**:
   * High-DPI screens (`devicePixelRatio > 1`) require canvas backing-store multiplication while maintaining CSS dimensions to prevent pixelation on zoomed viewports.

---

## 4. Conclusion & Concrete Design Proposals

### 4.1 Component Blueprint: `NetworkConstellation.jsx`

```jsx
// Key Physics & Zoom additions:
// 1. Transform state
const transformRef = useRef({ scale: 1, x: 0, y: 0, isDragging: false, startX: 0, startY: 0 });

// 2. Ambient harmonic force in RAF frame loop:
const ambientAngle = t * 1.2 + n.x * 0.01 + n.y * 0.01;
n.vx += Math.cos(ambientAngle) * 0.035;
n.vy += Math.sin(ambientAngle) * 0.035;

// 3. Dynamic edge spring length oscillation:
const targetDist = 95 + Math.sin(t * 2.0 + (e.timestamp % 10)) * 3.5;
const f = (dist - targetDist) * 0.007;

// 4. Particle dot animation along edges:
const speed = 0.5 + ((e.riskScore || 50) / 100) * 0.5;
const u = ((t * speed + pIdx / 3) % 1);
const px = a.x + (b.x - a.x) * u;
const py = a.y + (b.y - a.y) * u;
ctx.fillStyle = e.riskScore >= 70 ? "#ef4444" : e.riskScore >= 40 ? "#f59e0b" : "#14b8a6";
ctx.beginPath();
ctx.arc(px, py, 3.0, 0, Math.PI * 2);
ctx.fill();

// 5. Verdict glow on nodes:
const verdict = n.caseData?.verdict || (n.kind === "hub" ? "BLOCK" : "HOLD");
const pulseRadius = r * (verdict === "BLOCK" ? 2.2 + 0.4 * Math.sin(t * 4) : verdict === "HOLD" ? 1.8 + 0.3 * Math.sin(t * 2.5) : 1.2);
const glowColor = verdict === "BLOCK" ? "rgba(220, 38, 38, 0.45)" : verdict === "HOLD" ? "rgba(245, 158, 11, 0.40)" : "rgba(16, 185, 129, 0.25)";
```

### 4.2 Component Blueprint: DMV Arc Dial Gauge (`DmvArcGauge.jsx`)

```jsx
export function DmvArcGauge({ score }) {
  const clamped = Math.max(0, Math.min(100, Number(score) || 0));
  // Map score [0, 100] to angle [-180, 0] degrees (left to right semicircle)
  const angle = -180 + (clamped / 100) * 180;
  
  return (
    <div className="flex flex-col items-center justify-center p-3 bg-slate-50/70 rounded-lg border border-hairline">
      <svg viewBox="0 0 200 115" className="w-48 overflow-visible">
        {/* Track Arcs */}
        <path d="M 20 100 A 80 80 0 0 1 76 34" fill="none" stroke="#10b981" strokeWidth="12" strokeLinecap="round" />
        <path d="M 78 33 A 80 80 0 0 1 122 33" fill="none" stroke="#f59e0b" strokeWidth="12" />
        <path d="M 124 34 A 80 80 0 0 1 180 100" fill="none" stroke="#ef4444" strokeWidth="12" strokeLinecap="round" />
        
        {/* Animated Needle */}
        <g transform="translate(100, 100)">
          <line
            x1="0" y1="0" x2="-62" y2="0"
            stroke="#1e293b" strokeWidth="3.5" strokeLinecap="round"
            style={{ transform: `rotate(${angle + 180}deg)`, transition: "transform 1s cubic-bezier(0.34, 1.56, 0.64, 1)" }}
          />
          <circle cx="0" cy="0" r="5" fill="#1e293b" />
        </g>
      </svg>
      <div className="text-center -mt-3">
        <span className="font-mono text-2xl font-bold text-ink-900">{clamped.toFixed(1)}</span>
        <span className="text-xs text-muted font-mono"> / 100</span>
      </div>
    </div>
  );
}
```

### 4.3 Component Blueprint: Recharts Rule Breakdown (`RuleBreakdownChart.jsx`)

```jsx
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

export function RuleBreakdownChart({ ruleHits = [] }) {
  const data = (ruleHits.length > 0 ? ruleHits : [{ code: "VELOCITY_BURST", points: 40, detail: "Velocity Surge" }])
    .map((h) => ({
      name: h.detail || h.code || h.rule_name || "Rule Hit",
      points: h.points || 25,
      code: h.code || "",
    }))
    .sort((a, b) => b.points - a.points);

  return (
    <div className="panel p-4 bg-white border border-hairline rounded-lg space-y-2">
      <div className="text-[10px] font-mono uppercase text-muted">Explainable Rule Contributions (Sorted)</div>
      <ResponsiveContainer width="100%" height={Math.max(140, data.length * 34)}>
        <BarChart layout="vertical" data={data} margin={{ top: 4, right: 24, left: 110, bottom: 4 }}>
          <XAxis type="number" domain={[0, "dataMax + 10"]} tick={{ fontSize: 10, fontFamily: "monospace" }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#334155" }} width={105} />
          <Tooltip formatter={(val) => [`${val} pts`, "Risk Contribution"]} />
          <Bar dataKey="points" radius={[0, 4, 4, 0]} isAnimationActive={true} animationDuration={800}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={entry.points >= 35 ? "#ef4444" : entry.points >= 20 ? "#f59e0b" : "#10b981"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### 4.4 Component Blueprint: Multi-Tier ForensicImageViewer & SVG Ring Topology Fallback

```jsx
export function SvgRingTopology({ topology, caseData }) {
  const collector = caseData?.trigger_txn?.payee_vpa || caseData?.payee_vpa || "collector@hub";
  const members = caseData?.ring_members_vpas || [];
  const victims = topology?.fan_in || members.slice(0, 3);
  const hops = topology?.hops || members.slice(3, 6);
  const cashouts = topology?.fan_out || members.slice(6);

  return (
    <div className="relative w-full h-[280px] bg-slate-900 rounded-lg overflow-hidden flex flex-col p-3">
      <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 border-b border-slate-800 pb-1.5">
        <span>IN-BROWSER VECTOR TOPOLOGY (FALLBACK)</span>
        <span className="text-amber-400">Ring Hash: {caseData?.ring_hash?.slice(0, 12) || "SYN-RING"}</span>
      </div>
      <svg viewBox="0 0 440 220" className="flex-1 w-full h-full">
        {/* SVG Bezier fund paths with markers */}
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
          </marker>
        </defs>
        {/* Collector Node */}
        <circle cx="220" cy="110" r="16" fill="#ef4444" className="animate-pulse" />
        <text x="220" y="114" textAnchor="middle" fill="#fff" fontSize="9" fontWeight="bold">HUB</text>
        {/* Render Victims (Left), Hops (Top/Bottom), Cashouts (Right) */}
      </svg>
    </div>
  );
}
```

---

## 5. Verification Method

### 5.1 Automated Test Suites
Run the full backend and frontend validation pipeline:
```bash
# 1. Backend validation (648+ tests)
./.venv/bin/pytest tests/ -v

# 2. Frontend ESLint validation (--max-warnings 0 enforced)
cd frontend && npm run lint

# 3. Frontend Production Build validation
npm run build
```

### 5.2 Manual Browser Verification Checklist
1. **Constellation (R3)**:
   * Open `http://localhost:5173/` or EC2 preview.
   * Observe auto-play timeline starting at $t=0$ and building network step-by-step.
   * Verify continuous organic drift of nodes even when paused (no rigid freeze).
   * Verify node glow pulses based on verdict (`BLOCK` = red, `HOLD` = amber, `ALLOW` = neutral).
   * Verify traveling particle dots along high-risk edges ($>70$).
   * Use mouse wheel to zoom in/out; click-drag canvas to pan.
   * Click any node $\to$ verify `CaseDrawer` slides out smoothly with case data.
2. **Investigations & CaseDrawer (R4, R1)**:
   * Navigate to `/investigations`.
   * Click any status badge in the filter bar (`OPEN`, `ESCALATED`, `DISMISSED`) $\to$ verify table filters instantly without page reload.
   * Click any row in the case table $\to$ verify drawer opens immediately.
   * Inspect DMV Score section $\to$ verify semi-circular arc dial gauge needle animates to score.
   * Inspect Rule Breakdown section $\to$ verify horizontal bar chart renders sorted bars by points.
   * Inspect Visual Forensics section $\to$ verify PNG loads or renders vector SVG ring fallback on 404 with smooth fade-in.
   * Click "Export SAR" $\to$ verify real PDF binary downloads as `SAR_<case_id>.pdf`. On failure, verify prominent inline error toast.
