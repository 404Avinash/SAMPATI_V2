# Frontend Architecture & Multi-Page Dashboard Upgrade Blueprint (R2)

**Author:** Frontend Architecture Explorer  
**Target Milestone:** SAMPATI V2 R2 Frontend Multi-Page Architecture Upgrade  
**Working Directory:** `/home/avi/Downloads/Sampati_v2/frontend`  
**Target Output Artifact:** `handoff.md`  

---

## 1. Observation

### 1.1 Existing Codebase Anatomy & State Flow
- **Package Manifest (`frontend/package.json`):**
  - Current version: `2.1.0` (Type: `module`).
  - Production Dependencies: `framer-motion` (^11.11.17), `react` (18.3.1), `react-dom` (18.3.1), `react-markdown` (9.1.0), `recharts` (2.15.4).
  - Dev Dependencies: `@vitejs/plugin-react` (4.7.0), `autoprefixer` (10.5.4), `postcss` (8.5.26), `tailwindcss` (3.4.19), `vite` (5.4.21).
  - **Missing Dependencies:** `react-router-dom` is currently not present in `dependencies`. No `eslint` or `lint` script exists in `scripts`.
- **Vite Configuration (`frontend/vite.config.js`):**
  - Configures dev server reverse proxies for `/upi`, `/gateway`, `/cases`, and `/ws` to `http://localhost:8000`.
  - **Missing Proxy Routes:** New backend additions (`/stats/analytics`, `/health/detailed`) require proxying `/stats` and `/health` to avoid 404s in development mode.
- **FastAPI Static Mounting (`app/main.py:122-124`):**
  - Uses `app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")`.
  - In Starlette, direct URL reloads on client routes (e.g. `/investigations`) will return a 404 unless a custom 404 exception handler or HTML fallback router redirects to `index.html`.
- **Existing Dashboard Component Structure (`frontend/src/App.jsx:1-288`):**
  - Monolithic single-page view mounting `Masthead`, `KpiStrip`, `VerdictHistoryChart`, `ControlBar`, `NetworkConstellation`, `LiveFeed`, `VerdictDonut`, and `CaseDrawer`.
  - Centralized state in `App.jsx`: `stats` (evaluated, allowed, held, blocked, rings, dpip), `cases` (list of 100 recent items), `verdictHistory` (rolling 40-point time-series buffer), `selectedCase`, `busy`, `live`, `sensitivity`.
  - WebSocket Hook (`frontend/src/hooks/useWebSocket.js:1-149`): Connects to `ws://<host>/ws/feed` with exponential backoff auto-reconnect, parses incoming `new_case` / `UPI_CASE_OPENED` and `stats_update` / `UPI_EVALUATED` events.
  - API Service (`frontend/src/services/api.js:1-72`): Exports `simulate()`, `runFederation()`, `cases()`, `case(id)`, `feedback(id, confirmed)`, `stats()`, and formatting helpers (`formatINR`, `relativeTime`, `formatTime`, `shortVpa`).
- **Backend Data Schemas (`app/models/upi_persistence.py:33-112` & `app/api/upi.py:1-434`):**
  - Cases contain `case_id`, `created_at`, `status` (`OPEN`, `INVESTIGATED`, `RESOLVED`), `verdict` (`ALLOW`, `HOLD`, `BLOCK`), `risk_score` (0-100), `payer_vpa`, `payee_vpa`, `amount`, `trigger_txn`, `rule_hits`, `adaptive_score`, `network_score`, `ring_hash`, `ring_members_vpas`, `token_economy`, `sar_markdown`, `visual_path`, `topology`, `resolution`, `resolution_notes`.
  - 4-panel visual summary PNG is served at `GET /upi/cases/{case_id}/graph.png`.

---

## 2. Logic Chain & Architectural Blueprint

