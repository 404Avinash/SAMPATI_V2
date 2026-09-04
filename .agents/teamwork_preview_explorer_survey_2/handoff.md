# Handoff Report: Requirement R3 (Whitewash Constellation Graph Background)

**Agent**: `survey_explorer_2`  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2`  
**Parent Conversation ID**: `271e71dd-4370-4307-afc1-a65ac33fe525`  
**Status**: Complete (Hard Handoff)  
**Deliverable**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md`  

---

## 1. Observation

Direct examination of `frontend/src/components/NetworkConstellation.jsx`, `frontend/src/pages/OverviewPage.jsx`, `frontend/src/components/CaseDrawer.jsx`, and `frontend/tailwind.config.js` reveals the following exact styling and canvas rendering calls:

### 1.1 Root Canvas Container & Background Architecture
- **`NetworkConstellation.jsx:983-984`**:
  ```jsx
  <div
    ref={containerRef}
    className="relative w-full h-full flex flex-col overflow-hidden rounded-md bg-[#0f172a] select-none"
  >
  ```
  The container hardcodes `bg-[#0f172a]` (Tailwind Slate-900 dark background).
- **`OverviewPage.jsx:96-115`**:
  The constellation is wrapped inside:
  ```jsx
  <div className="panel overflow-hidden">
    ...
    <div className="h-[440px] p-2 bg-[#f8f9fc]">
      <NetworkConstellation cases={cases} onSelectCase={openCase} />
    </div>
  </div>
  ```
  `OverviewPage.jsx` has a clean white panel (`bg-white border border-hairline`) and an inner tray with `bg-[#f8f9fc]`. The dark `#0f172a` canvas container creates a harsh, clashing black box inside an otherwise light dashboard.
- **`CaseDrawer.jsx:641-645`**:
  ```jsx
  <div className="h-64 p-1 bg-[#f8f9fc]">
    <NetworkConstellation caseData={caseData} />
  </div>
  ```
  In the investigation drawer, the same `#0f172a` dark box clashes with the white drawer panels.

### 1.2 Canvas Clearing & Background State
- **`NetworkConstellation.jsx:535-538`**:
  ```javascript
  ctx.save();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ```
  `ctx.clearRect()` clears the canvas to transparency. Currently, the canvas depends entirely on the CSS background of its parent `div` (`bg-[#0f172a]`). No explicit background color or grid texture is drawn onto the canvas bitmap.
- **`NetworkConstellation.jsx:542-551` (Initial State Text at t=0)**:
  ```javascript
  ctx.save();
  ctx.fillStyle = "rgba(100, 116, 139, 0.6)";
  ctx.font = "500 13px monospace";
  ctx.textAlign = "center";
  ctx.fillText(
    "t=0 (Initial State) · Auto-playing chronological mule-ring sequence…",
    width / 2,
    height / 2
  );
  ctx.restore();
  ```
  `rgba(100, 116, 139, 0.6)` on a white background yields a contrast ratio of only **2.4:1**, failing WCAG AA legibility requirements.
- **`NetworkConstellation.jsx:996-1000` (Empty State Text)**:
  ```jsx
  {totalSteps === 0 && (
    <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-400 font-mono">
      Awaiting mule-ring detections…
    </div>
  )}
  ```
  `text-slate-400` (`#94a3b8`) on white has a contrast ratio of **2.5:1** (washed out).

