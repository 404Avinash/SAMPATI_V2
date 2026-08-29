## 2026-08-29T15:36:46Z
You are the Frontend Worker (worker_m3_frontend) for Milestone M3 in SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/worker_m3_frontend/
The project root is: /home/avi/Downloads/Sampati_v2

CRITICAL MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A forensic auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please read:
1. /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
2. /home/avi/Downloads/Sampati_v2/PROJECT.md
3. /home/avi/Downloads/Sampati_v2/frontend/package.json
4. Existing files in frontend/src/:
   - frontend/src/App.jsx
   - frontend/src/main.jsx
   - frontend/src/context/AppStateContext.jsx
   - frontend/src/services/api.js
   - frontend/src/components/common/Sidebar.jsx
   - frontend/src/components/common/Topbar.jsx
   - frontend/src/pages/OverviewPage.jsx
   - frontend/src/pages/InvestigationsPage.jsx
   - frontend/src/components/analytics/*
   - frontend/src/components/investigations/*

Your Mission (Milestone M3: Multi-Page React Dashboard):
1. Create frontend/src/layouts/MainLayout.jsx:
   - Persistent responsive layout with Sidebar and Topbar.
   - Contains mobile sidebar toggle and backdrop drawer overlay.
   - Contains <Outlet /> for active page rendering, standard footer, and CaseDrawer/CaseDetailModal integration.
2. Implement frontend/src/pages/AnalyticsPage.jsx:
   - Real-time and time-series analytics dashboard.
   - Top KPI summary strip using AnalyticsSummaryKpis.
   - TimeSeriesVerdictChart (hourly/daily interval toggle, Allow/Hold/Block Recharts AreaChart).
   - FraudRateTrendChart (fraud percentage trend over time).
   - TopFlaggedAccountsTable (top mule hubs/corporate accounts with bank names, total amounts, risk scores).
   - BankDistributionChart (distribution across @okhdfcbank, @icici, @oksbi, @okaxis, @paytm).
   - Data fetched from api.getAnalytics() with graceful fallback data if API returns empty/offline.
3. Implement frontend/src/pages/SystemHealthPage.jsx:
   - Real-time telemetry dashboard.
   - Latency Percentiles Card: p50, p90, p99, min, max, avg (formatted in milliseconds, e.g. 1.25 ms).
   - PostgreSQL Connection Pool Card: status badge, driver, pool_size, max_overflow, checked_in/checked_out connections.
   - Redis Cache Card: status, ping latency, fallback indicators.
   - WebSocket Telemetry Card: active connections count, streaming status, real-time message indicator.
   - Throughput & Performance Card: sliding 60s throughput (batches/min, txns/sec, total evaluations).
   - Process Uptime Card: human-readable uptime (e.g. 2d 4h 15m), start timestamp.
   - Auto-refresh interval (polling every 3-5 seconds) and manual refresh button.
4. Implement frontend/src/pages/SettingsPage.jsx:
   - Adaptive Sensitivity Threshold: slider + numeric input (0.1 to 3.0) with "Save Sensitivity" invoking api.updateSensitivity().
   - Fraud Simulator Controls: fraud injection ratio slider (0% to 100%), transaction count selector (50 to 1000), "Generate Stream" button invoking api.simulate().
   - Active CI/CD Deployment Status Card: displays latest commit SHA, GHCR image tag (ghcr.io/404avinash/sampati_v2:latest), pipeline status badge (PASSING), AWS EC2 environment, health status (200 OK), rollback target, and simulated deploy trigger.
5. Refactor frontend/src/App.jsx:
   - Set up React Router (BrowserRouter, Routes, Route, Navigate).
   - Wrap with AppStateProvider.
   - Define routes:
     - / -> Navigate to /overview (replace)
     - /overview -> OverviewPage
     - /investigations -> InvestigationsPage
     - /investigations/:caseId -> InvestigationsPage (loads dossier modal)
     - /analytics -> AnalyticsPage
     - /health -> SystemHealthPage
     - /system-health -> Navigate to /health (replace)
     - /settings -> SettingsPage
     - * -> Navigate to /overview (replace)
   - Ensure URL routing persists page state on browser refresh.
6. Verify Build and Lint:
   - Run `npm run build` in frontend/ and ensure 0 errors.
   - Run `npm run lint` (or `npx eslint src`) and ensure 0 lint errors/warnings.
7. Write complete handoff report to /home/avi/Downloads/Sampati_v2/.agents/worker_m3_frontend/handoff.md and notify parent via send_message.