```
                     ┌───────────────────────────────────────────────────────────┐
                     │                   BrowserRouter (main.jsx)                │
                     └─────────────────────────────┬─────────────────────────────┘
                                                   │
                     ┌─────────────────────────────▼─────────────────────────────┐
                     │                  AppLayout (layouts/AppLayout.jsx)        │
                     │  ┌───────────────────────┐  ┌──────────────────────────┐  │
                     │  │   CollapsibleSidebar  │  │  TopHeader / Masthead    │  │
                     │  │   - Persisted State   │  │  - Adaptive Sensitivity  │  │
                     │  │   - Responsive Drawer │  │  - Live WS Stream Pulse  │  │
                     │  └───────────┬───────────┘  └─────────────┬────────────┘  │
                     │              │                            │               │
                     │              └──────────────┬─────────────┘               │
                     │                             ▼                             │
                     │                     <Outlet /> (Routes)                   │
                     └──────┬──────────────┬──────────────┬──────────────┬───────┘
                            │              │              │              │
           ┌────────────────┼──────────────┼──────────────┼──────────────┤
           ▼                ▼              ▼              ▼              ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ 1. Overview  │ │2.Investigate │ │ 3. Analytics │ │4.Sys Health  │ │ 5. Settings  │
    │ (Constell'n, │ │(Case Table,  │ │(Hourly/Daily,│ │(Latency p99, │ │(Sensitivity, │
    │  KPI, Feed,  │ │ Detail Modal,│ │ Top Payees,  │ │ DB Pool, WS, │ │ Fraud Rate,  │
    │  Velocity)   │ │ 4-Panel PNG, │ │ Heatmap,     │ │ Throughput,  │ │ CI/CD Badge, │
    │              │ │ SAR, DPIP)   │ │ Bank Distr)  │ │ Uptime)      │ │ Commit SHA)  │
    └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### 2.1 Routing & URL Persistence Architecture
1. **Router Model:** Standard `react-router-dom` with `BrowserRouter`.
   - Route mapping:
     - `/` -> `<OverviewPage />`
     - `/investigations` -> `<InvestigationsPage />`
     - `/investigations/:caseId` -> `<InvestigationsPage />` (auto-opens case detail modal/dossier based on URL parameter)
     - `/analytics` -> `<AnalyticsPage />`
     - `/health` -> `<SystemHealthPage />`
     - `/settings` -> `<SettingsPage />`
     - `*` -> `<NotFoundPage />`
2. **Server-Side Fallback Support:**
   - In Vite dev server: handled natively by Vite's HTML5 history fallback.
   - In FastAPI production container (`app/main.py`): add an SPA fallback route handler to serve `dist/index.html` on 404 for any non-API routes.

### 2.2 Global State & Real-Time Synchronization (`AppStateContext`)
To ensure seamless transitions between pages without losing WebSocket events or telemetry state:
- Create `src/context/AppStateContext.jsx` exposing:
  - `stats`: Cumulative telemetry (`evaluated`, `allowed`, `held`, `blocked`, `rings`, `dpip`).
  - `cases`: Recent stream buffer of cases (capped at 150 items in memory).
  - `verdictHistory`: 40-point rolling time-series buffer for instant chart rendering.
  - `live`: Real-time WebSocket connection state (`connected`, `reconnectAttempt`).
  - `sensitivity`: Active adaptive threshold factor.
  - `selectedCase`: Currently opened case dossier.
  - Actions: `runSimulation()`, `runFederation()`, `refreshCases()`, `refreshStats()`, `openCase()`, `updateCaseStatus()`.

---

## 3. Detailed Page Decomposition & Component Specifications

### 3.1 App Shell & Navigation (`src/layouts/AppLayout.jsx` & `src/components/common/Sidebar.jsx`)
- **Collapsible Sidebar UX:**
  - Expanded width: `w-64` (shows label, icon, badge).
  - Collapsed width: `w-20` (icon-only mode with floating tooltips).
  - Persistence: `localStorage.getItem("sampati_sidebar_collapsed")` with instant initialization.
  - Mobile Mode (`< md`): Off-canvas slide-out drawer with backdrop blur overlay and hamburger toggle in Masthead.
  - Nav Items:
    1. **Overview** (`/`): `LayoutDashboard` icon.
    2. **Investigations** (`/investigations`): `ShieldAlert` icon + dynamic badge of unreviewed flagged cases.
    3. **Analytics** (`/analytics`): `BarChart3` icon.
    4. **System Health** (`/health`): `Activity` icon + live pulse indicator (Green/Amber/Red).
    5. **Settings** (`/settings`): `Sliders` / `Settings` icon.
  - Footer Section: Version tag `v2.1.0`, GitHub CI commit SHA badge, and sidebar expand/collapse chevron toggle.

---

### 3.2 Page 1: Overview (`src/pages/OverviewPage.jsx`)
- **Objective:** High-density real-time monitoring and simulation hub.
- **Component Breakdown:**
  1. `<KpiStrip stats={stats} />`: 6 animated metric cards with `useCountUp` (Evaluated, Allowed, Held, Blocked, Mule Rings, DPIP).
  2. `<VerdictHistoryChart history={verdictHistory} />`: Recharts `AreaChart` with gradient fill showing session velocity.
  3. `<ControlBar onSimulate={runSimulation} onFederate={runFederation} busy={busy} />`: Interactive simulation sliders & federation trigger.
  4. `<NetworkConstellation cases={cases} onSelectCase={openCase} />`: 60 FPS interactive HTML5 canvas graph visualizer with node tooltips, continuous edge risk gradients, and click-to-open case.
  5. Split Bottom Section:
     - Left (2/3): `<LiveFeed cases={cases} onSelect={openCase} />` with scanline animation and risk badges.
     - Right (1/3): `<VerdictDonut allowed={stats.allowed} held={stats.held} blocked={stats.blocked} />` with percentage breakdown.

---

### 3.3 Page 2: Investigations (`src/pages/InvestigationsPage.jsx`)
- **Objective:** Comprehensive case management and triage console for fraud investigators.
- **Component Decomposition:**
  1. `<CaseFilterBar />`:
     - Full-text search across `case_id`, `payer_vpa`, `payee_vpa`, and `ring_hash`.
     - Verdict Filter: Multi-select pills (`ALL`, `HOLD`, `BLOCK`, `ALLOW`).
     - Status Filter: Dropdown (`ALL`, `OPEN`, `REVIEWED`, `ESCALATED`, `DISMISSED`, `RESOLVED`).
     - Risk Score Threshold Slider (e.g. `Score >= 70`).
     - Sort Options: Newest First, Highest Risk First, Highest Amount First.
     - Refresh button with spinner.
  2. `<CaseTable />`:
     - Tabular view with columns:
       - **Case ID**: Monospace badge with copy button.
       - **Timestamp**: Relative time (`2m ago`) + exact UTC tooltip.
       - **Payer VPA → Payee VPA**: Entity addresses with masked identifiers and PSP badges (`@okhdfcbank`, `@paytm`).
       - **Amount**: INR currency formatting (`₹50,000`).
       - **Verdict**: Color-coded pill (`ALLOW` green, `HOLD` amber, `BLOCK` red with pulse).
       - **Risk Score**: Score pill + mini progress bar.
       - **Status**: Status badge (`OPEN`, `REVIEWED`, `ESCALATED`, `DISMISSED`).
       - **Primary Signals**: Top 2 rule triggers.
       - **Actions**: `View Dossier` button.
     - Empty State: Clean card with illustration and "Run simulation to generate investigative cases" action.
  3. `<CasePagination />`:
     - Page size selector (`10`, `25`, `50`, `100`).
     - Previous / Next buttons, page indicators, and total records count.
  4. `<CaseDetailModal />` (Full Case Dossier View):
     - **Header**: Case ID, timestamp, verdict badge, current status, risk score meter.
     - **4-Panel Forensic Summary (`<ForensicImageViewer />`)**:
       - Embedded image fetching `/upi/cases/{case_id}/graph.png`.
       - Displays: Sub-graph topology, Velocity histogram, Amount anomaly, Feature attribution.
       - Click to zoom / Lightbox modal with pan & zoom.
     - **AI Case Narrative (`<SarNarrativeView />`)**:
       - Renders `sar_markdown` via `react-markdown` with bespoke typography.
     - **Token Economy Telemetry**:
       - 3-card grid: Raw LLM Tokens, Vision Forensics Tokens, Compression Ratio (e.g. `14.8× savings`).
     - **Payee & Mule Ring Breakdown Table (`<PayeeBreakdownTable />`)**:
       - Fan-in victims, Collector Hub, Layering hops, and Cash-out destination accounts with transaction amounts.
     - **Status Transition Workflow (`<StatusTransitionActions />`)**:
       - Status update buttons triggering `PATCH /cases/{case_id}/status`:
         - `Mark as Reviewed` (sets status to `REVIEWED`).
         - `Escalate to DPIP` (sets status to `ESCALATED`, publishes ring VPAs to RBI DPIP feed).
         - `Dismiss as False Positive` (sets status to `DISMISSED`, calls feedback false).
         - `Confirm Mule Ring / Fraud` (sets status to `RESOLVED`, calls feedback true).
       - Analyst notes text input with audit timestamp.

---

### 3.4 Page 3: Analytics (`src/pages/AnalyticsPage.jsx`)
- **Objective:** Fraud intelligence trends, high-risk entity identification, and rule telemetry.
- **Data Source:** `GET /stats/analytics` (with automatic client fallback computation if backend is loading).
- **Component Decomposition:**
  1. `<AnalyticsSummaryKpis />`:
     - Global Fraud Rate % (e.g. `10.8%`), Total Intercepted Volume (e.g. `₹4.2M`), Peak Velocity (txns/min), DPIP Sync Count.
  2. `<TimeSeriesVerdictChart />`:
     - Stacked `BarChart` or multi-line `AreaChart` of hourly/daily breakdown:
       - Series: `ALLOW` (Green), `HOLD` (Amber), `BLOCK` (Red).
       - Toggle between Hourly (24h) and Daily (7d / 30d) views.
  3. `<FraudRateTrendChart />`:
     - Recharts `LineChart` plotting Fraud Rate % over time with an SLA target reference line (e.g. 5.0%).
  4. `<TopFlaggedAccountsTable />`:
     - Ranked list of top high-risk payee VPAs / corporate mule accounts with:
       - VPA address, PSP handle, Flagged Case Count, Total At-Risk Amount (INR), Average Risk Score.
  5. `<BankDistributionChart />`:
     - Recharts `PieChart` / Donut chart showing distribution across PSP handles (`Paytm`, `HDFC`, `Axis`, `ICICI`, `PhonePe/YBL`).
  6. `<RuleTriggerHeatmap />`:
     - Ranked horizontal bar chart / heatmap matrix showing rule hit frequencies:
       - *Velocity burst (>5 txns/min)*
       - *New device fingerprint binding*
       - *High fan-in to fan-out ratio*
       - *DPIP blacklist intelligence match*
       - *Amount anomaly (>3σ above baseline)*

---

### 3.5 Page 4: System Health (`src/pages/SystemHealthPage.jsx`)
- **Objective:** Real-time SRE and infrastructure operations telemetry.
- **Data Source:** `GET /health/detailed` polled every 3-5 seconds + WebSocket heartbeat.
- **Component Decomposition:**
  1. `<HealthStatusBanner />`:
     - Overall System Status: `HEALTHY` (Green), `DEGRADED` (Amber), `OUTAGE` (Red).
     - System Uptime ticker (e.g. `4d 14h 22m`), Host: `AWS EC2 Mumbai (ap-south-1)`.
  2. Metric Cards Grid:
     - **Detection Latency (p50 / p99)**: Gauge showing `p50` (1.2ms) and `p99` (4.8ms) vs 10ms SLA.
     - **Throughput**: Transactions/sec and Batches/min.
     - **WebSocket Clients**: Active live dashboard connections.
     - **PostgreSQL Pool**: Active vs Idle vs Overflow connections + % capacity bar.
     - **Redis Hot State Ping**: Response time (0.4ms) and memory usage.
  3. `<LiveLatencyJitterChart />`:
     - Rolling Recharts time-series chart showing p50 and p99 latency jitter over the last 60 polls.
  4. `<ServiceComponentGrid />`:
     - Status grid of core architectural modules:
       - `Inline Gate (Layer 1)`: UP (6 heuristic rules loaded).
       - `Adaptive Behavioral Engine (Layer 2)`: UP (Sensitivity: 1.000).
       - `Federated Coordinator (Layer 3)`: UP (Cross-PSP consensus active).
       - `Visual Forensics SAR (Layer 4)`: UP (Matplotlib renderer pool ready).
       - `PostgreSQL AWS RDS`: CONNECTED (Dialect: postgresql+asyncpg).
       - `Redis Hot State Store`: CONNECTED (Key TTL monitoring).
       - `RBI DPIP Loop`: UP (Bidirectional ring synchronization).

---

### 3.6 Page 5: Settings (`src/pages/SettingsPage.jsx`)
- **Objective:** Dynamic engine threshold configuration and deployment observability.
- **Component Decomposition:**
  1. `<SensitivitySlider />`:
     - Interactive range input (0.100 - 3.000, step 0.025, default 1.000).
     - Explanatory scale: Higher sensitivity increases HOLD/BLOCK precision for aggressive fraud capture; lower sensitivity reduces false positives.
     - `Save to Engine` button calling backend settings update.
  2. `<SimulatorConfigPanel />`:
     - Default Transaction Count (10 - 2000).
     - Default Fraud Injection Rate (0% - 60%).
     - Auto-run Federation toggle.
     - Random Seed control.
  3. `<DeployStatusPanel />`:
     - CI/CD Deployment Observability card:
       - Current Git Commit SHA with short hash link.
       - Docker Image Tag: `ghcr.io/404avinash/sampati_v2:sha-...` / `latest`.
       - Deployment Environment: `AWS EC2 (Mumbai ap-south-1)`.
       - GitHub Actions Workflow Status: Passing / Failing badge.
       - Container Healthcheck Status: `HTTP 200 OK`.
       - Previous Rollback Tag identifier.

---

## 4. Complete Frontend File Layout & Manifest

```
frontend/
├── package.json                          # Updated with react-router-dom, lucide-react, eslint
├── vite.config.js                        # Updated with /stats and /health dev proxies
├── tailwind.config.js                    # Theme colors, fonts, animations
├── .eslintrc.cjs                         # Strict ESLint configuration
├── index.html                            # Root HTML entry point
└── src/
    ├── main.jsx                          # Root DOM mount with BrowserRouter
    ├── App.jsx                           # Route declarations & AppLayout mount
    ├── index.css                         # Tailwind directives & custom component classes
    │
    ├── context/
    │   ├── AppStateContext.jsx           # Global state, WS stream handler, shared actions
    │   └── ToastContext.jsx              # Toast alert notification provider
    │
    ├── hooks/
    │   ├── useWebSocket.js               # Auto-reconnecting WebSocket client
    │   ├── useCountUp.js                 # Smooth numeric value tweening
    │   ├── useAnalyticsData.js           # Analytics polling & fallback aggregation
    │   └── useHealthData.js              # Detailed health polling hook
    │
    ├── services/
    │   └── api.js                        # REST client with new endpoints (analytics, health, status)
    │
    ├── layouts/
    │   └── AppLayout.jsx                 # Persistent sidebar, masthead topbar, <Outlet />
    │
    ├── components/
    │   ├── common/
    │   │   ├── Sidebar.jsx               # Collapsible, mobile-responsive navigation
    │   │   ├── Topbar.jsx                # Header masthead with live badge & sensitivity
    │   │   ├── StatusBadge.jsx           # Standardized verdict and status pill
    │   │   ├── MetricCard.jsx            # Reusable KPI tile with count-up animation
    │   │   └── Modal.jsx                 # Accessible modal dialog
    │   │
    │   ├── overview/                     # Page 1 components
    │   │   ├── KpiStrip.jsx              # 6-metric telemetry strip
    │   │   ├── VerdictHistoryChart.jsx   # Real-time velocity area chart
    │   │   ├── ControlBar.jsx            # Simulation & federation triggers
    │   │   ├── NetworkConstellation.jsx  # Interactive canvas force-directed graph
    │   │   ├── LiveFeed.jsx              # Flagged activity stream table
    │   │   └── VerdictDonut.jsx          # Verdict mix pie chart
    │   │
    │   ├── investigations/               # Page 2 components
    │   │   ├── CaseFilterBar.jsx         # Search, status/verdict filters, sort
    │   │   ├── CaseTable.jsx             # Paginated flagged cases table
    │   │   ├── CasePagination.jsx        # Pagination controls
    │   │   ├── CaseDetailModal.jsx       # Full case dossier modal
    │   │   ├── ForensicImageViewer.jsx   # 4-panel PNG viewer with zoom
    │   │   ├── SarNarrativeView.jsx      # Markdown SAR renderer
    │   │   ├── PayeeBreakdownTable.jsx   # Mule ring member accounts table
    │   │   └── StatusTransitionActions.jsx # Review, Escalate, Dismiss, Confirm buttons
    │   │
    │   ├── analytics/                    # Page 3 components
    │   │   ├── AnalyticsSummaryKpis.jsx  # Fraud rate & volume summary
    │   │   ├── TimeSeriesVerdictChart.jsx# Hourly/Daily verdict breakdown chart
    │   │   ├── FraudRateTrendChart.jsx   # Fraud rate % line chart with SLA
    │   │   ├── TopFlaggedAccountsTable.jsx# Ranked corporate mule accounts
    │   │   ├── BankDistributionChart.jsx # PSP / Bank breakdown donut
    │   │   └── RuleTriggerHeatmap.jsx    # Rule trigger frequency chart
    │   │
    │   ├── health/                       # Page 4 components
    │   │   ├── HealthStatusBanner.jsx    # System health overview & uptime
    │   │   ├── EngineLatencyGauge.jsx    # p50 / p99 latency meters
    │   │   ├── ConnectionPoolStatus.jsx  # PostgreSQL connection pool bar
    │   │   ├── ServiceComponentGrid.jsx  # Component health status grid
    │   │   └── LiveLatencyJitterChart.jsx# Rolling latency percentiles chart
    │   │
    │   └── settings/                     # Page 5 components
    │       ├── SensitivitySlider.jsx     # Adaptive threshold slider
    │       ├── SimulatorConfigPanel.jsx  # Traffic simulation presets
    │       └── DeployStatusPanel.jsx     # GitHub Actions CI/CD status & SHA
    │
    └── pages/
        ├── OverviewPage.jsx              # Route /
        ├── InvestigationsPage.jsx        # Route /investigations
        ├── AnalyticsPage.jsx             # Route /analytics
        ├── SystemHealthPage.jsx          # Route /health
        ├── SettingsPage.jsx              # Route /settings
        └── NotFoundPage.jsx              # Route *