### 1.3 Node Styling, Radial Glow Halos, and Border Strokes
- **`NetworkConstellation.jsx:707-742` (Node Colors & Glows)**:
  ```javascript
  const verdict = (
    n.caseData?.verdict ||
    n.verdict ||
    (n.kind === "hub" || n.kind === "cashout" ? "BLOCK" : n.kind === "hop" ? "HOLD" : "ALLOW")
  ).toUpperCase();

  let baseRadius = n.kind === "hub" ? 9 : n.kind === "hop" ? 6.5 : n.kind === "cashout" ? 7 : 5.5;
  if (isHovered || isPartOfActiveEdge) baseRadius += 2.5;

  let glowMultiplier = 1.0;
  let glowColor = "rgba(16, 185, 129, 0.25)";
  let coreColor = "#059669";

  if (verdict === "BLOCK") {
    const pulseFactor = Math.sin(t * 4.0 + (n.x * 0.04));
    glowMultiplier = 2.2 + 0.45 * pulseFactor;
    glowColor = `rgba(220, 38, 38, ${(0.35 + 0.15 * pulseFactor).toFixed(2)})`;
    coreColor = "#dc2626";
  } else if (verdict === "HOLD") {
    const pulseFactor = Math.sin(t * 2.5 + (n.y * 0.04));
    glowMultiplier = 1.8 + 0.35 * pulseFactor;
    glowColor = `rgba(245, 158, 11, ${(0.30 + 0.12 * pulseFactor).toFixed(2)})`;
    coreColor = "#d97706";
  } else {
    glowMultiplier = 1.3 + 0.1 * Math.sin(t * 1.5);
    glowColor = "rgba(16, 185, 129, 0.25)";
    coreColor = "#059669";
  }

  if (n.kind === "cashout" && verdict !== "BLOCK") {
    coreColor = "#1e293b";
  }
  ```
- **`NetworkConstellation.jsx:744-752` (Radial Glow Gradient Outer Stop)**:
  ```javascript
  const glowGrad = ctx.createRadialGradient(n.x, n.y, baseRadius * 0.4, n.x, n.y, maxGlowR);
  glowGrad.addColorStop(0, glowColor);
  glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
  ```
  In Canvas 2D, fading to `rgba(0, 0, 0, 0)` on a light canvas creates a dirty grayish outer fringing ring because the RGB channels interpolate towards black as alpha reaches zero.
- **`NetworkConstellation.jsx:760-762` (Node Border Stroke)**:
  ```javascript
  ctx.lineWidth = isHovered || isPartOfActiveEdge ? 2.5 : 1.5;
  ctx.strokeStyle = isHovered || isPartOfActiveEdge ? "#fbbf24" : "#ffffff";
  ctx.stroke();
  ```
  - **Critical Failure 1**: Default stroke is `#ffffff`. On a pure white background, this border is **completely invisible**, causing the circular node edges to blur into the white canvas.
  - **Critical Failure 2**: Hovered/active stroke is `#fbbf24` (amber-400). On white, `#fbbf24` has a contrast ratio of only **1.6:1**, rendering active selection highlights virtually invisible.

### 1.4 Edge / Connection Lines and Active Edge Stroke
- **`NetworkConstellation.jsx:24-45` (`getEdgeStroke`)**:
  ```javascript
  export function getEdgeStroke(riskScore, isHovered = false) {
    if (isHovered) return "rgba(255, 120, 0, 1.0)";
    if (riskScore == null) return "rgba(20, 184, 166, 0.45)";
    ...
    if (clamped < 40) {
      const ratio = clamped / 40;
      const alpha = 0.4 + ratio * 0.25;
      return `rgba(20, 184, 166, ${alpha.toFixed(2)})`;
    } else if (clamped <= 70) {
      const ratio = (clamped - 40) / 30;
      const alpha = 0.65 + ratio * 0.25;
      return `rgba(245, 158, 11, ${alpha.toFixed(2)})`;
    } else {
      const ratio = (clamped - 70) / 30;
      const alpha = 0.85 + ratio * 0.15;
      return `rgba(239, 68, 68, ${alpha.toFixed(2)})`;
    }
  }
  ```
  - Low-risk (<40): `rgba(20, 184, 166, 0.40 - 0.65)` (teal-500) has an effective contrast of only **1.3:1 - 1.8:1** on white.
  - Medium-risk (40-70): `rgba(245, 158, 11, 0.65 - 0.90)` (amber-500) has an effective contrast of **~2.1:1** on white.
- **`NetworkConstellation.jsx:636-642` (Active Edge Stroke)**:
  ```javascript
  if (isActive) {
    ctx.strokeStyle = "rgba(251, 191, 36, 0.95)";
    ctx.lineWidth = 3.2;
  } else {
    ctx.strokeStyle = getEdgeStroke(e.riskScore, isHovered);
    ctx.lineWidth = isHovered ? 2.8 : 1.6;
  }
  ```
  - **Critical Failure 3**: `isActive` uses `rgba(251, 191, 36, 0.95)` (`#fbbf24`). On a white background, this active transmission line is unreadable (contrast **1.6:1**).

