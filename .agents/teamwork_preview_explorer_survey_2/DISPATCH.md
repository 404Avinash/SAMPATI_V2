## 2026-09-04T10:25:00Z
Conduct a comprehensive Survey on Requirement R2 (Make KPI Numbers Dynamic & Real):
1. Inspect the entire frontend (in /home/avi/Downloads/Sampati_v2/frontend/src) for all KPI and metric numbers:
   - Threat Intelligence page: Find the "21 signals", "3 campaigns", "42 nodes" counters or any other hardcoded metric cards. Trace where they are rendered and how they should fetch live data from backend endpoints `/intel/signals` and `/intel/campaigns`.
   - Overview page: Inspect the KPI strip (Blocked, Flagged, Honeypot Hits, Volume, etc.). Identify how it currently gets data and what changes are needed to ensure it auto-refreshes every 15 seconds cleanly without jarring re-renders.
   - Investigations tab badge: Find the tab navigation / header where the Investigations badge is rendered. Identify where the case count comes from and how to wire it to the actual count of cases from `/cases` or `/upi/cases`.
   - Analytics page: Check all KPI cards and metrics for any hardcoded or stale values.
2. Inspect the backend endpoints (`/intel/signals`, `/intel/campaigns`, `/cases`, `/upi/cases`, `/upi/stats`, `/stats/analytics`, etc.) in `app/api/` and `app/services/`:
   - Verify what fields and counts these endpoints return.
   - If any endpoint lacks a required count or summary field, identify exact backend additions needed.
3. Catalogue all files, line numbers, state variables, and exact implementation recommendations.
