# Comprehensive Analysis & Survey Report: R3 (Ambient Traffic for Velocity Chart) & R4 (Threat Intel UI Uniform White Redesign)

**Agent**: Survey Explorer 15.3  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_3`  
**Date**: 2026-09-04T13:20:00Z  
**Target Scope**: 
- R3: `frontend/src/components/VerdictVelocityChart.jsx`, `frontend/src/components/VerdictHistoryChart.jsx`, and `frontend/src/context/AppStateContext.jsx`
- R4: `frontend/src/pages/ThreatIntelPage.jsx`

---

## 1. Executive Summary

This survey provides a comprehensive diagnosis, architectural design, and concrete code blueprints for two major demo polish requirements in SAMPATI V2:

1. **R3: Ambient Traffic for Verdict Velocity Chart**: The chart currently looks flatlined and dead (at 0 tx/s) because:
   - Initial state in `AppStateContext.jsx` fills all 30 time buckets with `0`.
   - The 1-second interval ticker drains and resets the current bucket every 1000ms. In the absence of an active WebSocket event stream or continuous simulation, all rates remain strictly 0.
   - Within 30 seconds of any single batch simulation burst, all historical points exit the 30-second window, dropping the chart back to flat zero.
   - **Solution**: We design an organic, continuous ambient traffic simulation (2–5 TPS background `ALLOW` traffic) using a harmonic wave model with stochastic micro-jitter. This pre-populates the initial rolling window and continuously injects 2–5 TPS into the 1-second ticker, seamlessly adding on top of real burst traffic without corrupting backend KPI counters.

2. **R4: Threat Intel UI Uniform White & Typography Redesign**: `ThreatIntelPage.jsx` currently suffers from heavy visual disharmony, AI-slop typography, and cramped spacing:
   - **Undefined `.card` CSS Class**: Lines 535, 545, 555, 565, 581, 733, and 861 use `className="card ..."` which has NO definition in `index.css` or Tailwind, causing containers to render with transparent/patchy backgrounds against the gray `#f4f6fa` layout background.
   - **Dark Slate Clashes**: A dark gradient banner (`from-ink-900 via-slate-900 to-ink-900`) at the top and a pitch-black/slate-900 card (`from-slate-900 via-slate-800 to-ink-900`) inside the Campaign Clustering section violently clash with the clean white FinTech aesthetic.
   - **Fragmented Pastel & Gray Sections**: The 3-stage entity extraction pipeline uses a mishmash of `amber-50/50`, `indigo-50/50`, and `emerald-50/50` tinted cards with nested `bg-white/80` boxes and `bg-surface-muted/60` gray status bars.
   - **Clunky Typography & Emoji Spam**: Excessive use of unreadable `text-[9px]`, `text-[10px]`, `text-[11px]`, repetitive "Pre-Transaction" buzzwords, pseudo-technical jargon ("Vector Cosine Correlation", "Campaign Invariant Stats"), and random emoji icons (`⚡`, `▶`, `📱`, `🔗`, `🏷️`, `☍`).
   - **Solution**: A complete, breathable redesign into a uniform white aesthetic (`panel` / `bg-white border border-hairline rounded-xl shadow-xs`), professional FinTech typography (`font-serif` for titles/KPI numbers, `font-mono` for tokens, `font-sans` for body), clean white cards with crisp semantic borders, and removal of all emoji clutter.

---

## 2. Investigation of R3: Ambient Traffic for Verdict Velocity Chart

### 2.1 Component Structure & Data Flow
- `frontend/src/components/VerdictVelocityChart.jsx` is a re-export wrapper:
  ```javascript
  import VerdictHistoryChart from "./VerdictHistoryChart";
  export default VerdictHistoryChart;
  export { VerdictHistoryChart };
  ```
- The actual visualization is implemented in `frontend/src/components/VerdictHistoryChart.jsx`.
- In `frontend/src/pages/OverviewPage.jsx` (line 88):
  ```jsx
  <VerdictHistoryChart history={verdictHistory} />
  ```
- The `verdictHistory` prop is supplied by `useAppState()` from `frontend/src/context/AppStateContext.jsx`.

### 2.2 Root Cause Analysis: Why the Chart Flatlines and Looks Dead