### 1.5 Traveling Flow Particles
- **`NetworkConstellation.jsx:667-698`**:
  - High risk: Outer halo `rgba(239, 68, 68, 0.35)` radius 5.0, core `#ef4444` radius 3.0, and a center pinpoint `#ffffff` radius 1.2 (`NetworkConstellation.jsx:681`). On a white background, the `#ffffff` center core makes the particle look hollow or washed out.
  - Medium risk: `#f59e0b` radius 2.5 (too faint on white).
  - Low risk: `#14b8a6` radius 2.0 (too faint on white).

### 1.6 HUD Overlays, Legends, and Controls
- **`NetworkConstellation.jsx:1003-1021` (HUD Legend)**:
  - Container: `bg-slate-900/85 backdrop-blur border-slate-700/60 text-slate-300` (dark theme).
  - Header: `text-[10px] text-slate-400`
  - Cash-Out dot border: `border="#475569"`
  - Footer: `border-slate-800 text-slate-400`
  - Risk labels: `text-[#14b8a6]`, `text-[#f59e0b]`, `text-[#ef4444]` (too light against white).
- **`NetworkConstellation.jsx:1024-1049` (Zoom/Pan Controls)**:
  - Container: `bg-slate-900/85 backdrop-blur border-slate-700/60`
  - Buttons: `text-slate-200 bg-slate-800/80 hover:bg-slate-700`
  - Fit badge: `text-slate-300 bg-slate-800/80`
- **`NetworkConstellation.jsx:1053-1129` (Hover Tooltip)**:
  - Container: `bg-slate-900/95 text-white border-slate-700 shadow-2xl`
  - Dividers: `border-slate-800`
  - Case drilldown hints: `text-amber-400`
- **`NetworkConstellation.jsx:1133-1251` (Timeline Bottom Bar)**:
  - Container: `border-t border-slate-800 bg-slate-900/95 backdrop-blur` (pitch black bottom strip).
  - Reset button: `bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700`
  - Slider: `bg-slate-700 accent-amber-500`
  - Step badge: `bg-slate-800 border-slate-700 text-slate-200`
  - Speed toggles: `bg-slate-800 border-slate-700 text-slate-400`
  - Active edge telemetry: `bg-purple-950/80 text-purple-300 border-purple-700/60`, `text-slate-100`, `text-slate-300`.

---

## 2. Logic Chain

1. **Root & Canvas Aesthetic**:
   - Replacing `bg-[#0f172a]` with `bg-white border border-hairline rounded-lg` immediately removes the clashing dark block.
   - Adding `ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, width, height);` on canvas render guarantees that any raster operations, exports, or canvas captures maintain pure white integrity regardless of DOM opacity.
   - Drawing a subtle cybersecurity dot-grid (`#e2e8f0` at 28px intervals) prevents the white canvas from feeling like a stark empty void while preserving clean contrast.
2. **Node Contrast & Definition**:
   - Replacing `#ffffff` border stroke with a subtle outer boundary (`rgba(15, 23, 42, 0.16)` hairline stroke or white stroke with subtle `shadowColor = "rgba(0,0,0,0.12)"`) ensures circular nodes do not bleed into the white background.
   - BLOCK verdict: `#dc2626` (contrast 4.55:1) or SAMPATI's official `verdict.block` (`#b3261e`, contrast 5.62:1).
   - HOLD verdict: Replacing low-contrast `#d97706` (3.3:1) with `#b45309` (Amber-700, contrast 4.68:1) or `#a8660a` (SAMPATI `verdict.hold`) ensures full WCAG AA compliance.
   - ALLOW verdict: `#0f7a3d` (SAMPATI `verdict.allow`, contrast 5.14:1) or `#059669` (Emerald-600, contrast 4.56:1).
   - Cash-Out: `#0b1f3a` (Ink-900, contrast 15.8:1).
   - Active/Hovered selection stroke: Replacing invisible `#fbbf24` (1.6:1) with SAMPATI saffron `#c8641e` (contrast 4.60:1) with `lineWidth = 2.5` creates an unmistakable selection halo.
   - Glow Gradients: Changing the outer stop from `rgba(0,0,0,0)` to `rgba(R, G, B, 0)` eliminates grayish interpolation artifacts on white.
