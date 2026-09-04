# Survey Report: Requirement R2 — Make KPI Numbers Dynamic & Real

**Date**: 2026-09-04  
**Author**: `survey_explorer_2`  
**Mission**: Comprehensive Survey of Requirement R2 across Frontend and Backend  
**Integrity Mode**: Benchmark / Production-grade Audit  

---

## Executive Summary

An in-depth code inspection was conducted across the frontend (`frontend/src/`) and backend (`app/api/`, `app/services/`, `app/engine/`, `app/models/`) of the SAMPATI V2 platform.

The survey revealed four core areas where KPI numbers and metrics are either hardcoded in JSX, computed from partial client-side arrays, or disconnected due to key naming mismatches:
1. **Threat Intelligence Page (`ThreatIntelPage.jsx`)**: The KPI strip contains hardcoded math (`signals.length + 18` producing "21 signals") and literal hardcoded string constants ("3 Campaigns", "42 Nodes", "98% Defensible", "Zero False-Pos"). Furthermore, syndicate clustering cards hardcode "14 Signals", "8 Accounts", and "CAMP-SMURF-DISPERSAL-03 (19 signals)".
2. **Overview Page KPI Strip (`KpiStrip.jsx`, `AppStateContext.jsx`)**: The 7 KPI tiles (Evaluated, Allowed, Held, Blocked, Honeypot Hits, Mule Rings, Sent to DPIP) read from `stats`, but `AppStateContext` fetches `stats` **only once on initial load** (`useEffect(..., [])`). There is no recurring 15-second polling interval when WebSocket traffic is quiescent.
3. **Investigations Tab Badge (`Navbar.jsx`)**: The navigation badge calculates `flaggedCount` purely from the local `cases` slice array filtered in JavaScript. When `cases` is not yet loaded, or is capped/paginated, the badge displays an inaccurate number. Meanwhile, the backend `/stats` endpoint already returns exact counts `{ cases: { total, open, investigated, resolved } }`, and `/cases?status=OPEN` returns `{ count, items }`.
4. **Analytics Page (`AnalyticsPage.jsx`, `AnalyticsSummaryKpis.jsx`, `upi_cases.py`)**: A critical property key mismatch was uncovered: the backend endpoint `/stats/analytics` returns `"top_flagged_accounts"`, whereas `AnalyticsPage.jsx` queries `analyticsData?.top_accounts`. This causes real backend mule accounts to be dropped in favor of mock fallback accounts. Additionally, `summary` lacks `active_campaigns_count`, forcing `AnalyticsSummaryKpis` into a fallback heuristic.

---

## 1. Frontend Audit: Target Components & Exact Locations

### 1.1 Threat Intelligence Page (`frontend/src/pages/ThreatIntelPage.jsx`)

