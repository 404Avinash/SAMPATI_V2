# Project: SAMPATI V2 Sprint 3

## Architecture
- Backend: FastAPI (`app/`), UpiCaseService (`app/services/upi_cases.py`), Routes (`app/api/`), Static mounts (`static/upi_cases/`).
- Frontend: React + Vite (`frontend/src/`), Components (`NetworkConstellation.jsx`, `CaseDrawer.jsx`, `ForensicImageViewer.jsx`, `KpiStrip.jsx`, `LiveFeed.jsx`, `ControlBar.jsx`), Pages (`InvestigationsPage.jsx`, `AnalyticsPage.jsx`, `OverviewPage.jsx`).
- Testing: Pytest (`tests/`), ESLint + Vite build.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Static File Mount & Artifact Dir | Mount `/static` before SPA fallback, ensure `artifact_dir` exists | M1 | Sprint 3 R1 |
| 2 | ForensicImageViewer Fallback URL | Fallback to `/static/upi_cases/{case_id}_ring.png` if endpoint 404s | M1 | Sprint 3 R1 |
| 3 | Requirements.txt Verification | Verify reportlab and all dependencies listed | M1 | Sprint 3 R1 |
| 4 | Demo Seed Data Generation | Non-blocking auto-seed (~150 txns, fraud_ratio=0.25) on startup or first stats call | M1 | Sprint 3 R2 |
| 5 | Cinematic Spring-Force Physics | Continuous spring-force simulation with drift/settle | M2 | Sprint 3 R3 |
| 6 | Pulsing Node Glows | Pulsing red glow for BLOCK, amber for HOLD | M2 | Sprint 3 R3 |
| 7 | Animated Edge Risk Gradient & Flow | Risk-colored edges (teal/amber/crimson) with animated particle dots | M2 | Sprint 3 R3 |
| 8 | Constellation Zoom, Pan & Auto-play | Zoom/pan interaction and auto-play timeline on load | M2 | Sprint 3 R3 |
| 9 | Constellation Node Click Drawer | Clicking node opens CaseDrawer | M2 | Sprint 3 R3 |
| 10 | Clickable Case Table Rows & Status Filter | Clickable table rows to open drawer, instant status badge filtering | M3 | Sprint 3 R4 |
| 11 | Animated DMV Gauge | Animated arc/dial gauge in CaseDrawer | M3 | Sprint 3 R4 |
| 12 | Horizontal Bar Chart Rule Breakdown | Sorted horizontal bar chart with Recharts in CaseDrawer | M3 | Sprint 3 R4 |
| 13 | Fallback SVG Ring Topology | In-browser SVG ring topology when PNG fails (404) | M3 | Sprint 3 R4 |
| 14 | Real PDF SAR Export Download | Trigger real PDF binary download with error toast | M3 | Sprint 3 R4 |
| 15 | Recharts Animation & Polish | `animationDuration={800}` & `isAnimationActive={true}` on all charts | M4 | Sprint 3 R5 |
| 16 | 7x24 CSS Grid Heatmap | Heatmap with hover tooltips + skeleton loading state | M4 | Sprint 3 R5 |
| 17 | Top VPAs Table Progress Bars & Sorting | Top VPAs table with inline progress bars and sortable headers | M4 | Sprint 3 R5 |
| 18 | Active Campaigns Metric Card | Metric card showing count of unique fingerprinted fraud campaigns | M4 | Sprint 3 R5 |
| 19 | KPI Count-up Animations | Count-up animations (0 -> value) and smooth updates | M4 | Sprint 3 R6 |
| 20 | Live Feed Smooth Slide-in / Fade-out | CSS transitions for new events and expiring events | M4 | Sprint 3 R6 |
| 21 | Auto-Feed Toggle Pulsing & TPS Counter | Pulsing dot indicator and live TPS counter next to toggle | M4 | Sprint 3 R6 |
| 22 | Honeypot Alert Toast | Red toast notification for honeypot hits (5s) | M4 | Sprint 3 R6 |
| 23 | E2E Testing, Linting & Safe-Push | 648+ Pytest passing, 0 ESLint warnings, Vite build, SSH git push | M5 | Sprint 3 R7 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Backend Deployment & Seed Data | Features 1, 2, 3, 4 (R1, R2) | none | DONE |
| 2 | Cinematic NetworkConstellation | Features 5, 6, 7, 8, 9 (R3) | M1 | DONE |
| 3 | Interactive Investigations & CaseDrawer | Features 10, 11, 12, 13, 14 (R4) | M1 | DONE |
| 4 | Analytics & Overview Polish | Features 15, 16, 17, 18, 19, 20, 21, 22 (R5, R6) | M1 | DONE |
| 5 | E2E Verification & Safe-Push | Feature 23 (R7) | M1, M2, M3, M4 | IN_PROGRESS |

## Code Layout
- Backend files:
  - `app/main.py`
  - `app/services/upi_cases.py`
  - `app/api/upi.py`
  - `requirements.txt`
- Frontend files:
  - `frontend/src/components/NetworkConstellation.jsx`
  - `frontend/src/components/CaseDrawer.jsx`
  - `frontend/src/components/investigations/ForensicImageViewer.jsx`
  - `frontend/src/components/investigations/CaseFilterBar.jsx`
  - `frontend/src/components/analytics/TimeSeriesVerdictChart.jsx`
  - `frontend/src/components/analytics/FraudRateTrendChart.jsx`
  - `frontend/src/components/analytics/BankDistributionChart.jsx`
  - `frontend/src/components/VerdictHistoryChart.jsx`
  - `frontend/src/components/VerdictDonut.jsx`
  - `frontend/src/components/analytics/AnalystWorkloadHeatmap.jsx`
  - `frontend/src/components/analytics/TopDmvAccountsTable.jsx`
  - `frontend/src/components/analytics/AnalyticsSummaryKpis.jsx`
  - `frontend/src/pages/AnalyticsPage.jsx`
  - `frontend/src/pages/InvestigationsPage.jsx`
  - `frontend/src/pages/OverviewPage.jsx`
  - `frontend/src/hooks/useCountUp.js`
  - `frontend/src/components/LiveFeed.jsx`
  - `frontend/src/components/ControlBar.jsx`
  - `frontend/src/hooks/useWebSocket.js`
  - `frontend/src/context/AppStateContext.jsx`
  - `frontend/src/services/api.js`
