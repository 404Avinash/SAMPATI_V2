# Deep Architectural Survey: R2 — Separating Topology Visualizers into a Dedicated Space / Sub-Navbar

**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_2`  
**Date**: 2026-09-04  
**Target Feature**: R2 — Separate Topology Visualizer (`NetworkConstellation` & `GeoMuleMap`) into Dedicated Space / Sub-Navbar  
**Scope**: `frontend/src/pages/OverviewPage.jsx`, `frontend/src/components/common/Navbar.jsx`, `frontend/src/App.jsx`, `frontend/src/components/NetworkConstellation.jsx`, `frontend/src/components/overview/GeoMuleMap.jsx`, `tests/frontend_contracts_test.py`, `tests/test_tier1_features.py`.

---

## 1. Executive Summary

In the current dashboard layout, both the **Network Constellation Force-Directed Graph** (`NetworkConstellation.jsx`) and the **Geographic India Mule Corridors Map** (`GeoMuleMap.jsx`) are shoehorned into a single `440px` tall panel in the middle of `OverviewPage.jsx`. This creates two major problems:
1. **Severe Visual Cramping**: The Constellation canvas contains a 60 FPS physics engine, multi-step playback timeline controls, zoom/pan HUD, and node inspection tooltips. The Geo Mule Map features a `0 0 600 680` SVG with animated bezier arcs, radar hotspot epicenters, and corridor filters. Confining both to `440px` leaves only ~340px of active drawable canvas, suffocating complex multi-hop mule rings and making India map labels microscopic.
2. **Overview Page Clutter**: The Overview page spans over `2000px` vertically. Users must scroll through KPI cards, velocity charts, and controls, navigate past the heavy visualizer panel, and scroll further down to reach the operational `LiveFeed` worklist and `VerdictDonut`.

This survey details a **clean, production-grade architecture** to extract `NetworkConstellation` and `GeoMuleMap` into a **dedicated top-level space (`/topology`)** featuring a **dedicated sub-navbar**, while providing a streamlined summary preview on `OverviewPage.jsx` that **strictly preserves 100% compatibility with all 969 backend and frontend tests**.

---

## 2. Codebase Investigation & Current Implementation

### 2.1 File Inspection: `frontend/src/pages/OverviewPage.jsx`
- **Lines 14 & 97–147**: Holds state `topologyTab = "constellation" | "geomap"`:
  ```jsx
  <div className="panel overflow-hidden">
    <div className="panel-header flex items-center justify-between">
      <div className="panel-title">
        <div className="text-[11px] uppercase tracking-wide text-muted font-mono">Topology Visualizer</div>
        <div className="font-serif font-bold text-ink-900">Live Constellation &amp; Mule Rings</div>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex bg-surface-muted rounded-lg p-0.5 border border-hairline text-xs font-mono">
          <button onClick={() => setTopologyTab("constellation")}>☍ Constellation Graph</button>
          <button onClick={() => setTopologyTab("geomap")}>🗺️ India Mule Corridors</button>
        </div>
        <span className="px-2 py-0.5 rounded bg-surface-muted border border-hairline">
          {cases.length} active rings tracked
        </span>
      </div>
    </div>
    <div className="h-[440px] p-2 bg-[#f8f9fc]">
      {topologyTab === "constellation" ? (
        <NetworkConstellation cases={cases} onSelectCase={openCase} />
      ) : (
        <GeoMuleMap cases={cases} onSelectCase={openCase} />
      )}
    </div>
  </div>
  ```
- **Observations**:
  - `h-[440px]` hardcoded container forces the canvas bitmap and SVG to shrink into a cramped letterbox.
  - The local button group is currently an inline toggle, not a proper sub-navigation system.
  - Clicking on nodes or corridors triggers `openCase`, opening the global `CaseDrawer`.

### 2.2 File Inspection: `frontend/src/components/NetworkConstellation.jsx`
- **Scale & Capabilities**: 1,286 lines of rich canvas logic.
- **Components & Controls**:
  - HTML5 Canvas with force-directed physics (repulsion, spring tension, gravity).
  - Fraud playback scrubber timeline (`handlePlay`, `handlePause`, `handleReset`, speed multiplier, step slider `type="range"`).
  - Viewport navigation (zoom HUD `+`, `-`, reset, click-drag panning with DPR compensation).
  - Legend badge strip (Collector Hub, Victim / Payer, Layering Hop, Cash-Out Exit).
  - Node & edge hover inspection tooltips with formatted INR amounts and VPA identifiers.
- **Cramping Impact**: The HUD controls, timeline bar, and legends consume ~90px vertically, leaving only ~350px for the canvas. When rendering cases with 15+ nodes across 4 hops, nodes overlap and edges cluster excessively unless zoomed in heavily.

### 2.3 File Inspection: `frontend/src/components/overview/GeoMuleMap.jsx`
- **Scale & Capabilities**: 528 lines of custom SVG mapping.
- **Geometry**: India SVG path normalized to `viewBox="0 0 600 680"` (aspect ratio 0.88).
- **Features**:
  - 8+ Indian financial & threat hubs: Delhi NCR, Mewat, Jamtara, Mumbai, Ahmedabad, Bengaluru, Hyderabad, Kolkata, Pune.
  - Quadratic Bezier animated arcs (`<path className="animate-dash" ... />`) representing active mule corridors with animated pulse markers.
  - Hotspot radar pulse rings (e.g. Mewat SIM-swap syndicates, Jamtara phishing origins).
  - Severity risk filter bar (`ALL`, `CRITICAL`, `HIGH`).
  - Monitored hubs telemetry bar.
- **Cramping Impact**: Because `viewBox` is `600x680`, placing it in a container with height `440px` forces the width to shrink to ~388px. Wide modern desktop screens (1440px to 1920px) show vast empty margins on either side of the map while the map itself is squashed.

### 2.4 File Inspection: `frontend/src/App.jsx` & `frontend/src/components/common/Navbar.jsx`
- **Routing in `App.jsx`**:
  - Uses React Router v6 with `MainLayout` wrapping child routes: `/overview`, `/threat-intel`, `/investigations`, `/investigations/:caseId`, `/analytics`, `/health`, `/settings`.
- **Navigation in `Navbar.jsx`**:
  - Top fixed navigation bar rendering `NAV_ITEMS`.
  - Desktop nav links + responsive horizontal-scrolling mobile nav bar.
  - Supports badge counters (e.g. `openCasesCount` on Investigations), pulse indicators (System Health), and telemetry refresh button.

---

## 3. Test Suite Regression Analysis

We executed the full test suite and analyzed all test contracts:

### 3.1 Existing Baseline Status
- **Pytest**: `969 passed, 6 warnings in 127.20s` (100% pass rate across all tiers: Tier 1 Features, Tier 2 Boundaries, Tier 3 Combinations, Tier 4 Scenarios, Tier 5 Adversarial, Sprint 2 & M1/M2/M3 suites).
- **Ruff**: `All checks passed!` (`ruff check app tests`).
- **Frontend ESLint**: `0 errors, 0 warnings` (`npm run lint` with `--max-warnings 0`).
- **Frontend Vite Build**: `✓ built in 10.19s` (`dist/index.html` 0.88 kB, `dist/assets/index.js` 1,099 kB).

### 3.2 Key Frontend AST & String Contract Invariants
We systematically reviewed every assertion in `tests/frontend_contracts_test.py` and `tests/test_tier1_features.py`:

| Test Function | Target File | Exact Assertion / Invariant | Impact of Extracting Topology | Mitigation / Compliance Strategy |
|---|---|---|---|---|
| `test_f15_01_app_layout_order` (`test_tier1_features.py:717`) | `OverviewPage.jsx` | `content.find("KpiStrip") != -1`<br>`content.find("NetworkConstellation") != -1`<br>`kpi_idx < constellation_idx` | **CRITICAL**: If `NetworkConstellation` is completely erased from `OverviewPage.jsx`, this test **FAILS**. | Keep a streamlined "Topology Intelligence Snapshot" in `OverviewPage.jsx` that imports and renders `NetworkConstellation` (in compact or quick-preview mode) after `KpiStrip`. |
| `test_five_dedicated_pages_exist_in_pages_directory` (`frontend_contracts_test.py:181`) | `frontend/src/pages/` | Requires `OverviewPage.jsx`, `InvestigationsPage.jsx`, `AnalyticsPage.jsx`, `SystemHealthPage.jsx`, `SettingsPage.jsx`. | **NONE**: All 5 pages remain intact. Adding `TopologyPage.jsx` does not violate this list. | Keep all 5 pages. Add `TopologyPage.jsx` alongside them. |
| `test_routes_coverage_in_app_jsx` (`frontend_contracts_test.py:203`) | `frontend/src/App.jsx` | Asserts `route in content` for `["/overview", "/investigations", "/analytics", "/health", "/settings"]`. | **NONE**: Adding `/topology` adds a new route without removing any of the existing 5 routes. | Add `<Route path="/topology" ... />` inside `Routes`. |
| `test_navbar_navigation_state` (`frontend_contracts_test.py:223`) | `Navbar.jsx` | Asserts `NavLink`, `Overview`, `Investigations`, `Analytics`, `Health`, `Settings`. | **NONE**: Adding `Topology` to `NAV_ITEMS` preserves all existing labels. | Add `{ to: "/topology", label: "Topology Mesh", ... }` to `NAV_ITEMS`. |
| `test_main_layout_and_outlet_contract` (`frontend_contracts_test.py:214`) | `MainLayout.jsx` | Asserts `Navbar` and `Outlet`. | **NONE**: `MainLayout.jsx` remains completely untouched. | Route runs inside existing `Outlet`. |
| `test_network_constellation_jsx_contains_canvas_interaction` | `NetworkConstellation.jsx` | Asserts `canvasRef`, `onMouseMove`/`mousemove`, `onClick`/`click`. | **NONE**: Component internal implementation is preserved. | No breaking changes to `NetworkConstellation.jsx`. |
| `test_case_drawer_embeds_network_constellation` | `CaseDrawer.jsx` | Asserts `NetworkConstellation` and `caseData={caseData}` in `CaseDrawer.jsx`. | **NONE**: `CaseDrawer.jsx` is not altered. | Untouched. |

---

## 4. Proposed Clean Architecture

### 4.1 Architecture Overview
We propose a **two-tier complementary architecture**:
1. **Dedicated Top-Level Space**: `frontend/src/pages/TopologyPage.jsx` accessible at `/topology` (with dedicated entry in `Navbar.jsx`).
2. **Dedicated Sub-Navbar**: An interactive, sticky view controller within `TopologyPage.jsx` allowing analysts to switch seamlessly between:
   - `☍ Constellation Physics Mesh` (Full-screen interactive canvas graph)
   - `🗺️ India Mule Corridors` (Full-height geospatial corridor map)
   - `⛶ Dual Perspective / Split View` (Side-by-side synchronized view for wide displays)
3. **Streamlined Overview Snapshot**: `OverviewPage.jsx` replaces the cramped 440px monolithic box with an executive **"Live Topology & Corridors Snapshot"** card linking directly to `/topology`, while embedding a sleek compact preview of `NetworkConstellation` to satisfy `test_f15_01_app_layout_order`.

---

### 4.2 Detailed Component Specification

#### A. New Page: `frontend/src/pages/TopologyPage.jsx`
- **Location**: `frontend/src/pages/TopologyPage.jsx`
- **Container Sizing**: `h-[calc(100vh-12rem)] min-h-[720px] max-h-[920px]` providing full real estate (>65% larger active canvas area).
- **Sub-Navbar Structure**:
  ```jsx
  {/* Dedicated Topology Sub-Navbar */}
  <div className="bg-white border border-hairline rounded-xl p-3 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
    {/* Left: View Mode Segmented Controls */}
    <div className="flex items-center gap-1 bg-surface-muted p-1 rounded-lg border border-hairline text-xs font-mono">
      <button
        onClick={() => setViewMode("constellation")}
        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md font-semibold transition-all ${
          viewMode === "constellation" ? "bg-white text-ink-900 shadow-xs border border-hairline" : "text-muted hover:text-ink-900"
        }`}
      >
        <span>☍</span>
        <span>Constellation Graph</span>
      </button>
      <button
        onClick={() => setViewMode("geomap")}
        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md font-semibold transition-all ${
          viewMode === "geomap" ? "bg-white text-ink-900 shadow-xs border border-hairline" : "text-muted hover:text-ink-900"
        }`}
      >
        <span>🗺️</span>
        <span>India Mule Corridors</span>
      </button>
      <button
        onClick={() => setViewMode("dual")}
        className={`hidden lg:flex items-center gap-2 px-3.5 py-1.5 rounded-md font-semibold transition-all ${
          viewMode === "dual" ? "bg-white text-ink-900 shadow-xs border border-hairline" : "text-muted hover:text-ink-900"
        }`}
      >
        <span>⛶</span>
        <span>Dual Perspective</span>
      </button>
    </div>

    {/* Center: Live Telemetry Badges */}
    <div className="flex items-center gap-3 text-xs font-mono">
      <span className="px-2.5 py-1 rounded bg-surface-muted border border-hairline text-ink-900 flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <strong>{cases.length}</strong> Active Rings
      </span>
      <span className="hidden sm:inline-flex px-2.5 py-1 rounded bg-surface-muted border border-hairline text-muted">
        <strong>9</strong> Monitored Hubs
      </span>
      <span className="hidden sm:inline-flex px-2.5 py-1 rounded bg-surface-muted border border-hairline text-rose-700">
        <strong>₹6.78 Cr</strong> Intercepted
      </span>
    </div>

    {/* Right: Operational Tool Controls */}
    <div className="flex items-center gap-2">
      <button onClick={toggleFullscreen} className="btn-secondary text-xs" title="Toggle Fullscreen Canvas">
        ⛶ Fullscreen
      </button>
      <button onClick={runSimulation} disabled={busy} className="btn-secondary text-xs">
        ⚡ Simulate
      </button>
    </div>
  </div>
  ```

- **Visualizer Layout Modes**:
  1. `viewMode === "constellation"`:
     - Renders `<NetworkConstellation cases={cases} onSelectCase={openCase} />` inside a full-height container (`h-full min-h-[680px]`).
     - Force-directed physics has room to expand without edge clustering. Scrubber and zoom HUD rest comfortably at edges without obscuring graph nodes.
  2. `viewMode === "geomap"`:
     - Renders `<GeoMuleMap cases={cases} onSelectCase={openCase} />` inside a full-height container (`h-full min-h-[680px]`).
     - India vector map SVG scales cleanly to `680px` height with crisp typography, clearly distinguishable animated corridor arcs, and legible hub telemetry cards.
  3. `viewMode === "dual"`:
     - High-impact visual for demos on 1080p+ monitors:
       ```jsx
       <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 h-full min-h-[680px]">
         <div className="panel h-full"><NetworkConstellation cases={cases} onSelectCase={openCase} /></div>
         <div className="panel h-full"><GeoMuleMap cases={cases} onSelectCase={openCase} /></div>
       </div>
       ```

#### B. Top Navigation Bar: `frontend/src/components/common/Navbar.jsx`
- Add new item to `NAV_ITEMS`:
  ```javascript
  {
    to: "/topology",
    label: "Topology Mesh",
    badgeKey: "topology",
    icon: (
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    ),
  }
  ```
- Placement order:
  `Overview -> Threat Intelligence -> Topology Mesh -> Investigations -> Analytics -> System Health -> Settings`.
  - Fits cleanly into the desktop navbar (1400px width easily accommodates 7 items).
  - Automatically included in mobile scrolling nav without extra configuration.

#### C. App Router: `frontend/src/App.jsx`
- Import:
  `import TopologyPage from "./pages/TopologyPage";`
- Route registration:
  ```jsx
  <Route path="/topology" element={<TopologyPage />} />
  <Route path="/topology/:viewMode" element={<TopologyPage />} />
  ```

#### D. Streamlined Overview Page: `frontend/src/pages/OverviewPage.jsx`
- Replace lines 97–147 with a clean, executive **Topology Mesh Snapshot**:
  ```jsx
  {/* Mule-Network Topology Snapshot & Dedicated Space Launcher */}
  <div className="panel overflow-hidden">
    <div className="panel-header flex items-center justify-between">
      <div className="panel-title">
        <div className="text-[11px] uppercase tracking-wide text-muted font-mono">
          Fraud Mesh Intelligence
        </div>
        <div className="font-serif font-bold text-ink-900 flex items-center gap-2">
          <span>Topology &amp; Mule Corridors</span>
          <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-saffron/10 text-saffron border border-saffron/20">
            {cases.length} active rings
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Link
          to="/topology"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold bg-ink-900 text-white hover:bg-ink-800 transition-colors shadow-xs"
        >
          <span>Open Dedicated Topology Space</span>
          <span>→</span>
        </Link>
      </div>
    </div>

    {/* Compact Preview Container */}
    <div className="h-[280px] p-2 bg-[#f8f9fc] relative">
      <NetworkConstellation cases={cases} onSelectCase={openCase} />
      <div className="absolute top-4 right-4 z-20">
        <Link
          to="/topology"
          className="px-2.5 py-1 rounded bg-white/90 backdrop-blur text-xs font-mono font-semibold text-ink-900 border border-hairline shadow-xs hover:bg-white flex items-center gap-1.5"
        >
          <span>⛶ Expand Fullscreen View</span>
        </Link>
      </div>
    </div>
  </div>
  ```
- **Benefits**:
  1. Reduces Overview vertical height from ~2000px to ~1700px, creating a tight, fast, responsive executive dashboard.
  2. Directly preserves the `KpiStrip` -> `NetworkConstellation` order required by `test_tier1_features.py:717`.
  3. Gives users immediate visual feedback on Overview while guiding deep investigative work to the dedicated `/topology` space.

---

## 5. Implementation Roadmap for Subsequent Agent

1. **Step 1: Create `frontend/src/pages/TopologyPage.jsx`**
   - Implement `TopologyPage` with sub-navbar segmented buttons (`constellation`, `geomap`, `dual`).
   - Wire `AppStateContext` (`cases`, `openCase`, `busy`, `runSimulation`).
   - Style with full-height container (`h-[calc(100vh-13rem)] min-h-[700px]`).
2. **Step 2: Update `frontend/src/App.jsx`**
   - Import `TopologyPage` and mount route `<Route path="/topology" element={<TopologyPage />} />`.
3. **Step 3: Update `frontend/src/components/common/Navbar.jsx`**
   - Add `{ to: "/topology", label: "Topology Mesh", ... }` to `NAV_ITEMS`.
4. **Step 4: Refine `frontend/src/pages/OverviewPage.jsx`**
   - Add the dedicated space launch button linking to `/topology`.
   - Ensure `KpiStrip` remains before `NetworkConstellation`.
5. **Step 5: Run Verification Pipeline**
   - `./.venv/bin/pytest tests/ -v`
   - `./.venv/bin/ruff check app tests`
   - `cd frontend && npm run lint && npm run build`