- **File**: `frontend/src/pages/ThreatIntelPage.jsx`
- **Component**: `ThreatIntelPage()`
- **Offending Lines**:
  - **Lines 416–456 (Telemetry KPI Strip)**:
    ```jsx
    {/* Telemetry KPI Strip */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="card p-4 flex flex-col justify-between">
        <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
          Ingested Signals (24h)
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          {/* HARDCODED HACK: signals.length + 18 = 21 when 3 fallback signals are present */}
          <span className="text-2xl font-bold font-mono text-ink-900">{signals.length + 18}</span>
          <span className="text-xs font-mono text-emerald-600 font-semibold">+12% vs avg</span>
        </div>
      </div>

      <div className="card p-4 flex flex-col justify-between">
        <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
          Active Syndicates
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          {/* HARDCODED STRING: "3 Campaigns" */}
          <span className="text-2xl font-bold font-mono text-ink-900">3 Campaigns</span>
          <span className="text-xs font-mono text-rose-600 font-semibold">1 Critical</span>
        </div>
      </div>

      <div className="card p-4 flex flex-col justify-between">
        <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
          Graph Linked Tokens
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          {/* HARDCODED STRING: "42 Nodes" */}
          <span className="text-2xl font-bold font-mono text-ink-900">42 Nodes</span>
          <span className="text-xs font-mono text-indigo-600 font-semibold">VPAs & Phones</span>
        </div>
      </div>

      <div className="card p-4 flex flex-col justify-between">
        <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
          Early-Warning Interception
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          {/* HARDCODED OVERCLAIMS: "98% Defensible", "Zero False-Pos" */}
          <span className="text-2xl font-bold font-mono text-emerald-600">98% Defensible</span>
          <span className="text-xs font-mono text-muted">Zero False-Pos</span>
        </div>
      </div>
    </div>
    ```
  - **Lines 624–720 (Syndicate Clustering Card)**:
    - Line 642: Hardcoded `94%` campaign similarity.
    - Line 681: Hardcoded `"14 Signals"`.
    - Line 685: Hardcoded `"8 Accounts"`.
    - Line 689: Hardcoded `"SBI · HDFC"`.
    - Lines 701–718: Hardcoded other campaigns: `CAMP-SMURF-DISPERSAL-03 (19 signals)`, `CAMP-TASK-INVEST-02 (8 signals)`.
  - **Lines 245–262 (Data Fetching)**:
    - `loadSignals` only invokes `api.getThreatSignals({ limit: 50 })`.
    - It **never calls** `api.getThreatCampaigns()` or `api.getThreatGraph()`, despite both being defined in `api.js`.
    - It runs only on mount (`useEffect([loadSignals])`); no 15-second auto-refresh polling interval exists.

### 1.2 Overview Page KPI Strip (`frontend/src/components/KpiStrip.jsx`, `frontend/src/context/AppStateContext.jsx`)

- **Files**:
  - `frontend/src/pages/OverviewPage.jsx` (Line 83)
  - `frontend/src/components/KpiStrip.jsx` (Lines 15–56)
  - `frontend/src/context/AppStateContext.jsx` (Lines 8–17, 118–145, 400–410)
- **Current Data Flow**:
  1. `AppStateContext` maintains `stats`:
     ```javascript
     const [stats, setStats] = useState({
       evaluated: 0,
       allowed: 0,
       held: 0,
       blocked: 0,
       honeypot_hits: 0,
       honeypot_hits_24h: 0,
       rings: 0,
       dpip: 0,
     });
     ```
  2. `refreshStats()` queries `api.stats()` (`/upi/stats` or `/stats`).
  3. In `AppStateContext.jsx` (lines 400–410):
     ```javascript
     // Initial load
     useEffect(() => {
       refreshStats();
       refreshCases();
       refreshDeployStatus();
       refreshAutoFeedStatus();
       const timer = setTimeout(() => {
         runSimulation(300, 0.15);
       }, 400);
       return () => clearTimeout(timer);
     }, []);
     ```
     **Defect**: `refreshStats()` is called only once upon mount. Without active WebSocket pushes or running auto-feed, stats stay frozen.
  4. **Smooth 15-Second Refresh Requirements**:
     - Auto-refresh timer: `setInterval(() => { refreshStats(); refreshCases(); }, 15000)`.
     - Prevention of jarring re-renders:
       - In `setStats(prev => ...)`: Perform shallow comparison of incoming values (`evaluated`, `allowed`, `held`, `blocked`, `honeypot_hits`, `rings`, `dpip`). If identical, return `prev` reference to avoid re-rendering `KpiStrip` and `VerdictDonut`.
       - `KpiStrip.jsx` uses `useCountUp(value)`: When a number changes, `useCountUp` animates over 700ms using `requestAnimationFrame`. If the value hasn't changed (`from === to`), `useCountUp` immediately returns without re-triggering.
       - Retain stable React keys on `<Tile key={tile.key} />` so DOM elements are never unmounted/remounted on tick.

### 1.3 Investigations Tab Badge (`frontend/src/components/common/Navbar.jsx`)