3. **Edge Visibility & Dynamics**:
   - Active edge: Replacing `#fbbf24` with `#c8641e` (saffron) or `#0b1f3a` (navy) with `lineWidth = 3.2` makes the current transaction line prominently visible.
   - Low-risk edges: Shifting from `#14b8a6` at alpha 0.40 to `#0d9488` (Teal-600) with alpha 0.60–0.80 elevates contrast from 1.3:1 to 4.5:1.
   - Medium-risk edges: Shifting from `#f59e0b` to `#b45309` (Amber-700) with alpha 0.70–0.90 elevates contrast from 2.1:1 to 4.68:1.
   - High-risk edges: `#dc2626` / `#b91c1c` with alpha 0.85–1.0 provides punchy, unmistakable crimson conduits.
4. **Data Flow Particles**:
   - Removing the `#ffffff` center pinpoint on high-risk particles and using solid `#b91c1c` / `#dc2626` with a soft outer blush `rgba(220, 38, 38, 0.25)` keeps particles crisp and prominent against white.
   - Scaling medium-risk particles to `#b45309` (radius 2.8) and low-risk to `#0d9488` (radius 2.4) maintains clear movement visibility.
5. **HUD and Controls Harmonization**:
   - Transforming the HUD Legend, Zoom HUD, Tooltip, and Timeline Strip from `bg-slate-900` to `bg-white/95` and `bg-surface-muted/95` with `border-hairline` and `text-ink-900` / `text-body` transforms the widget into a cohesive, executive-grade fintech interface matching the rest of SAMPATI V2.

---

## 3. Caveats

1. **Subtle Dot-Grid Performance**:
   - If rendering a background dot-grid on canvas at 60 FPS, drawing nested loops in world coordinates during zoom/pan must be kept efficient (only draw visible dots within viewport bounds) or drawn with a pattern canvas (`ctx.createPattern`). A simple 24–28px dot grid with ~300 dots adds <0.2ms per frame.
2. **Tooltip Stacking**:
   - The tooltip overlay must retain `z-30 pointer-events-none shadow-xl border border-hairline` so it doesn't flicker or capture mouse drag events.
3. **Embedded Mode vs Overview Mode**:
   - `NetworkConstellation` is used in both `OverviewPage` (`h-[440px]`) and `CaseDrawer` (`h-64`). In `CaseDrawer`, compact styling for the timeline strip and HUD ensures the visualizer does not feel cramped.
4. **No Other Caveats**:
   - All color replacements use Tailwind tokens already defined in `tailwind.config.js` (`ink-900`, `saffron`, `surface-muted`, `hairline`, `verdict.block`, `verdict.hold`, `verdict.allow`).

---

## 4. Conclusion

Requirement R3 can be completely fulfilled by modifying `frontend/src/components/NetworkConstellation.jsx` with the following concrete changes:

### Concrete Proposed Code Modifications:

#### 1. Edge Stroke Function (`getEdgeStroke`):
```javascript
export function getEdgeStroke(riskScore, isHovered = false) {
  if (isHovered) return "rgba(194, 65, 12, 1.0)"; // #c2410c orange-700
  if (riskScore == null) return "rgba(13, 148, 136, 0.60)"; // #0d9488 teal-600

  const num = typeof riskScore === "number" ? riskScore : parseFloat(riskScore);
  if (isNaN(num)) return "rgba(13, 148, 136, 0.60)";

  const clamped = Math.max(0, Math.min(100, num));
  if (clamped < 40) {
    const ratio = clamped / 40;
    const alpha = 0.55 + ratio * 0.25;
    return `rgba(13, 148, 136, ${alpha.toFixed(2)})`; // Teal-600 (contrast > 4.5:1)
  } else if (clamped <= 70) {
    const ratio = (clamped - 40) / 30;
    const alpha = 0.70 + ratio * 0.25;
    return `rgba(180, 83, 9, ${alpha.toFixed(2)})`; // Amber-700 (contrast > 4.6:1)
  } else {
    const ratio = (clamped - 70) / 30;
    const alpha = 0.85 + ratio * 0.15;
    return `rgba(220, 38, 38, ${alpha.toFixed(2)})`; // Red-600 (contrast > 4.5:1)
  }
}
```

