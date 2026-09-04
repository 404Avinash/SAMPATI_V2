# Handoff Report — Explorer 15.2: Topology Navigation & Space Separation (R2)

## 1. Observation

1. **Current Placement in `OverviewPage.jsx`**:
   - In `frontend/src/pages/OverviewPage.jsx`, lines 97–147 contain the monolithic "Mule-Network Interactive Fabric" panel:
     ```jsx
     {/* Line 98 */}
     <div className="panel overflow-hidden">
       <div className="panel-header flex items-center justify-between">
         ...
         <button onClick={() => setTopologyTab("constellation")}>☍ Constellation Graph</button>
         <button onClick={() => setTopologyTab("geomap")}>🗺️ India Mule Corridors</button>
       ...
       {/* Line 140 */}
       <div className="h-[440px] p-2 bg-[#f8f9fc]">
         {topologyTab === "constellation" ? (
           <NetworkConstellation cases={cases} onSelectCase={openCase} />
         ) : (
           <GeoMuleMap cases={cases} onSelectCase={openCase} />
         )}
       </div>
     </div>
     ```
   - Both visualizers are locked into `h-[440px]`, creating cramped viewing conditions for multi-hop graph networks and the `0 0 600 680` India SVG map.

2. **Routing & Top Navbar Structure**:
   - `frontend/src/App.jsx` (lines 20–37) defines routes wrapped in `MainLayout`: `/overview`, `/threat-intel`, `/investigations`, `/investigations/:caseId`, `/analytics`, `/health`, `/settings`.
   - `frontend/src/components/common/Navbar.jsx` (lines 6–65) defines 6 `NAV_ITEMS`: Overview, Threat Intelligence, Investigations, Analytics, System Health, Settings.

3. **Existing AST and Layout Test Assertions**:
   - `tests/test_tier1_features.py` lines 717–729:
     ```python
     async def test_f15_01_app_layout_order(self):
         """F15.1: Verify App.jsx component layout order (Masthead -> KpiStrip -> Visuals)."""
         overview_path = os.path.join(ROOT, "frontend", "src", "pages", "OverviewPage.jsx")
         app_path = os.path.join(ROOT, "frontend", "src", "App.jsx")
         p = overview_path if os.path.exists(overview_path) else app_path
         with open(p, "r", encoding="utf-8") as f:
             content = f.read()
         kpi_idx = content.find("KpiStrip")
         constellation_idx = content.find("NetworkConstellation")
         self.assertNotEqual(kpi_idx, -1)
         self.assertNotEqual(constellation_idx, -1)
         self.assertLess(kpi_idx, constellation_idx)
     ```
     **Critical Finding**: If `NetworkConstellation` is completely removed from `OverviewPage.jsx`, this test fails with `assert -1 != -1`.
   - `tests/frontend_contracts_test.py` lines 181–202 (`test_five_dedicated_pages_exist_in_pages_directory`) verifies that `OverviewPage.jsx`, `InvestigationsPage.jsx`, `AnalyticsPage.jsx`, `SystemHealthPage.jsx`, and `SettingsPage.jsx` exist in `frontend/src/pages/`. Adding a 6th page `TopologyPage.jsx` does not violate this invariant.
   - `tests/frontend_contracts_test.py` lines 203–213 (`test_routes_coverage_in_app_jsx`) checks that routes `/overview`, `/investigations`, `/analytics`, `/health`, `/settings` are present in `App.jsx`. Adding `/topology` does not remove any existing routes.
   - `tests/frontend_contracts_test.py` lines 223–236 (`test_navbar_navigation_state`) verifies that `Navbar.jsx` contains `NavLink`, `Overview`, `Investigations`, `Analytics`, `System Health` or `Health`, and `Settings`. Adding `Topology` preserves all of them.

4. **Test Suite Baseline Verification**:
   - `./.venv/bin/pytest tests/`: **969 passed, 0 failures** in 127.20s.
   - `./.venv/bin/ruff check app tests`: **All checks passed!**
   - `cd frontend && npm run lint`: **0 errors, 0 warnings** (`--max-warnings 0`).
   - `cd frontend && npm run build`: **✓ built in 10.19s** cleanly.

---

## 2. Logic Chain

1. **Step 1 (Problem Identification)**:
   From Observation 1, both `NetworkConstellation` and `GeoMuleMap` are constrained to `440px` on `OverviewPage.jsx`, competing with `KpiStrip`, `VerdictHistoryChart`, `ControlBar`, `LiveFeed`, and `VerdictDonut`. This produces an unwieldy 2000px+ vertical scroll on Overview and squashes the visualizers.