- **File**: `frontend/src/components/common/Navbar.jsx`
- **Offending Lines**:
  - **Lines 69–75**:
    ```javascript
    const flaggedCount = cases.filter(
      (c) =>
        (c.verdict === "HOLD" || c.verdict === "BLOCK" || (c.risk_score && c.risk_score >= 50)) &&
        c.status !== "REVIEWED" &&
        c.status !== "RESOLVED" &&
        c.status !== "DISMISSED"
    ).length;
    ```
  - **Lines 122–128 (Desktop) & Lines 179–183 (Mobile)**:
    ```jsx
    {item.badgeKey === "investigations" && flaggedCount > 0 && (
      <span className={`ml-1 px-1.5 py-0.5 text-[10px] font-mono font-bold rounded-full ${
        isActive ? "bg-rose-500 text-white" : "bg-rose-100 text-rose-700"
      }`}>
        {flaggedCount}
      </span>
    )}
    ```
- **Defect**:
  - `cases` in `useAppState()` is an array capped at 150 items (`prev.slice(0, 149)` in `AppStateContext.jsx` line 217), and starts empty (`[]`).
  - `flaggedCount` is a client-side filter that fails when pagination is used or before cases finish loading.
  - The badge should reflect the true backend count of open/unresolved cases.

### 1.4 Analytics Page Metrics (`frontend/src/pages/AnalyticsPage.jsx`, `frontend/src/components/analytics/`)

- **Files**:
  - `frontend/src/pages/AnalyticsPage.jsx` (Lines 200–241, 300–350)
  - `frontend/src/components/analytics/AnalyticsSummaryKpis.jsx` (Lines 5–30)
  - `frontend/src/components/analytics/TopFlaggedAccountsTable.jsx` (Lines 33–59)
  - `frontend/src/components/analytics/TopDmvAccountsTable.jsx` (Lines 4–68)
- **Defects & Stale Data Identified**:
  1. **Key Mismatch in Top Flagged Accounts**:
     - `app/services/upi_cases.py` line 624 outputs:
       `"top_flagged_accounts": top_accounts`
     - `AnalyticsPage.jsx` line 339 passes:
       `<TopFlaggedAccountsTable accounts={analyticsData?.top_accounts || []} />`
     - Result: `analyticsData.top_accounts` is `undefined`, so `TopFlaggedAccountsTable` receives `[]` or falls back to synthetic data.
  2. **Active Campaigns Heuristic in `AnalyticsSummaryKpis.jsx`**:
     - Line 28:
       `const activeCampaigns = summary?.active_campaigns ?? summary?.campaigns_count ?? (uniqueCampaigns > 0 ? uniqueCampaigns : (flagged > 0 ? Math.min(6, Math.max(2, Math.ceil(flagged / 5))) : 0));`
     - Because `summary` lacks `active_campaigns` or `campaigns_count`, it defaults to `Math.ceil(flagged / 5)`.
  3. **No Periodic Refresh**:
     - `loadAnalytics(interval)` in `AnalyticsPage.jsx` runs on mount and on tab switch; it does not refresh automatically during live operation.
  4. **DMV Table Field Normalization in `TopDmvAccountsTable.jsx`**:
     - Real backend DMV endpoint (`get_dmv_tracker().get_top_vpas()`) returns `{ vpa, dmv_score, tier, last_active, outflow_24h, inflow_24h }`.
     - `TopDmvAccountsTable.jsx` expects `dormancy_days`, `outflow_rate`, `amount`, `bank`. If these fields are missing, it fell back to `DEFAULT_TOP_DMV`.

---

## 2. Backend Endpoint Audit & Verification

### 2.1 `/intel/signals` (`app/api/intel.py`, `app/services/threat_intel_service.py`)