#### Flaw 1: Flat Zero Initialization (`AppStateContext.jsx:71-87`)
```javascript
  const [verdictHistory, setVerdictHistory] = useState(() => {
    const now = Date.now();
    return Array.from({ length: 30 }, (_, i) => {
      const ts = now - (29 - i) * 1000;
      return {
        time: new Date(ts).toLocaleTimeString("en-IN", { hour12: false }),
        timestamp: ts,
        ALLOW: 0,
        HOLD: 0,
        BLOCK: 0,
        allowed: 0,
        held: 0,
        blocked: 0,
        total: 0,
      };
    });
  });
```
On initial page load, all 30 rolling data points are hardcoded with zeros. The user is greeted by a completely flat, horizontal line at $Y=0$.

#### Flaw 2: 1-Second Bucket Reset in Ticker (`AppStateContext.jsx:90-120`)
```javascript
  useEffect(() => {
    const ticker = setInterval(() => {
      const now = Date.now();
      const timeStr = new Date(now).toLocaleTimeString("en-IN", { hour12: false });

      const allowRate = currentBucketRef.current.ALLOW;
      const holdRate = currentBucketRef.current.HOLD;
      const blockRate = currentBucketRef.current.BLOCK;
      const totalRate = currentBucketRef.current.total;

      // Reset bucket for the upcoming 1s interval
      currentBucketRef.current = { ALLOW: 0, HOLD: 0, BLOCK: 0, total: 0 };

      setVerdictHistory((prev) => {
        const newPoint = {
          time: timeStr,
          timestamp: now,
          ALLOW: allowRate,
          ...
        };
        return [...prev.slice(1), newPoint];
      });
    }, 1000);

    return () => clearInterval(ticker);
  }, []);
```
When no transaction stream or simulation is active:
- `currentBucketRef.current.ALLOW` remains `0`.
- Every 1000ms, a new `{ ALLOW: 0, HOLD: 0, BLOCK: 0, total: 0 }` point is appended to `verdictHistory`, and the oldest point is dropped.
- If a simulation ran 30 seconds ago, its burst deltas slide out of the 30-element array. The chart returns to 0 tx/s and stops moving entirely.

#### Flaw 3: Recharts Area Path Collapse (`VerdictHistoryChart.jsx:197-232`)
- In `VerdictHistoryChart.jsx`:
  `currentTps = (latestPoint.ALLOW || 0) + (latestPoint.HOLD || 0) + (latestPoint.BLOCK || 0);`
  When all values are 0, `currentTps` displays `0 tx/s`.
- The `<Area>` SVG paths calculate $Y$-coordinates at the bottom of the chart (`height - margin.bottom`). Because all 30 data points are at $Y=0$, the chart renders a flat line on the floor.
- The Y-axis has no fixed domain floor, causing the axis to default to 0–0, completely flattening any visual perception of an active monitoring engine.

---

### 2.3 Proposed Solution Architecture for R3

#### 1. The Organic Ambient Traffic Mathematical Model
Payment rails (UPI/IMPS) never hit zero in production; there is continuous legitimate consumer commerce. In SAMPATI, legitimate traffic is classified as `ALLOW`.
To make the chart look alive and genuine, we introduce an organic ambient generator:
- **Rate Range**: $2.0 \text{ to } 5.0 \text{ tx/s}$ (strictly `ALLOW` traffic).
- **Harmonic Wave + Noise Formulation**:
  ```javascript
  const now = Date.now();
  // Phase rotates smoothly every 16 seconds (period ~ 16s)
  const phase = (now / 2500) % (2 * Math.PI);
  // Base 3.2 tx/s with ±1.1 harmonic wave and ±0.4 random jitter
  const rawAmbient = 3.2 + 1.1 * Math.sin(phase) + (Math.random() - 0.5) * 0.8;
  const ambientAllow = Math.max(2, Math.min(5, Math.round(rawAmbient)));
  ```
- **Why this is superior to pure random**: Pure random (`Math.floor(Math.random() * 4) + 2`) produces jagged, spiky, unnatural oscillations (2 -> 5 -> 2 -> 5 -> 3). The harmonic wave creates a smooth, breathing, organic wave that looks like actual network traffic rolling past an analyst's monitor.

#### 2. Seamless Blending with Real Traffic Bursts
When real traffic is received (from WebSocket `UPI_EVALUATED` events, auto-feed, or manual batch simulation):
- If `currentBucketRef.current.ALLOW > 0`:
  `const allowRate = currentBucketRef.current.ALLOW + Math.round(ambientAllow * 0.5);`
  The real burst sits naturally on top of the ambient floor. When the burst peaks (e.g. 25 tx/s) and finishes, the curve smoothly returns to the 2–5 tx/s ambient baseline rather than crashing into dead silence.
