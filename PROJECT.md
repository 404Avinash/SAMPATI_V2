# Project: SAMPATI V2 — Hackathon Demo UI Redesign & Intelligence Polish

## Architecture
SAMPATI V2 is a Collaborative Fraud-Intelligence Mesh for real-time UPI mule-network interception.
- **Backend**: FastAPI (Python 3.14) with a 4-layer risk evaluation pipeline (`app/engine/`), Early Warning threat intelligence ingestion (`/intel`), simulated institutional adapters (NPCI MuleHunter, DPIP, PSP), and WebSocket streaming.
- **Frontend**: React 18 / Vite / Tailwind CSS / Framer Motion:
  * Executive Overview Dashboard with live KPI counters, ambient Verdict Velocity chart, and Topology Mesh Snapshot.
  * Dedicated Topology Visualizers Space (`/topology`) featuring a 3-way sub-navbar (`Constellation Force Graph`, `India Mule Corridors`, and `Dual Perspective`).
  * High-Fidelity Geographic India Mule Corridors Map (`GeoMuleMap.jsx`) with 139-vertex authentic boundary path, geodetically calibrated hubs, glowing bezier arcs, and Jamtara/Mewat radar hotspots.
  * Uniform White Threat Intelligence Dashboard (`/threat-intel`) with executive typography, clean 3-stage entity extraction pipeline, and dynamic campaign clustering.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | High-Fidelity India Vector Cartography | Replace crude 20-point blob in `GeoMuleMap.jsx` with authentic 139-vertex geographic path (Kashmir, Gujarat peninsulas, Malabar/Konkan, Kanyakumari, Northeast) | M1 | Survey 15.1 / R1 |
| 2 | Geodetic Hub & Arc Recalibration | Align `INDIAN_HUBS` coordinates to true lat/long from backend `CITY_COORDINATES`; recalibrate glowing bezier arcs and `<animateMotion>` particles | M1 | Survey 15.1 / R1 |
| 3 | Dedicated Topology Visualizers Page | Create `TopologyPage.jsx` at `/topology` with dedicated sub-navbar (Constellation Graph, India Mule Corridors, Dual Perspective) and full viewport real estate | M2 | Survey 15.2 / R2 |
| 4 | Navigation & Overview Integration | Add `Topology Mesh` to `Navbar.jsx`, register `/topology` in `App.jsx`, and streamline Overview with a Topology Snapshot linking to `/topology` (satisfying `test_f15_01_app_layout_order`) | M2 | Survey 15.2 / R2 |
| 5 | Organic Ambient Traffic Generation | Implement harmonic ambient traffic simulation (2–5 TPS background ALLOW traffic) in `AppStateContext.jsx` so the chart always breathes and never flatlines at 0 | M3 | Survey 15.3 / R3 |
| 6 | Verdict Velocity Chart Smooth Scaling | Anchor Y-axis domain floor to 8 in `VerdictHistoryChart.jsx` and tune animations for seamless real-time velocity curve rendering | M3 | Survey 15.3 / R3 |
| 7 | Threat Intel Uniform White Theme | Replace undefined `.card` containers and dark/slate blocks with uniform clean white panels (`bg-white border border-hairline rounded-xl shadow-xs`) | M4 | Survey 15.3 / R4 |
| 8 | Threat Intel Typography & Slop Purge | Clean up typography, remove emoji spam, refine 3-stage entity extraction cards, and fix null-check bug at line 1080 | M4 | Survey 15.3 / R4 |
| 9 | Full Regression & Quality Gates | 969 pytest tests pass with 0 failures, ESLint 0 warnings (`--max-warnings 0`), Vite build succeeds cleanly | Final | Quality Gates |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Geographic India Map Redesign | Authentic 139-vertex vector map, geodetic calibration, glowing arcs, city labels in `GeoMuleMap.jsx` | none | IN_PROGRESS |
| M2 | Dedicated Topology Space & Sub-Navbar | `TopologyPage.jsx`, `/topology` route in `App.jsx`, `Navbar.jsx`, and Overview snapshot | none | PLANNED |
| M3 | Ambient Verdict Velocity Chart | 2–5 TPS ambient ALLOW traffic in `AppStateContext.jsx` and Y-axis scaling in `VerdictHistoryChart.jsx` | none | PLANNED |
| M4 | Threat Intel Uniform White Redesign | Uniform white panels, executive typography, entity extraction polish, null-check fix in `ThreatIntelPage.jsx` | none | PLANNED |
| Final | Regression & Quality Verification | Full pytest suite (969 tests), ESLint (`--max-warnings 0`), Vite production build, visual checks | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### `GeoMuleMap.jsx` Props Contract
- `GeoMuleMap({ cases, onSelectCase })`:
  * `cases`: Array of case objects (from `AppStateContext.cases`).
  * `onSelectCase(caseId)`: Callback when clicking a corridor or case hotspot.

### `/topology` Route & Navigation Contract
- Route path: `/topology` in `App.jsx` rendered inside `MainLayout`.
- `Navbar.jsx`: Item `{ name: "Topology Mesh", path: "/topology", icon: Share2 }`.
- `OverviewPage.jsx`: Must maintain `KpiStrip` followed by `NetworkConstellation` component (to preserve `tests/test_tier1_features.py::test_f15_01_app_layout_order`).

### Ambient Traffic Contract
- `verdictHistory`: Array of 30 buckets with timestamps.
- Ambient traffic: 2–5 TPS of `ALLOW` verdicts injected every 1000ms. Does not inflate `stats.evaluated` or generate false `HOLD`/`BLOCK` counts.

## Code Layout
- `frontend/src/components/overview/GeoMuleMap.jsx`: High-fidelity geographic India map (Owned by M1).
- `frontend/src/pages/TopologyPage.jsx`: Dedicated topology page with sub-navbar (Owned by M2).
- `frontend/src/components/common/Navbar.jsx`: Navigation links (Owned by M2).
- `frontend/src/App.jsx`: Route definitions (Owned by M2).
- `frontend/src/pages/OverviewPage.jsx`: Overview layout and snapshot (Owned by M2).
- `frontend/src/context/AppStateContext.jsx`: State provider and ambient traffic generator (Owned by M3).
- `frontend/src/components/VerdictHistoryChart.jsx`: Velocity chart rendering and Y-axis scale (Owned by M3).
- `frontend/src/components/VerdictVelocityChart.jsx`: Velocity chart alias re-export (Owned by M3).
- `frontend/src/pages/ThreatIntelPage.jsx`: Threat Intelligence dashboard (Owned by M4).