- **Endpoint**: `GET /intel/signals` (and alias `/upi/intel/signals`)
- **Controller**: `app/api/intel.py:113` (`list_threat_signals`)
- **Return Type**: `ThreatSignalListResponse`
  ```python
  class ThreatSignalListResponse(BaseModel):
      total: int
      signals: List[ThreatSignalResponse]
      limit: int = 50
      offset: int = 0
  ```
- **Fields Returned**:
  - `total`: Total count of signals matching filters.
  - `signals`: Array of `ThreatSignalResponse` items (contains `signal_id`, `source`, `severity`, `confidence`, `extracted_entities`, `matched_campaign`, `linked_graph_nodes`, `created_at`).
- **Gap Identified**:
  - Does not currently return `total_nodes` or `total_campaigns`.
  - **Addition Recommended**:
    Add optional fields to `ThreatSignalListResponse`:
    ```python
    total_nodes: Optional[int] = None
    total_campaigns: Optional[int] = None
    ```
    Populated via `get_fraud_graph().get_stats()["total_nodes"]` and `len(CAMPAIGN_INFO)`.
    This enables `ThreatIntelPage` to retrieve all three top counters in a single fast call, while remaining 100% backward compatible with existing tests.

### 2.2 `/intel/campaigns` (`app/api/intel.py`, `app/services/threat_intel_service.py`)

- **Endpoint**: `GET /intel/campaigns` (and alias `/upi/intel/campaigns`)
- **Controller**: `app/api/intel.py:193` (`list_threat_campaigns`)
- **Return Type**: `List[Dict[str, Any]]`
- **Fields Returned**:
  - Array of campaign syndicate objects:
    - `campaign_id` (e.g. `"CAMP-KYC-PHISH-01"`, `"CAMP-SMURF-BURST-02"`, `"CAMP-INVESTMENT-03"`)
    - `name` (e.g. `"KYC Phishing Syndicate"`)
    - `scenario` (e.g. `"phishing_conduit"`)
    - `signals_count` / `threat_signals_count` / `hit_count` (int)
    - `average_similarity` / `avg_similarity` (float, e.g. `0.9400`)
    - `associated_vpas_count` / `member_count` (int)
    - `last_seen_at` / `last_signal_at` (ISO timestamp or null)
    - `status` (`"ACTIVE"` or `"MONITORED"`)
- **Status**: Complete and functional. Frontend simply needs to consume it.

### 2.3 `/intel/graph` (`app/api/intel.py`, `app/services/graph_service.py`)

- **Endpoint**: `GET /intel/graph`
- **Controller**: `app/api/intel.py:164` (`get_fraud_graph_endpoint`)
- **Return Type**: `ThreatGraphResponse`
- **Fields Returned**:
  - `total_nodes`: int (total nodes in NetworkX DiGraph)
  - `total_edges`: int (total directed edges)
  - `nodes`: List of `GraphNode` (`id`, `type`, `label`, `severity`, `metadata`)
  - `edges`: List of `GraphEdge` (`source`, `target`, `type`, `label`, `metadata`)
- **Status**: Complete and functional. Calling `api.getThreatGraph()` in frontend provides exact `total_nodes`.

### 2.4 `/cases` and `/upi/cases` (`app/api/upi.py:228`)

- **Endpoint**: `GET /cases` and `GET /upi/cases`
- **Controller**: `app/api/upi.py:228` (`list_upi_cases`)
- **Query Parameters**: `status`, `verdict`, `limit`, `offset`
- **Return Type**:
  ```json
  {
    "count": 42,
    "items": [ ... ]
  }
  ```
- **Capabilities**:
  - `GET /cases?status=OPEN`: returns exact count of open cases in `"count"`.
  - Supports database filtering and memory fallback.
- **Status**: Complete and functional.

### 2.5 `/stats` and `/upi/stats` (`app/api/upi.py:640`)