- `HOLD` and `BLOCK` rates remain strictly tied to actual flagged threats:
  `const holdRate = currentBucketRef.current.HOLD;`
  `const blockRate = currentBucketRef.current.BLOCK;`
  Ambient traffic NEVER fabricates fake threats, preserving statistical integrity.

#### 3. Pre-populated Rolling Window on Mount
In `AppStateContext.jsx`, initialize `verdictHistory` using the same harmonic function over the past 30 seconds:
```javascript
  const [verdictHistory, setVerdictHistory] = useState(() => {
    const now = Date.now();
    return Array.from({ length: 30 }, (_, i) => {
      const ts = now - (29 - i) * 1000;
      const phase = (ts / 2500) % (2 * Math.PI);
      const ambient = Math.max(2, Math.min(5, Math.round(3.2 + 1.1 * Math.sin(phase) + (Math.random() - 0.5) * 0.6)));
      return {
        time: new Date(ts).toLocaleTimeString("en-IN", { hour12: false }),
        timestamp: ts,
        ALLOW: ambient,
        HOLD: 0,
        BLOCK: 0,
        allowed: ambient,
        held: 0,
        blocked: 0,
        total: ambient,
      };
    });
  });
```
**Result**: The instant the page is loaded, the chart is already populated with a breathing, moving wave.

#### 4. Protecting Backend KPI Integrity
`stats.evaluated` and `stats.allowed` are polled from the FastAPI backend every 15s (`refreshStats()`). The ambient traffic ONLY operates in `verdictHistory` (the rolling TPS velocity time-series). We do NOT increment `stats.evaluated` in state, preventing state desynchronization or jumpy metric rewrites when `refreshStats()` fires from the server.

#### 5. Chart Stabilization in `VerdictHistoryChart.jsx`
- **Y-Axis Minimum Domain Floor**:
  ```jsx
  <YAxis
    allowDecimals={false}
    domain={[0, (dataMax) => Math.max(8, Math.ceil(dataMax * 1.25))]}
    tick={{ fontSize: 10, fill: "#6b7280", fontFamily: "monospace" }}
    axisLine={{ stroke: "#e5e7eb" }}
    tickLine={false}
    unit=" /s"
  />
  ```
  Setting a minimum domain floor of `8` prevents the Y-axis from twitching between 4 and 5 every second when ambient traffic is at 3–4 TPS.
- **Area Animation Tuning**:
  In Recharts, default area animation with 800ms duration on 1000ms intervals can cause jitter. Setting `animationDuration={400}` with `animationEasing="linear"` produces a silky-smooth oscilloscope glide.

---

## 3. Investigation of R4: Threat Intel UI Uniform White & Typography Redesign

### 3.1 Structural Flaw Inventory in `ThreatIntelPage.jsx`

| Component Section | Line Numbers | Current Problem | Impact |
|---|---|---|---|
| **Undefined `.card` class** | 535, 545, 555, 565, 581, 733, 861 | `className="card ..."` is used across 7 key containers, but `.card` is NOT defined anywhere in `index.css` or Tailwind. | Containers have no background or border defined; they render transparent over gray `bg-surface-muted`, looking patchy and unfinished. |
| **Hero Banner** | 496–531 | Heavy dark gradient: `bg-gradient-to-r from-ink-900 via-slate-900 to-ink-900 text-white` with dark buttons (`bg-slate-800`). | Clashes sharply with the clean white FinTech dashboard aesthetic; feels like an auto-generated AI template. |
| **Telemetry KPI Strip** | 534–576 | Transparent container; mixed font sizes (`text-[11px] font-mono`); inconsistent with `KpiStrip.jsx`. | Lacks the crisp white panel styling and serif typography seen on Overview and Analytics. |
| **Entity Extraction Flow (Left Col)** | 580–730 | 3-stage visual pipeline uses pastel colors (`bg-amber-50/50`, `bg-indigo-50/50`, `bg-emerald-50/50`), nested white/80 boxes, and gray status bar (`bg-surface-muted/60`). | Highly fragmented colors, boxed-in feeling, cramped `p-1.5` padding, tiny `text-[9px]`. |
| **Campaign Clustering Card (Right Col)** | 733–857 | Pitch-black card: `bg-gradient-to-br from-slate-900 via-slate-800 to-ink-900 text-white rounded-xl p-4.5 border border-slate-700` with dark sub-boxes (`bg-slate-800`). | Severe aesthetic contradiction. Having a pitch-black box next to pastel stages and gray secondary lists creates a visual disaster. |
| **Signal Feed & Detail Cards** | 861–1006 | Filter bar in gray `bg-surface-muted`; signals contain random emoji icons (`📱`, `⚡`, `🔗`, `🏷️`); inspect button in gray. | Looks like an AI hackathon demo rather than an institutional fraud intelligence console. |
| **Graph Nodes Null-Check Bug** | 1080 | `typeof node === 'object' ? (node.id || node.label || JSON.stringify(node)) : String(node)` | If a node in `linked_graph_nodes` is `null`, `typeof null === 'object'` evaluates to true, triggering `null.id` runtime TypeError. |