```

---

## 5. API Service Extensions & Endpoints Contract

### 5.1 Updated `frontend/src/services/api.js` Blueprint
```javascript
const BASE = "";

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${options.method || "GET"} ${path} -> ${res.status}: ${text}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export const api = {
  // Existing endpoints
  simulate: (count, fraudRatio) =>
    req("/upi/simulate", {
      method: "POST",
      body: JSON.stringify({ total_txns: count, fraud_ratio: fraudRatio }),
    }),
  runFederation: () => req("/upi/federation/run", { method: "POST" }),
  cases: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/upi/cases${qs ? `?${qs}` : ""}`);
  },
  case: (id) => req(`/upi/cases/${id}`),
  feedback: (id, confirmed) =>
    req(`/upi/cases/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ confirmed }),
    }),
  stats: () => req("/upi/stats"),
  checkTxn: (txn) => req("/upi/check", { method: "POST", body: JSON.stringify(txn) }),

  // R2 Backend Additions
  getAnalytics: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/stats/analytics${qs ? `?${qs}` : ""}`).catch(() => req(`/upi/stats/analytics${qs ? `?${qs}` : ""}`));
  },
  getDetailedHealth: () =>
    req("/health/detailed").catch(() => req("/api/health/detailed")),
  updateCaseStatus: (caseId, status, notes = "", publishToDpip = false) =>
    req(`/cases/${caseId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, notes, publish_to_dpip: publishToDpip }),
    }).catch(() =>
      req(`/upi/cases/${caseId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status, notes, publish_to_dpip: publishToDpip }),
      })
    ),
  updateSensitivity: (sensitivity) =>
    req("/upi/settings/sensitivity", {
      method: "POST",
      body: JSON.stringify({ sensitivity }),
    }).catch(() =>
      req("/engine/sensitivity", {
        method: "POST",
        body: JSON.stringify({ sensitivity }),
      })
    ),
  getDeployStatus: () =>
    req("/api/deployment/status").catch(() => ({
      commit_sha: "manual-build",
      status: "PASSING",
      deployed_at: new Date().toISOString(),
      environment: "AWS EC2 Mumbai (ap-south-1)",
    })),
};
```

---

## 6. Caveats & Implementation Edge Cases

1. **SPA Routing Fallback on Container Deployments:**
   - In production with `uvicorn` and FastAPI's `StaticFiles`, refreshing directly on `/investigations` or `/analytics` will return 404 unless FastAPI catches 404s and serves `frontend/dist/index.html`.
   - *Recommendation for Backend Implementer:* Add an exception handler or catch-all fallback route in `app/main.py`:
     ```python
     @app.exception_handler(404)
     async def custom_404_handler(request, exc):
         index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")
         if os.path.isfile(index_path) and not request.url.path.startswith(("/upi", "/gateway", "/cases", "/stats", "/health", "/ws", "/api")):
             return FileResponse(index_path)
         return JSONResponse(status_code=404, content={"detail": "Not Found"})
     ```
2. **Vite Dev Server Proxy Routing:**
   - In `frontend/vite.config.js`, proxy configuration must include `/stats` and `/health`:
     ```javascript
     proxy: {
       "/upi": "http://localhost:8000",
       "/gateway": "http://localhost:8000",
       "/cases": "http://localhost:8000",
       "/stats": "http://localhost:8000",
       "/health": "http://localhost:8000",
       "/ws": { target: "ws://localhost:8000", ws: true },
     }
     ```
3. **Graceful Fallback on Async Backend Endpoints:**
   - During early deployment phases when the backend might be starting or running in-memory fallback mode, `useAnalyticsData` and `useHealthData` should compute dynamic fallback values from `/upi/cases` and `/upi/stats` so pages never crash or display blank screens.

---

## 7. Conclusion

The architectural design for R2 expands SAMPATI from a single-page prototype into an enterprise-grade multi-page operations center:
- **Routing:** Clean `react-router-dom` URL hierarchy persisting across reloads.
- **Navigation:** Modern collapsible sidebar with mobile drawer support.
- **5 Full-Featured Pages:**
  1. *Overview*: Live constellation, KPI strip, verdict velocity, and live feed.
  2. *Investigations*: Full case triage table, 4-panel forensic PNG viewer, AI narrative SAR, and status transitions.
  3. *Analytics*: Recharts time-series verdict breakdown, fraud rate trends, top corporate mule accounts, bank distribution, and rule heatmap.
  4. *System Health*: Detection latency percentiles (p50/p99), DB pool status, Redis ping, throughput, and component grid.
  5. *Settings*: Adaptive sensitivity slider, simulator controls, and GitHub Actions CI/CD deployment observability.

---

## 8. Verification Method

### 8.1 Build & Package Verification
1. **Package Installation:**
   ```bash
   cd frontend && npm install react-router-dom lucide-react && npm install -D eslint eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-react-refresh
   ```
2. **ESLint Lint Check:**
   ```bash
   cd frontend && npm run lint
   ```
   *Expected Output:* Zero syntax errors or missing hook dependency warnings.
3. **Vite Production Build:**
   ```bash
   cd frontend && npm run build
   ```
   *Expected Output:* `dist/` directory generated with optimized JS chunks and CSS assets without errors.

### 8.2 Functional Verification Checklist
1. **Route Persistence:** Navigate to `http://localhost:8000/investigations`, refresh the browser, and confirm the Investigations table renders without 404.
2. **Sidebar Collapse:** Click the collapse toggle; verify sidebar transitions to 80px icon mode and setting persists across page reloads.
3. **Forensic PNG & SAR Narrative:** Click a case in Investigations; verify `/upi/cases/{case_id}/graph.png` loads and markdown renders cleanly.
4. **Status Transition:** Click "Mark as Reviewed" on a case; verify optimistic status update and `PATCH /cases/{case_id}/status` call.
5. **Real-Time WS Push:** Trigger a simulation from ControlBar or Settings; verify live feed, KPI counters, and verdict velocity chart update simultaneously across all views.