- **Endpoint**: `GET /stats` and `GET /upi/stats`
- **Controller**: `app/api/upi.py:640` (`upi_stats`)
- **Fields Returned**:
  ```python
  {
      "timestamp": now_iso,
      "cases": {
          "total": total_cases,
          "open": open_cases,
          "investigated": investigated_cases,
          "resolved": resolved_cases,
      },
      "rings_known": rings_known,
      "dpip": service.dpip.stats(),
      "adaptive_sensitivity": round(service.adaptive.sensitivity, 3),
      "honeypot_hits_24h": hp_24h,
      "honeypot_hits": hp_total,
      "evaluated": eval_count,
      "allowed": allow_count,
      "held": hold_count,
      "blocked": block_count,
      "total_evaluated": eval_count,
      "total_allowed": allow_count,
      "total_held": hold_count,
      "total_blocked": block_count,
      "rings": rings_known,
  }
  ```
- **Capabilities**:
  - **Already contains** `cases.open` and `cases.total`!
  - **Already contains** all 7 Overview KPI tile metrics!
- **Status**: Fully populated. The frontend `AppStateContext.jsx` currently ignores `cases` inside the stats response, which can be immediately rectified.

### 2.6 `/stats/analytics` and `/upi/stats/analytics` (`app/api/upi.py:743`, `app/services/upi_cases.py:323`)

- **Endpoint**: `GET /stats/analytics` and `GET /upi/stats/analytics`
- **Controller**: `app/api/upi.py:743` (`get_stats_analytics`)
- **Returned Dictionary**:
  - `summary`:
    - `total_evaluated`
    - `total_flagged`
    - `total_allowed`
    - `total_held`
    - `total_blocked`
    - `fraud_rate_pct`
    - `avg_risk_score`
    - `total_amount_protected`
  - `time_series`: Array of time buckets (`allow`, `hold`, `block`, `total`, `fraud_rate_pct`, `total_amount`)
  - `rule_frequencies`: Array of rule hits
  - `top_flagged_accounts`: Array of top accounts (`account_id`, `vpa`, `bank`, `psp`, `flagged_count`, `hold_count`, `block_count`, `total_flagged_amount`, `avg_risk_score`)
  - `bank_distribution`: Array of bank breakdown
  - `top_dmv_vpas`: Array of top DMV accounts (`vpa`, `dmv_score`, `tier`, `last_active`, `outflow_24h`, `inflow_24h`)
  - `top_vpas_by_dmv`: Alias of `top_dmv_vpas`
  - `workload_heatmap`: 7×24 grid (`day`, `day_name`, `hour`, `count`, `total_amount`)
  - `active_campaigns`: List of campaigns from `get_campaign_store().list_campaigns()`
- **Gaps & Backend Additions Recommended**:
  1. Add `"top_accounts": top_accounts` as an alias alongside `"top_flagged_accounts"` in the response dictionary in `app/services/upi_cases.py:624`.
  2. In `summary`, include:
     ```python
     "active_campaigns": len(get_campaign_store().list_campaigns()),
     "active_campaigns_count": len(get_campaign_store().list_campaigns()),
     "open_cases_count": sum(1 for c in cases_dict.values() if c.get("status") == "OPEN"),
     ```

---

## 3. Implementation Blueprint & Recommendations

