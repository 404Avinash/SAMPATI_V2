# BRIEFING — 2026-09-04T10:25:00Z

## Mission
Conduct a comprehensive Survey on Requirement R2 (Make KPI Numbers Dynamic & Real) across frontend and backend.

## 🔒 My Identity
- Archetype: explorer
- Roles: survey, read-only investigation, produce structured reports
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2
- Original parent: 633a9079-d863-4bd1-9c75-d637844689ae
- Milestone: Requirement R2 Survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Do NOT modify any source code files
- Deliver findings in survey_r2_report.md and handoff in handoff.md

## Current Parent
- Conversation ID: 633a9079-d863-4bd1-9c75-d637844689ae
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `frontend/src/pages/ThreatIntelPage.jsx`
  - `frontend/src/pages/OverviewPage.jsx`
  - `frontend/src/components/KpiStrip.jsx`
  - `frontend/src/context/AppStateContext.jsx`
  - `frontend/src/components/common/Navbar.jsx`
  - `frontend/src/pages/AnalyticsPage.jsx`
  - `frontend/src/components/analytics/AnalyticsSummaryKpis.jsx`
  - `frontend/src/components/analytics/TopFlaggedAccountsTable.jsx`
  - `frontend/src/components/analytics/TopDmvAccountsTable.jsx`
  - `frontend/src/components/analytics/AnalystWorkloadHeatmap.jsx`
  - `frontend/src/services/api.js`
  - `app/api/intel.py`
  - `app/services/threat_intel_service.py`
  - `app/services/graph_service.py`
  - `app/models/threat_intel.py`
  - `app/api/upi.py`
  - `app/services/upi_cases.py`
  - `app/engine/dmv.py`
- **Key findings**:
  - `ThreatIntelPage.jsx:416-456`: hardcoded `signals.length + 18`, `"3 Campaigns"`, `"42 Nodes"`, `"98% Defensible"`, `"Zero False-Pos"`.
  - `AppStateContext.jsx:400-410`: `refreshStats()` is only executed once on mount; lacks 15s auto-refresh interval.
  - `Navbar.jsx:69-75`: Investigations badge calculates `flaggedCount` from local sliced `cases` array rather than `/stats` `cases.open` or `/cases?status=OPEN`.
  - `AnalyticsPage.jsx:339`: queries `analyticsData?.top_accounts`, but `upi_cases.py:624` returns `"top_flagged_accounts"`, leading to dropped live mule data.
  - Backend endpoints (`/intel/signals`, `/intel/campaigns`, `/intel/graph`, `/cases`, `/stats`, `/stats/analytics`) are mostly fully populated and need minor field alias additions for seamless consumption.
- **Unexplored areas**: None for R2 scope.

## Key Decisions Made
- Fully documented all 4 frontend targets and 6 backend endpoints in `survey_r2_report.md`.
- Authored self-contained 5-component handoff report in `handoff.md`.

## Artifact Index
- survey_r2_report.md — Comprehensive survey report on R2
- handoff.md — 5-component handoff report
