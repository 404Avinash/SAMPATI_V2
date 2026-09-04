# Dispatch — Worker 15.M2: Dedicated Topology Space & Sub-Navbar

Read:
- `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md`
- `/home/avi/Downloads/Sampati_v2/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_2/analysis.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_2/handoff.md`

Your working directory is: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m2`

File Write Ownership (Exclusive):
- `frontend/src/pages/TopologyPage.jsx` (New file)
- `frontend/src/App.jsx`
- `frontend/src/components/common/Navbar.jsx`
- `frontend/src/pages/OverviewPage.jsx`

Task:
Implement the Dedicated Topology Visualizers Space with Sub-Navbar:
1. Create `frontend/src/pages/TopologyPage.jsx`:
   - An executive dedicated view giving full viewport real estate (`min-h-[700px]`, `h-[calc(100vh-12rem)]`).
   - Integrated sub-navbar with 3 view modes:
     * `☍ Constellation Force Graph` (`NetworkConstellation.jsx`)
     * `🗺️ India Mule Corridors` (`GeoMuleMap.jsx`)
     * `⛶ Dual Perspective` (Side-by-side or stacked split view showing both simultaneously on wide screens)
   - Telemetry strip: Active Mule Rings, Monitored Hubs, Intercepted Volume.
   - Interactive controls: Fullscreen toggle, simulate burst shortcut.
2. Register `/topology` in `frontend/src/App.jsx` inside `MainLayout`.
3. Add `"Topology Mesh"` to `NAV_ITEMS` in `frontend/src/components/common/Navbar.jsx` (use `Share2` icon or similar from `lucide-react`).
4. Update `frontend/src/pages/OverviewPage.jsx`:
   - Replace the cramped 440px tab container with a clean "Topology Intelligence Snapshot" panel.
   - CRITICAL REQUIREMENT: `tests/test_tier1_features.py::test_f15_01_app_layout_order` asserts that `OverviewPage.jsx` contains `KpiStrip` followed by `NetworkConstellation`. You MUST keep `NetworkConstellation` mounted in `OverviewPage.jsx` (e.g. in a sleek preview container of ~280px height with a prominent "Open Fullscreen Mesh / Dedicated Topology View" button linking to `/topology`).
5. Verify:
   - `cd frontend && npm run lint` must pass with 0 warnings (`--max-warnings 0`).
   - `cd frontend && npm run build` must complete cleanly with 0 errors.
   - `./.venv/bin/pytest tests/test_tier1_features.py -k "test_f15_01_app_layout_order" -v` must PASS.
   - `./.venv/bin/pytest tests/frontend_contracts_test.py -v` must PASS.
   - Full `./.venv/bin/pytest tests/ -v` must pass 969 tests.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes, run tests, and write your completion report in `handoff.md` in your working directory. Send a message to parent when done.

## 2026-09-04T13:22:54Z
You are Worker 15.M2 for SAMPATI V2.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m2
Read DISPATCH.md in your working directory and follow all instructions.
Your exclusive file ownership: frontend/src/pages/TopologyPage.jsx (create new), frontend/src/App.jsx, frontend/src/components/common/Navbar.jsx, frontend/src/pages/OverviewPage.jsx.
Implement the dedicated /topology page with 3-way sub-navbar (Constellation Graph, India Mule Corridors, Dual Perspective). Update App.jsx and Navbar.jsx. Update OverviewPage.jsx to show Topology Snapshot while keeping NetworkConstellation mounted to preserve test_f15_01_app_layout_order.
MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
Run verification: cd frontend && npm run lint && npm run build, and pytest tests/test_tier1_features.py -k "test_f15_01_app_layout_order" -v, pytest tests/frontend_contracts_test.py -v, and full pytest tests/ -v.
Write your handoff report to handoff.md and send a completion message to parent.