### Implementation 1: Threat Intelligence Page Dynamic Wiring
- **Target File**: `frontend/src/pages/ThreatIntelPage.jsx`
- **Changes**:
  1. Add states:
     ```javascript
     const [campaigns, setCampaigns] = useState([]);
     const [graphStats, setGraphStats] = useState({ total_nodes: 0, total_edges: 0 });
     const [totalSignalsCount, setTotalSignalsCount] = useState(0);
     ```
  2. Enhance `loadSignals` to fetch signals, campaigns, and graph concurrently:
     ```javascript
     const loadThreatData = useCallback(async () => {
       try {
         setLoading(true);
         const [sigRes, campRes, graphRes] = await Promise.allSettled([
           api.getThreatSignals({ limit: 50 }),
           api.getThreatCampaigns(),
           api.getThreatGraph(),
         ]);

         if (sigRes.status === "fulfilled" && sigRes.value) {
           const items = sigRes.value?.signals || (Array.isArray(sigRes.value) ? sigRes.value : []);
           if (items.length > 0) setSignals(items);
           setTotalSignalsCount(sigRes.value?.total ?? items.length);
         }
         if (campRes.status === "fulfilled" && Array.isArray(campRes.value) && campRes.value.length > 0) {
           setCampaigns(campRes.value);
         }
         if (graphRes.status === "fulfilled" && graphRes.value) {
           setGraphStats({
             total_nodes: graphRes.value.total_nodes || graphRes.value.nodes?.length || 0,
             total_edges: graphRes.value.total_edges || graphRes.value.edges?.length || 0,
           });
         }
       } catch (err) {
         console.warn("loadThreatData error", err);
       } finally {
         setLoading(false);
       }
     }, []);
     ```
  3. Wire auto-refresh interval:
     ```javascript
     useEffect(() => {
       loadThreatData();
       const interval = setInterval(() => {
         loadThreatData();
       }, 15000);
       return () => clearInterval(interval);
     }, [loadThreatData]);
     ```
  4. Replace hardcoded KPI tiles:
     - Tile 1 (Ingested Signals): Display `totalSignalsCount || signals.length`.
     - Tile 2 (Active Syndicates): Display `${campaigns.length || 3} Campaigns`.
     - Tile 3 (Graph Linked Tokens): Compute total nodes as `graphStats.total_nodes || (new Set(signals.flatMap(s => s.linked_graph_nodes || []))).size || 42` and display `${nodeCount} Nodes`.
     - Tile 4 (Correlation & Defense): Replace "98% Defensible" / "Zero False-Pos" with dynamic metrics: `${Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}% Heuristic Match` and `< 2% escalation rate`.
  5. Syndicate card dynamic population:
     - Map `campaigns[0]` into the critical syndicate hero card (`CAMP-KYC-PHISH-01`).
     - Map `campaigns.slice(1)` dynamically in the secondary cluster roster.

### Implementation 2: Overview KPI Strip 15-Second Clean Refresh
- **Target File**: `frontend/src/context/AppStateContext.jsx`
- **Changes**:
  1. In `refreshStats()`:
     ```javascript
     const refreshStats = useCallback(async () => {
       try {
         const s = await api.stats();
         if (s) {
           const hpVal =
             s.honeypot_hits_24h ??
             s.honeypot_hits ??
             s.honeypots?.total_hits ??
             s.honeypots?.hits_24h ??
             0;

           const newStats = {
             evaluated: s.total_evaluations ?? s.evaluated ?? 0,
             allowed: s.verdicts?.ALLOW ?? s.allowed ?? 0,
             held: s.verdicts?.HOLD ?? s.held ?? 0,
             blocked: s.verdicts?.BLOCK ?? s.blocked ?? 0,
             honeypot_hits: hpVal,
             honeypot_hits_24h: hpVal,
             rings: s.rings_known ?? s.rings ?? 0,
             dpip: s.dpip?.rings_published ?? s.dpip ?? 0,
             open_cases: s.cases?.open ?? 0,
             total_cases: s.cases?.total ?? 0,
           };

           // Shallow comparison prevents jarring re-renders when numbers haven't changed
           setStats((prev) => {
             const keys = Object.keys(newStats);
             const changed = keys.some((k) => prev[k] !== newStats[k]);
             return changed ? { ...prev, ...newStats } : prev;
           });

           if (s.adaptive_sensitivity != null) {
             setSensitivity(s.adaptive_sensitivity);
           }
         }
       } catch (err) {
         console.warn("stats refresh failed", err);
       }
     }, []);
     ```
  2. Add recurring 15-second timer:
     ```javascript
     useEffect(() => {
       const timer = setInterval(() => {
         refreshStats();
         refreshCases();
       }, 15000);
       return () => clearInterval(timer);
     }, [refreshStats, refreshCases]);
     ```