---

### 3.2 Proposed Redesign: Clean, Uniform White, Breathable Architecture

#### Design Principle: Uniform White & Refined Typography
- **Uniform White Base**: All containers use `.panel` or `bg-white border border-hairline rounded-xl shadow-xs`.
- **Typography Hierarchy**:
  - Section Headings: `font-serif text-lg font-bold text-ink-900 tracking-tight`
  - Page Title: `font-serif text-2xl sm:text-3xl font-bold text-ink-900 tracking-tight`
  - Body & Subtitles: `text-xs sm:text-sm text-muted leading-relaxed font-sans`
  - Identifiers & Code: `font-mono text-xs font-semibold text-ink-900`
  - KPI Big Numbers: `font-serif text-2xl sm:text-3xl font-bold tabular-nums text-ink-900`
- **Subtle Semantic Accents**: Semantic colors (emerald for valid/allowed, amber for warning/hold, rose for critical/block, indigo for graph tokens) are used strictly as subtle hairline borders, micro-badges, or pills, never as full-card dark background floods.

---

### 3.3 Detailed Redesign Specification by Section

#### Section 1: Page Header (Lines 496–531)
- **Replace**: Dark gradient hero banner.
- **With**: Crisp, clean white panel:
  ```jsx
  <div className="panel p-6 bg-white border border-hairline rounded-xl shadow-xs relative overflow-hidden">
    <div className="h-1 w-full bg-gradient-to-r from-saffron via-amber-400 to-verdict-allow absolute top-0 left-0" />
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pt-1">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200">
          <span className="w-2 h-2 rounded-full bg-saffron animate-pulse" />
          PRE-TRANSACTION INTELLIGENCE MESH
        </div>
        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ink-900 tracking-tight">
          Pre-Transaction Threat Intelligence
        </h1>
        <p className="text-xs font-serif italic text-muted">
          &ldquo;Everyone sees a piece. SAMPATI connects the dots.&rdquo;
        </p>
        <p className="text-xs text-muted max-w-2xl leading-relaxed">
          Early-warning interception engine capturing social engineering payloads (SMS, WhatsApp, Phishing portals) before money moves. Intercepted tokens correlate in real time against the central fraud graph to pre-arm UPI mule defense rails.
        </p>
      </div>

      <div className="flex flex-wrap md:flex-col gap-2.5 shrink-0">
        <button
          onClick={handleIngestMockSignal}
          className="px-4 py-2 rounded-lg bg-ink-900 hover:bg-ink-800 text-white font-semibold text-xs font-mono shadow-xs transition-colors flex items-center gap-2 justify-center"
        >
          <span>⚡</span>
          <span>Ingest Mock Signal</span>
        </button>
        <button
          onClick={handleSimulateBatch}
          className="px-4 py-2 rounded-lg bg-white hover:bg-surface-muted border border-hairline text-ink-900 font-semibold text-xs font-mono transition-colors shadow-xs flex items-center gap-2 justify-center"
        >
          <span>▶</span>
          <span>Simulate Batch (3x)</span>
        </button>
      </div>
    </div>
  </div>
  ```

#### Section 2: Telemetry KPI Strip (Lines 534–576)
- **Replace**: `card p-4 flex flex-col justify-between`.
- **With**: 4 uniform white panels with serif metrics:
  ```jsx
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div className="panel p-4 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between">
      <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
        Ingested Signals (24h)
      </span>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="text-2xl font-serif font-bold text-ink-900 tabular-nums">
          {totalSignalsCount || signals.length}
        </span>
        <span className="text-xs font-mono text-emerald-600 font-semibold">+12% vs avg</span>
      </div>
    </div>
    ...
  </div>
  ```