2. **Step 2 (Architectural Separation)**:
   Extracting the visualizers into a dedicated top-level page (`frontend/src/pages/TopologyPage.jsx`) at `/topology` with a link in `Navbar.jsx` provides full viewport real estate (`h-[calc(100vh-12rem)] min-h-[700px]`), allowing the physics graph and India SVG map to render at more than double the vertical space without edge clipping.
3. **Step 3 (Sub-Navbar Design in Dedicated Space)**:
   Within `TopologyPage.jsx`, an interactive sub-navbar provides 3 dedicated view modes:
   - `☍ Constellation Force Graph`
   - `🗺️ India Mule Corridors`
   - `⛶ Dual Perspective` (side-by-side on wide displays)
   along with telemetry badges (`Active Rings`, `Monitored Hubs`, `Intercepted Volume`) and actions (Fullscreen, Simulate).
4. **Step 4 (Preserving Overview Layout Contract)**:
   From Observation 3 (`test_f15_01_app_layout_order`), `OverviewPage.jsx` must contain both `KpiStrip` and `NetworkConstellation`, and `KpiStrip` must precede `NetworkConstellation`. Therefore, `OverviewPage.jsx` must not completely drop `NetworkConstellation`. Instead, Overview will render an executive "Topology Mesh Snapshot" featuring an active rings telemetry badge, a compact preview of `NetworkConstellation` (height 280px), and an explicit call-to-action button linking directly to `/topology`.
5. **Step 5 (Regression Immunity)**:
   From Observation 3 & 4, adding `TopologyPage.jsx` to `frontend/src/pages/`, adding `/topology` to `App.jsx`, adding the nav item to `Navbar.jsx`, and retaining `NetworkConstellation` after `KpiStrip` in `OverviewPage.jsx` guarantees that all 969 pytest tests, Ruff linting, ESLint (`--max-warnings 0`), and the Vite build pass without a single regression.

---

## 3. Caveats

1. **Leaflet / Third-Party Map Library Dependency**: If `GeoMuleMap` is upgraded to use Leaflet (`react-leaflet`) in R1, ensure CSS assets (`leaflet/dist/leaflet.css`) are imported at the page or app root without triggering ESLint unused variable warnings.
2. **Dual Perspective Screen Width**: In `TopologyPage.jsx`, the "Dual Perspective" side-by-side mode should be responsive: on screens below `1024px` (tablets/mobile), it should stack vertically or default to the single selected tab.
3. **Mock Data Synchronization**: Both visualizers consume `cases` from `AppStateContext`. Ensure `AppStateContext.cases` remains the single source of truth so actions in `TopologyPage` immediately reflect across `CaseDrawer`.

---

## 4. Conclusion

The separation of the Topology Visualizers into a dedicated space is clean, low-risk, and structurally sound:
1. **Create `frontend/src/pages/TopologyPage.jsx`** equipped with an internal 3-way sub-navbar (`Constellation Graph`, `India Mule Corridors`, `Dual Perspective`) and full viewport height (`min-h-[700px]`).
2. **Register `/topology` route in `App.jsx`** and add `"Topology Mesh"` to `NAV_ITEMS` in `frontend/src/components/common/Navbar.jsx`.
3. **Refactor `OverviewPage.jsx`** to replace the heavy 440px tabbed box with a streamlined **"Topology Intelligence Snapshot"** card linking to `/topology`, while embedding a compact preview of `NetworkConstellation` to satisfy `test_f15_01_app_layout_order`.
4. All existing contracts in `tests/frontend_contracts_test.py` and `tests/test_tier1_features.py` are strictly maintained.

---

## 5. Verification Method

To independently verify this proposal and any subsequent implementation:

1. **Run Full Pytest Test Suite**:
   ```bash
   ./.venv/bin/pytest tests/ -v
   ```
   *Expected*: All 969 tests pass with 0 failures. Pay special attention to `tests/frontend_contracts_test.py` and `tests/test_tier1_features.py::TestTier1Features::test_f15_01_app_layout_order`.

2. **Run Python Linter**:
   ```bash
   ./.venv/bin/ruff check app tests
   ```
   *Expected*: All checks pass (0 errors).

3. **Run Frontend Linter**:
   ```bash
   cd frontend && npm run lint
   ```
   *Expected*: Exits with code 0 and 0 warnings under `--max-warnings 0`.

4. **Run Frontend Vite Production Build**:
   ```bash
   cd frontend && npm run build
   ```
   *Expected*: Build completes successfully with 0 errors.

5. **AST Contract Verification Command**:
   ```bash
   ./.venv/bin/pytest tests/test_tier1_features.py -k "test_f15_01_app_layout_order" -v
   ./.venv/bin/pytest tests/frontend_contracts_test.py -v
   ```
   *Expected*: Both test modules pass unconditionally.