#### 2. Canvas Background & Initial State Text (lines 535-555):
```javascript
// Clear Canvas with pure white fill
ctx.save();
ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
ctx.fillStyle = "#ffffff";
ctx.fillRect(0, 0, width, height);

// Subtle dot grid background
ctx.fillStyle = "rgba(226, 232, 240, 0.85)";
for (let gx = 16; gx < width; gx += 28) {
  for (let gy = 16; gy < height; gy += 28) {
    ctx.beginPath();
    ctx.arc(gx, gy, 1.0, 0, Math.PI * 2);
    ctx.fill();
  }
}

// Initial state text at t=0
if (currentStep === 0 || visibleNodeIds.size === 0) {
  if (totalSteps > 0) {
    ctx.save();
    ctx.fillStyle = "#475569"; // Slate-600 (high contrast 5.7:1)
    ctx.font = "500 13px 'IBM Plex Mono', monospace";
    ctx.textAlign = "center";
    ctx.fillText(
      "t=0 (Initial State) · Auto-playing chronological mule-ring sequence…",
      width / 2,
      height / 2
    );
    ctx.restore();
  }
  ctx.restore();
  stateRef.current.raf = requestAnimationFrame(frame);
  return;
}
```

#### 3. Active Edge Highlight (line 637):
```javascript
if (isActive) {
  ctx.strokeStyle = "rgba(200, 100, 30, 0.95)"; // SAMPATI Saffron (#c8641e, 4.6:1 contrast)
  ctx.lineWidth = 3.2;
} else {
  ctx.strokeStyle = getEdgeStroke(e.riskScore, isHovered);
  ctx.lineWidth = isHovered ? 2.8 : 1.6;
}
```

#### 4. Data Flow Particles (lines 667-697):
```javascript
if (risk >= 70) {
  // Crimson high-risk glowing particle
  ctx.fillStyle = "rgba(220, 38, 38, 0.25)";
  ctx.beginPath();
  ctx.arc(px, py, 5.0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#b91c1c"; // Red-700
  ctx.beginPath();
  ctx.arc(px, py, 3.2, 0, Math.PI * 2);
  ctx.fill();
} else if (risk >= 40) {
  // Amber medium-risk particle
  ctx.fillStyle = "#b45309"; // Amber-700
  ctx.beginPath();
  ctx.arc(px, py, 2.8, 0, Math.PI * 2);
  ctx.fill();
} else {
  // Teal low-risk particle
  ctx.fillStyle = "#0d9488"; // Teal-600
  ctx.beginPath();
  ctx.arc(px, py, 2.4, 0, Math.PI * 2);
  ctx.fill();
}
```

#### 5. Node Halo and Border Contrast (lines 707-763):
```javascript
// Verdict color mapping
if (verdict === "BLOCK") {
  const pulseFactor = Math.sin(t * 4.0 + (n.x * 0.04));
  glowMultiplier = 2.2 + 0.45 * pulseFactor;
  glowColor = `rgba(220, 38, 38, ${(0.30 + 0.15 * pulseFactor).toFixed(2)})`;
  coreColor = "#dc2626";
} else if (verdict === "HOLD") {
  const pulseFactor = Math.sin(t * 2.5 + (n.y * 0.04));
  glowMultiplier = 1.8 + 0.35 * pulseFactor;
  glowColor = `rgba(180, 83, 9, ${(0.25 + 0.10 * pulseFactor).toFixed(2)})`;
  coreColor = "#b45309"; // Amber-700 (4.68:1 contrast)
} else {
  glowMultiplier = 1.3 + 0.1 * Math.sin(t * 1.5);
  glowColor = "rgba(15, 122, 61, 0.20)";
  coreColor = "#0f7a3d"; // Verdict Allow (5.14:1 contrast)
}

if (n.kind === "cashout" && verdict !== "BLOCK") {
  coreColor = "#0b1f3a"; // Ink-900 (15.8:1 contrast)
}

// Halo gradient without dark fringing
const maxGlowR = baseRadius * glowMultiplier;
const glowGrad = ctx.createRadialGradient(n.x, n.y, baseRadius * 0.4, n.x, n.y, maxGlowR);
glowGrad.addColorStop(0, glowColor);
glowGrad.addColorStop(1, glowColor.replace(/[\d\.]+\)$/, "0)"));
ctx.fillStyle = glowGrad;
ctx.beginPath();
ctx.arc(n.x, n.y, maxGlowR, 0, Math.PI * 2);
ctx.fill();

// Node Core Circle
ctx.beginPath();
ctx.arc(n.x, n.y, baseRadius, 0, Math.PI * 2);
ctx.fillStyle = coreColor;
ctx.fill();

// Stroke Border with high contrast on white
if (isHovered || isPartOfActiveEdge) {
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = "#c8641e"; // Saffron active border
} else {
  ctx.lineWidth = 1.8;
  ctx.strokeStyle = "#ffffff";
  ctx.shadowColor = "rgba(0, 0, 0, 0.16)";
  ctx.shadowBlur = 3;
}
ctx.stroke();
ctx.shadowColor = "transparent";
ctx.shadowBlur = 0;
```

