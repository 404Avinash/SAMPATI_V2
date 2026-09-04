# Handoff Report: Requirement R2 (Make KPI Numbers Dynamic & Real)

**Agent**: `survey_explorer_2`  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2`  
**Parent Conversation ID**: `633a9079-d863-4bd1-9c75-d637844689ae`  
**Status**: Complete (Hard Handoff)  
**Deliverable**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/survey_r2_report.md`  

---

## 1. Observation

1. **Threat Intelligence Page (`frontend/src/pages/ThreatIntelPage.jsx:416-456`)**:
   - The top telemetry strip renders hardcoded arithmetic and string literals:
     ```jsx
     {/* Line 422 */}
     <span className="text-2xl font-bold font-mono text-ink-900">{signals.length + 18}</span>
     {/* Line 432 */}
     <span className="text-2xl font-bold font-mono text-ink-900">3 Campaigns</span>
     {/* Line 442 */}
     <span className="text-2xl font-bold font-mono text-ink-900">42 Nodes</span>
     {/* Line 452 */}
     <span className="text-2xl font-bold font-mono text-emerald-600">98% Defensible</span>
     <span className="text-xs font-mono text-muted">Zero False-Pos</span>
     ```
   - In `ThreatIntelPage.jsx:245-263`, `loadSignals` invokes only `api.getThreatSignals({ limit: 50 })`. It does not invoke `api.getThreatCampaigns()` or `api.getThreatGraph()`.
   - In `ThreatIntelPage.jsx:260-262`, `useEffect` executes only once on component mount without a recurring timer.
   - Lines 642, 681, 685, 701, 712 hardcode "94%", "14 Signals", "8 Accounts", "CAMP-SMURF-DISPERSAL-03 (19 signals)", and "CAMP-TASK-INVEST-02 (8 signals)".

2. **Overview KPI Strip (`frontend/src/components/KpiStrip.jsx`, `frontend/src/context/AppStateContext.jsx`)**:
   - `frontend/src/components/KpiStrip.jsx:15-28` maps tiles (`evaluated`, `allowed`, `held`, `blocked`, `honeypot_hits`, `rings`, `dpip`) to properties of `stats`.
   - In `frontend/src/context/AppStateContext.jsx:400-410`, `refreshStats()` is called only once in the initial `useEffect`.
   - There is no recurring interval for `refreshStats()` when WebSocket traffic is quiescent.

3. **Investigations Tab Badge (`frontend/src/components/common/Navbar.jsx:69-75, 122-128`)**:
   - `Navbar.jsx:69-75` calculates `flaggedCount` from a local array slice:
     ```javascript
     const flaggedCount = cases.filter(
       (c) =>
         (c.verdict === "HOLD" || c.verdict === "BLOCK" || (c.risk_score && c.risk_score >= 50)) &&
         c.status !== "REVIEWED" &&
         c.status !== "RESOLVED" &&
         c.status !== "DISMISSED"
     ).length;
     ```
   - The badge displays `{flaggedCount}` instead of reading the true backend count of open cases from `/cases?status=OPEN` or `/stats`.

4. **Analytics Page (`frontend/src/pages/AnalyticsPage.jsx`, `app/services/upi_cases.py`)**:
   - In `app/services/upi_cases.py:624`, the endpoint `/stats/analytics` returns key `"top_flagged_accounts"`.
   - In `frontend/src/pages/AnalyticsPage.jsx:339`, the table is passed `accounts={analyticsData?.top_accounts || []}`.
   - Because `top_accounts` is not returned, the table renders empty or falls back to synthetic mock data.
   - In `frontend/src/components/analytics/AnalyticsSummaryKpis.jsx:28`, `activeCampaigns` falls back to `Math.ceil(flagged / 5)` because `summary` lacks `active_campaigns_count`.

5. **Backend Endpoints (`app/api/intel.py`, `app/api/upi.py`, `app/services/threat_intel_service.py`)**:
   - `GET /intel/signals` returns `ThreatSignalListResponse(total=total, signals=..., limit=..., offset=...)`.
   - `GET /intel/campaigns` returns `List[Dict[str, Any]]` (3 active campaigns with `signals_count`, `average_similarity`, `associated_vpas_count`).
   - `GET /intel/graph` returns `ThreatGraphResponse(total_nodes=..., total_edges=..., nodes=..., edges=...)`.
   - `GET /stats` returns `{ cases: { total, open, investigated, resolved }, evaluated, allowed, held, blocked, honeypot_hits, rings, dpip }`.
   - `GET /cases` returns `{"count": total_count, "items": [...]}` and supports `status=OPEN`.