#### Section 3: Entity Extraction Flow (Lines 580–730)
- **Replace**: Clashing pastel boxes and cramped styling.
- **With**: Clean white card architecture:
  - Outer container: `panel p-6 bg-white border border-hairline rounded-xl shadow-xs space-y-5`
  - Clean selector: `bg-white border border-hairline rounded-md px-3 py-1.5 text-xs font-mono text-ink-900`
  - Action button: `px-3.5 py-1.5 bg-ink-900 text-white hover:bg-ink-800 text-xs font-mono font-semibold rounded-md transition-colors`
  - All 3 Stages sit on `bg-white border rounded-xl p-4 transition-all duration-300`:
    - Stage 1: Active border `border-amber-400 bg-white` with amber indicator pill. Payload in clean `bg-surface-muted/40 border border-hairline p-3 rounded-lg text-xs font-mono text-slate-700 italic`.
    - Stage 2: Active border `border-indigo-400 bg-white` with indigo indicator pill. Extracted tokens formatted cleanly in white rounded sub-cards with clear labels (`PHONE:`, `UPI VPA:`, `URL TOKEN:`).
    - Stage 3: Active border `border-emerald-500 bg-white` with emerald indicator pill. Linked Campaign in bold font-mono, pre-armed rule status in clean emerald pill.
  - Status footer: Pure white strip with hairline top border: `border-t border-hairline pt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs`.