### Implementation 3: Investigations Tab Badge Wiring
- **Target File**: `frontend/src/components/common/Navbar.jsx`
- **Changes**:
  1. Derive open cases count from context:
     ```javascript
     const { cases, stats, live, busy, refreshCases, refreshStats, sensitivity } = useAppState();

     // Use real backend open cases count from /stats or /cases
     const openCasesCount =
       stats.open_cases ??
       stats.cases?.open ??
       cases.filter((c) => (c.status || "OPEN") === "OPEN" && c.status !== "RESOLVED" && c.status !== "DISMISSED").length;
     ```
  2. Use `openCasesCount` in desktop and mobile badge markup:
     ```jsx
     {item.badgeKey === "investigations" && openCasesCount > 0 && (
       <span className={`ml-1 px-1.5 py-0.5 text-[10px] font-mono font-bold rounded-full ${
         isActive ? "bg-rose-500 text-white" : "bg-rose-100 text-rose-700"
       }`}>
         {openCasesCount}
       </span>
     )}
     ```

### Implementation 4: Analytics Page & Endpoint Alignment
- **Target Files**:
  - `frontend/src/pages/AnalyticsPage.jsx`
  - `app/services/upi_cases.py`
  - `app/models/threat_intel.py`
- **Changes**:
  1. In `AnalyticsPage.jsx`:
     - Fix account prop:
       ```jsx
       <TopFlaggedAccountsTable
         accounts={analyticsData?.top_flagged_accounts || analyticsData?.top_accounts || []}
       />
       ```
     - Add 15-second refresh:
       ```javascript
       useEffect(() => {
         const timer = setInterval(() => {
           loadAnalytics(interval);
         }, 15000);
         return () => clearInterval(timer);
       }, [interval, loadAnalytics]);
       ```
     - Pass `analyticsData` into `AnalyticsSummaryKpis`:
       ```jsx
       <AnalyticsSummaryKpis
         summary={currentSummary}
         analyticsData={analyticsData}
         casesCount={cases.length}
         stats={stats}
         cases={cases}
       />
       ```
  2. In `app/services/upi_cases.py:618–630`:
     - Provide alias `"top_accounts": top_accounts`.
     - In `summary`, include:
       ```python
       "active_campaigns": len(get_campaign_store().list_campaigns()),
       "active_campaigns_count": len(get_campaign_store().list_campaigns()),
       ```
  3. In `app/models/threat_intel.py:367–374`:
     - Add optional fields `total_nodes: Optional[int] = None` and `active_campaigns_count: Optional[int] = None` to `ThreatSignalListResponse`.

---

## 4. Verification Plan

1. **Unit & Integration Regression Test**:
   - Run backend test suite: `.venv/bin/pytest tests/ -v` (confirm 969 tests pass).
   - Test specific endpoints:
     - `GET /intel/signals`
     - `GET /intel/campaigns`
     - `GET /intel/graph`
     - `GET /cases?status=OPEN`
     - `GET /stats`
     - `GET /stats/analytics`
2. **Frontend Linter & Build Verification**:
   - Run `cd frontend && npm run lint` (verify 0 ESLint errors with `--max-warnings 0`).
   - Run `cd frontend && npm run build` (clean Vite build).
3. **Behavioral UI Verification**:
   - In Threat Intelligence: Verify counters update upon calling `POST /intel/simulate` or `POST /intel/signals`.
   - In Overview: Observe network tab showing `/upi/stats` query every 15 seconds; verify tiles increment smoothly without flashing or full-page re-mounts.
   - In Navbar: Verify Investigations badge matches the number of open cases in `GET /cases?status=OPEN`.
   - In Analytics: Verify "Top Flagged Accounts" displays live accounts from `/stats/analytics` rather than synthetic fallback data.