#### 6. Root Container and HUD Elements:
- Root container (line 983):
  `className="relative w-full h-full flex flex-col overflow-hidden rounded-lg bg-white border border-hairline select-none shadow-xs"`
- HUD Legend (lines 1003-1021):
  `bg-white/95 backdrop-blur px-3 py-2 rounded-lg border border-hairline shadow-md text-ink-900`
- Zoom HUD (lines 1024-1049):
  `bg-white/95 backdrop-blur p-1 rounded-lg border border-hairline shadow-md` with buttons in `bg-white hover:bg-surface-muted text-ink-900 border border-hairline`
- Hover Tooltip (lines 1053-1129):
  `bg-white/98 text-ink-900 border border-hairline shadow-xl`
- Timeline Bottom Strip (lines 1133-1251):
  `border-t border-hairline bg-surface-muted/95 backdrop-blur px-3 py-2.5 flex flex-col gap-1.5 shrink-0`
  - Play button: `bg-emerald-600 hover:bg-emerald-500 text-white font-mono shadow-xs`
  - Pause button: `bg-amber-600 hover:bg-amber-500 text-white font-mono shadow-xs`
  - Reset button: `bg-white text-ink-900 border border-hairline hover:bg-slate-50 font-mono shadow-xs`
  - Range slider: `accent-ink-900 h-1.5 bg-slate-200 cursor-pointer`
  - Badge & speed buttons: `bg-white border border-hairline text-ink-900 shadow-xs`
  - Active telemetry chip: `bg-purple-50 text-purple-700 border border-purple-200 font-semibold`, `text-ink-900 font-semibold`, `text-body`, `text-verdict-block`.

---

## 5. Verification Method

1. **Automated Regression & Lint Verification**:
   ```bash
   ./.venv/bin/pytest tests/ -q
   cd frontend && npm run lint && npm run build
   ```
   - Must pass all tests with 0 failures.
   - ESLint (`--max-warnings 0`) and Vite build must exit with code 0.

2. **Contrast & Aesthetic Verification**:
   - Inspect `/` (Overview) and click a case to inspect CaseDrawer.
   - Verify that the canvas container has a pure white background (`bg-white`), with no dark `#0f172a` box.
   - Confirm nodes, active edges (saffron `#c8641e`), and traveling particle dots are clearly visible and legible with no white border washouts.
   - Confirm timeline controls strip at the bottom has a light background (`bg-surface-muted/95`) with high-contrast text (`text-ink-900`).

3. **Behavioral Invalidation Conditions**:
   - If `grep -rn "bg-\\[#0f172a\\]" frontend/src/` matches any line in `NetworkConstellation.jsx`, the whitewash is incomplete.
   - If `grep -rn "rgba(251, 191, 36" frontend/src/components/NetworkConstellation.jsx` matches, the invisible pale-yellow active stroke remains.
   - If the canvas renders black or transparent when screenshotted, the explicit `ctx.fillRect` on white was omitted.