#### Section 4: Suspected Campaign Clustering (Lines 733–857)
- **Replace**: The massive dark slate box (`bg-gradient-to-br from-slate-900 via-slate-800 to-ink-900`).
- **With**: Pure, luminous white FinTech panel:
  - Container: `panel p-6 bg-white border border-hairline rounded-xl shadow-xs space-y-5`
  - Hero Campaign Card:
    ```jsx
    <div className="bg-white border-2 border-rose-200 rounded-xl p-5 shadow-xs space-y-4 relative overflow-hidden">
      <div className="h-1 w-full bg-gradient-to-r from-rose-500 to-amber-500 absolute top-0 left-0" />
      <div className="flex items-center justify-between pt-1">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded">
            CRITICAL CAMPAIGN
          </span>
          <div className="text-lg font-mono font-bold text-ink-900 mt-1.5">
            {campaigns[0]?.campaign_id || "CAMP-KYC-PHISH-01"}
          </div>
          <div className="text-xs text-muted">
            {campaigns[0]?.name || "Coordinated KYC Phishing Campaign"}
          </div>
        </div>

        {/* Clean White Similarity Metric Box */}
        <div className="text-center bg-white border border-hairline rounded-xl p-3 min-w-[110px] shadow-xs">
          <div className="text-[10px] uppercase font-mono text-muted">Similarity</div>
          <div className="text-3xl font-serif font-bold text-ink-900 leading-tight">
            {Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%
          </div>
          <div className="text-[10px] font-mono text-emerald-700 font-semibold">High Match</div>
        </div>
      </div>

      {/* Progress Bar with light background */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-mono text-slate-600">
          <span>Vector Cosine Correlation</span>
          <span className="font-bold text-ink-900">{(campaigns[0]?.average_similarity || 0.94).toFixed(2)} / 1.00</span>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-hairline">
          <div
            className="h-full bg-gradient-to-r from-amber-400 to-rose-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%` }}
          />
        </div>
      </div>

      {/* Cluster Tags with clean white pills */}
      <div className="space-y-1.5">
        <div className="text-[10px] uppercase font-mono text-muted">Semantic &amp; Heuristic Cluster Tags:</div>
        <div className="flex flex-wrap gap-1.5">
          {["Bank impersonation", "Urgency", "KYC suspension", "PAN Freeze Alert", "APK Dropper"].map((t) => (
            <span
              key={t}
              className="text-xs font-mono bg-white text-slate-800 border border-hairline px-2.5 py-1 rounded-md shadow-xs"
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Stats Grid on clean white */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-hairline text-xs font-mono">
        <div>
          <span className="text-muted text-[10px] block uppercase">Signals Linked</span>
          <span className="font-serif text-base font-bold text-ink-900">{campaigns[0]?.signals_count ?? campaigns[0]?.threat_signals_count ?? 14} Signals</span>
        </div>
        <div>
          <span className="text-muted text-[10px] block uppercase">Mule VPAs Armed</span>
          <span className="font-serif text-base font-bold text-rose-700">{campaigns[0]?.associated_vpas_count ?? campaigns[0]?.member_count ?? 8} Accounts</span>
        </div>
        <div>
          <span className="text-muted text-[10px] block uppercase">Primary Rails</span>
          <span className="font-serif text-base font-bold text-ink-900">{campaigns[0]?.primary_rails || "SBI · HDFC"}</span>
        </div>
      </div>
    </div>
    ```
  - Secondary Campaign Roster: Pure white rows `bg-white hover:bg-slate-50 border border-hairline rounded-lg p-3 transition-colors flex items-center justify-between`.

#### Section 5: Live Signal Feed & Inspection Modal
- Outer container: `panel p-6 bg-white border border-hairline rounded-xl shadow-xs space-y-4`
- Filter Bar: Segmented control in `bg-surface-muted p-1 rounded-lg border border-hairline text-xs font-mono`, selected in `bg-white text-ink-900 font-bold shadow-xs px-3 py-1 rounded-md`.
- Signals Feed:
  - Generous card padding `p-5 rounded-xl border border-hairline bg-white hover:border-slate-300 transition-all shadow-xs hover:shadow-sm`.
  - Extracted Identifiers: Replace emojis with clean semantic label chips:
    - Phone: `bg-white text-slate-800 border border-slate-200 px-2.5 py-1 rounded-md text-xs font-mono font-medium shadow-xs` with SVG phone icon.
    - UPI VPA: `bg-indigo-50/70 text-indigo-900 border border-indigo-200 px-2.5 py-1 rounded-md text-xs font-mono font-bold shadow-xs` with SVG lightning icon.
    - URL: `bg-rose-50/70 text-rose-900 border border-rose-200 px-2.5 py-1 rounded-md text-xs font-mono font-medium truncate max-w-xs shadow-xs` with SVG link icon.
    - Tags: `bg-white text-slate-700 border border-hairline px-2 py-0.5 rounded text-[11px] font-mono`.
  - Detail Inspection Modal:
    - Pure white modal `bg-white rounded-xl shadow-2xl border border-hairline p-6 space-y-4`.
    - Fix the line 1080 null check bug:
      ```javascript
      node && typeof node === "object"
        ? (node.id || node.label || JSON.stringify(node))
        : String(node ?? "")
      ```

---

## 4. ESLint & Vite Build Constraints

1. **ESLint (`--max-warnings 0`) Rules**:
   - `react-hooks/exhaustive-deps`: In React `useEffect`, do not omit required dependencies.
   - React JSX quotes: Use `&ldquo;`, `&rdquo;`, and `&apos;` for unescaped quotes in JSX text.
   - Clean imports: Ensure no unused variables or orphaned React imports remain.
2. **Vite Build**:
   - Verify that all CSS classes are standard Tailwind or defined in `index.css`.
   - Ensure dynamic component resolution succeeds without Rollup bundling errors.

---

## 5. Summary of Recommended Actions for Implementing Agent

1. **In `frontend/src/context/AppStateContext.jsx`**:
   - Update `verdictHistory` initial state to pre-populate with 30 organic ambient points (2–5 TPS ALLOW) generated from a harmonic function.
   - In the 1-second ticker interval, compute `ambientAllow` (2–5 TPS harmonic wave). If `currentBucketRef.current.ALLOW > 0`, add real traffic to `ambientAllow * 0.5`. Otherwise use `ambientAllow`. Keep HOLD and BLOCK strictly based on real bucket counts.
2. **In `frontend/src/components/VerdictHistoryChart.jsx`**:
   - Set YAxis domain floor to `[0, (dataMax) => Math.max(8, Math.ceil(dataMax * 1.25))]`.
   - Configure area animation with `animationDuration={400}` and linear easing.
3. **In `frontend/src/pages/ThreatIntelPage.jsx`**:
   - Replace all 7 undefined `.card` containers with `.panel` / `bg-white border border-hairline rounded-xl shadow-xs`.
   - Replace dark hero banner with clean white page header card.
   - Redesign 3-stage entity extraction flow into pure white cards with active border highlights and clean typography.
   - Completely whitewash the Campaign Clustering card from dark slate-900 into crisp white with rose semantic highlights.
   - Clean up typography, remove emoji spam, and harden graph node unboxing at line 1080 (`node && typeof node === 'object'`).