---

## 2. Logic Chain

1. From Observation 1, `ThreatIntelPage.jsx` exhibits hardcoded numbers (`signals.length + 18`, `3 Campaigns`, `42 Nodes`) because `api.getThreatCampaigns()` and `api.getThreatGraph()` were never integrated into its data lifecycle.
2. Connecting `ThreatIntelPage.jsx` to `api.getThreatSignals()`, `api.getThreatCampaigns()`, and `api.getThreatGraph()` via `Promise.allSettled` enables dynamic binding:
   - Signals KPI = `resSignals.total` (or `signals.length`)
   - Syndicates KPI = `${campaigns.length} Campaigns`
   - Graph Nodes KPI = `${graphStats.total_nodes} Nodes`
   - Early-Warning KPI = `${(campaigns[0].average_similarity * 100).toFixed(0)}% Heuristic Match` and `< 2% escalation rate` (eliminating AI slop).
3. From Observation 2, `AppStateContext.jsx` lacks a recurring timer for `refreshStats()`. Adding `setInterval(() => { refreshStats(); refreshCases(); }, 15000)` satisfies the 15-second refresh requirement.
4. To avoid jarring re-renders, shallow-comparing incoming stats in `setStats(prev => ...)` ensures React skips re-rendering when counts are unchanged. When values do change, `useCountUp` animates smoothly.
5. From Observation 3 and Observation 5, `/stats` already returns `cases.open`. Exposing `stats.open_cases = s.cases?.open` in `AppStateContext` allows `Navbar.jsx` to bind its badge directly to the real open case count without client-side array slicing issues.
6. From Observation 4, resolving the property mismatch (`analyticsData?.top_flagged_accounts || analyticsData?.top_accounts`) and providing `"top_accounts"` alias alongside `"top_flagged_accounts"` in `upi_cases.py` ensures live mule accounts populate the table.

---

## 3. Caveats

1. The central fraud graph is in-memory (`NetworkX DiGraph`) in `app/services/graph_service.py`; upon service restart, `total_nodes` starts with base seeded nodes unless threat signals are ingested or simulated.
2. In `Navbar.jsx`, if the user has navigated between multiple tabs without refreshing, the badge will reflect whatever `stats.open_cases` reports from the 15-second polling cycle.
3. No other caveats.

---

## 4. Conclusion

Requirement R2 can be achieved with surgical frontend and backend updates:
1. Wire `ThreatIntelPage.jsx` to fetch live data from `api.getThreatSignals()`, `api.getThreatCampaigns()`, and `api.getThreatGraph()`, and remove all hardcoded metric strings.
2. Add a 15-second polling interval in `AppStateContext.jsx` with reference equality checking in `setStats` to ensure clean, non-jarring auto-refresh.
3. Wire the Investigations navigation badge in `Navbar.jsx` to `stats.open_cases` (populated from `/stats` or `/cases?status=OPEN`).
4. Reconcile the `top_flagged_accounts` / `top_accounts` key between `AnalyticsPage.jsx` and `upi_cases.py`, and auto-refresh the analytics view.

---

## 5. Verification Method

1. **Backend Pytest Suite**:
   ```bash
   .venv/bin/pytest tests/test_threat_intel_r1.py -v
   .venv/bin/pytest tests/ -v
   ```
   All 969 tests must pass with 0 failures.

2. **Frontend Linter & Build**:
   ```bash
   cd frontend && npm run lint && npm run build
   ```
   Must pass with 0 ESLint warnings (`--max-warnings 0`) and generate a clean production build.

3. **Behavioral Code Invalidation Conditions**:
   - A `grep` for `"signals.length + 18"`, `"3 Campaigns"`, `"42 Nodes"`, or `"Zero False-Pos"` in `frontend/src/` must return 0 matches.
   - Network inspector shows `GET /upi/stats` fired every 15 seconds on Overview page.
   - `GET /cases?status=OPEN` count matches the badge on the Investigations tab.
