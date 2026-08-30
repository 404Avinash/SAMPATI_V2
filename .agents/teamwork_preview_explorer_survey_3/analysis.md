# Comprehensive Test Suite Architecture & Verification Strategy (SAMPATI V2)

**Explorer 3 Investigation Report**  
**Working Directory:** `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3`  
**Target Platform:** SAMPATI V2 UPI Mule-Network Interception & Federated Intelligence Mesh  
**Timestamp:** 2026-08-31T00:58:00Z  

---

## 1. Executive Summary

This investigation analyzed the SAMPATI V2 test infrastructure, test runner architecture, mock dependencies, and verification strategy across all 5 testing tiers (492 existing tests). It establishes a zero-regression baseline and formulates a complete, executable verification plan for the three upcoming features:
1. **R1: Fraud Playback Timeline** (Frontend animated graph reconstruction on `NetworkConstellation`)
2. **R2: Federation Signal Exchange API** (`POST /federation/signal`, `GET /federation/query`, sub-5ms cache latency, dynamic `network_score`)
3. **R3: VPA Honeypot Network** (Seeded honeypot traps, `R_HONEYPOT_HIT` rule, mandatory `BLOCK` verdict, hit counters, and KPI telemetry)

---

## 2. Test Suite Architecture & Discovery Breakdown

### 2.1 Pytest & Runner Configuration
- **Configuration File:** `pyproject.toml`
  ```toml
  [tool.pytest.ini_options]
  minversion = "8.0"
  testpaths = ["tests"]
  python_files = ["test_*.py", "*_test.py"]
  ```
- **Linter:** `ruff` configured in `pyproject.toml` with line-length 120 and target Python 3.11.
- **Python Environment:** `.venv/bin/python3` (Python 3.14.4, pytest 9.1.1, pluggy 1.6.0, anyio 4.14.1).
- **Frontend Tooling:** `bun` (version 1.3.14) is installed in `/home/avi/.bun/bin/bun` and builds Vite/React production assets via `bun run build` in 6.67s.

### 2.2 Test Manifest & Inventory (492 Total Collected Tests)

| Test Module File | Test Count | Scope / Responsibility |
| :--- | :---: | :--- |
| `tests/test_tier1_features.py` | 78 | **Tier 1 (Isolation)**: Individual contracts for F1 through F15 |
| `tests/test_tier2_boundary.py` | 76 | **Tier 2 (Boundary)**: Negative inputs, extreme bounds, malformed payloads |
| `tests/test_tier3_combinations.py`| 7 | **Tier 3 (Integration Pipelines)**: 7 multi-hop end-to-end integration flows |
| `tests/test_tier4_scenarios.py` | 5 | **Tier 4 (Real Scenarios)**: Mule ring attacks, 500-txn bursts, reboot recovery |
| `tests/test_tier5_adversarial.py`| 20 | **Tier 5 (Adversarial Stress)**: Concurrency, geometry, connection pool churn |
| `tests/frontend_contracts_test.py`| 13 | AST & Mathematical Contracts: Hit testing, INR formatting, color gradients |
| `tests/test_analytics.py` | 7 | Analytics engine & `/stats/analytics` endpoint |
| `tests/test_case_status.py` | 6 | Case status lifecycle (`PATCH /cases/{case_id}/status`) |
| `tests/test_health_detailed.py` | 7 | System health telemetry (`GET /health/detailed`) |
| `tests/test_cicd_pipeline.py` | 12 | CI/CD pipeline structural invariants & GitHub Actions rules |
| `tests/test_m1_persistence.py` | 8 | Database persistence, schema migrations, fallback resilience |
| `tests/test_m2_websocket.py` | 10 | WebSocket event streaming, broadcast sync, connection manager |
| `tests/test_empirical_challenger.py`| 12 | Statistical empirical scoring verification |
| `tests/test_e2e_suite.py` | 231 | Master standalone async runner orchestrating Tiers 1–5 |
| **Total Test Inventory** | **492** | Complete verified collection |

### 2.3 Execution Modalities & Latency Profile
1. **Master Standalone Async Runner (`.venv/bin/python3 tests/test_e2e_suite.py`)**:
   - Executes 231 test cases across all tiers in **6.20s** with 100% pass rate (0 failures, 0 errors).
2. **Sub-Suite Pytest Invocation (`.venv/bin/pytest tests/test_tier1_features.py ...`)**:
   - Tiers 1–4 run 166 tests in **1.96s**.
   - Contract & unit tests run 75 tests in **2.54s**.
   - Tier 5 runs 20 tests in **6.38s**.

---

## 3. Mock Harness & Dependency Architecture (`tests/mock_env.py`)

The test infrastructure includes `tests/mock_env.py` (692 lines) providing a dual-mode execution environment:
1. **Production / Docker Mode:** Uses real installed libraries (`fastapi`, `pydantic`, `sqlalchemy.ext.asyncio`, `httpx`, `asyncpg`, `redis`).
2. **Fallback / Offline Mode:** Installs mock modules dynamically into `sys.modules` when external packages are omitted:
   - **`FastAPI` / `APIRouter`**: Mock routing table supporting `GET`, `POST`, `PATCH`, `WebSocket`.
   - **`AsyncSession` / `AsyncEngine`**: In-memory dictionary persistence (`_MOCK_DB_STORE`) simulating transactions, rollbacks, primary key lookups, and session commits.
   - **`httpx.AsyncClient`**: In-memory ASGI request dispatcher routing calls to `UpiCaseService`.

---

## 4. Verification Plan for R2: Federation Signal Exchange API

### 4.1 Feature Specifications
- **Write Endpoint (`POST /federation/signal` & `/upi/federation/signal`)**:
  - Accepts: `{ "vpa_hash": "<64-hex-sha256>", "risk_level": "HIGH" | 0.85, "ring_hash": "<optional_hash>" }`
  - Returns: HTTP 200 `{ "status": "ok", "vpa_hash": "...", "stored": true, "timestamp": "..." }`
- **Read Endpoint (`GET /federation/query?vpa_hash=<hash>` & `/upi/federation/query`)**:
  - Accepts query parameter `vpa_hash`
  - Returns: `{ "vpa_hash": "...", "federated_risk_score": 0.85, "ring_members": [...], "reported_by_nodes": ["PSP_HDFC", "PSP_AXIS"], "cached": true }`
  - **Latency Criterion:** Under 5ms (< 5.0ms) for cached queries.
- **Dynamic `network_score` in `/upi/check`**:
  - When evaluating a transaction, compute SHA-256 of `payee_vpa` and `payer_vpa`.
  - Look up federated risk signal from hot cache.
  - If a signal exists, dynamically populate `network_score` in `UpiEvaluationResponse` (non-zero, e.g. 0.85).
  - Risk score increases accordingly and verdict elevates to `HOLD` or `BLOCK`.

### 4.2 Multi-Tier Test Cases

```
+----------------------------------------------------------------------------------------------------+
|                                    R2 VERIFICATION TEST MATRIX                                     |
+----------------------------------------------------------------------------------------------------+
| Tier 1: Feature Isolation                                                                          |
|   - test_r2_01_signal_submission_success (POST /federation/signal returns 200)                     |
|   - test_r2_02_signal_query_cached_response (GET /federation/query returns score & nodes)          |
|   - test_r2_03_signal_query_unknown_vpa_hash (Returns neutral/default score without 500)          |
|   - test_r2_04_dynamic_network_score_in_upi_check (network_score > 0 populated in /upi/check)     |
|   - test_r2_05_cache_latency_sub_5ms (100 cached queries executed with p99 < 5.0ms)                |
+----------------------------------------------------------------------------------------------------+
| Tier 2: Boundary, Negative & Resilience                                                            |
|   - test_r2_b01_malformed_vpa_hash_rejection (Non-hex, length != 64 handled gracefully)           |
|   - test_r2_b02_missing_vpa_hash_param (GET /federation/query without param returns 422)           |
|   - test_r2_b03_risk_level_normalization (Strings "CRITICAL", "LOW", floats 0.0-1.0 normalized)   |
|   - test_r2_b04_multi_node_signal_aggregation (Signals from multiple PSPs merged cleanly)         |
|   - test_r2_b05_redis_fallback_to_in_memory (Cache operations continue when Redis offline)        |
+----------------------------------------------------------------------------------------------------+
| Tier 3: Cross-Feature Integration                                                                  |
|   - test_r2_pipe_signal_to_scoring_to_ws_event (Signal -> Check -> Case -> WebSocket broadcast)     |
+----------------------------------------------------------------------------------------------------+
| Tier 4: Real-World Scenario                                                                        |
|   - test_r2_scenario_federated_mule_ring_quarantine (Multi-PSP syndicate blocked via signal mesh)  |
+----------------------------------------------------------------------------------------------------+
| Tier 5: Adversarial Stress                                                                         |
|   - test_r2_adv_high_throughput_signal_burst (10,000 signal writes and queries under concurrency)  |
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Verification Plan for R3: VPA Honeypot Network

### 5.1 Feature Specifications
- **Seeded Honeypot Registry**:
  - Registry of synthetic honeypot VPAs (e.g. `honeypot.trap.01@okaxis`, `phish.mule.trap@ybl`, `scam.bait.03@paytm`, `mule.honeypot.99@oksbi`, `scam.honeypot@okhdfcbank`).
- **Rule `R_HONEYPOT_HIT`**:
  - Triggered whenever `payee_vpa` (or `payer_vpa`) matches a registered honeypot.
  - Adds 100 risk points (clamped to 100).
  - Verdict is guaranteed `BLOCK`.
  - `reasons` list in `UpiEvaluationResponse` includes `"R_HONEYPOT_HIT"`.
  - `rule_breakdown` includes `RuleHit(code="R_HONEYPOT_HIT", points=100, detail="...")`.
- **Hit Tracking & Telemetry**:
  - Tracks hit count and last-hit timestamp per honeypot VPA.
  - Telemetry surfaced in `/upi/stats`, `/stats/analytics`, and/or `/upi/honeypot/stats` (`honeypot_hits_24h` / `honeypots`).
  - Overview dashboard page displays reactive "Honeypot Hits (24h)" KPI counter.

### 5.2 Multi-Tier Test Cases

```
+----------------------------------------------------------------------------------------------------+
|                                    R3 VERIFICATION TEST MATRIX                                     |
+----------------------------------------------------------------------------------------------------+
| Tier 1: Feature Isolation                                                                          |
|   - test_r3_01_honeypot_registry_seed_validation (Pre-seeded VPAs present and indexed)            |
|   - test_r3_02_honeypot_transaction_block_verdict (Txn to honeypot returns BLOCK and score 100)    |
|   - test_r3_03_reasons_contain_r_honeypot_hit (R_HONEYPOT_HIT in reasons list and rule breakdown)  |
|   - test_r3_04_hit_count_and_timestamp_update (Hit counter increments and ISO timestamp updates)   |
|   - test_r3_05_honeypot_kpi_stats_reporting (honeypot_hits_24h returned in /upi/stats)            |
+----------------------------------------------------------------------------------------------------+
| Tier 2: Boundary, Negative & Resilience                                                            |
|   - test_r3_b01_case_insensitivity_and_whitespace (Mixed case and spaces matched correctly)        |
|   - test_r3_b02_legitimate_vpa_non_trigger (Clean VPAs never trigger R_HONEYPOT_HIT)               |
|   - test_r3_b03_zero_amount_honeypot_probe (Micro-transactions still trigger mandatory BLOCK)     |
|   - test_r3_b04_payer_vpa_honeypot_probe (Compromised account probes handled securely)             |
|   - test_r3_b05_consecutive_hit_counter_integrity (50 successive hits count exactly 50)           |
+----------------------------------------------------------------------------------------------------+
| Tier 3: Cross-Feature Integration                                                                  |
|   - test_r3_pipe_honeypot_to_case_persistence_and_kpi (Honeypot hit -> Case in DB -> KPI updated)  |
+----------------------------------------------------------------------------------------------------+
| Tier 4: Real-World Scenario                                                                        |
|   - test_r3_scenario_syndicate_honeypot_probing_detection (Syndicate probing triggers alerts)       |
+----------------------------------------------------------------------------------------------------+
| Tier 5: Adversarial Stress                                                                         |
|   - test_r3_adv_high_concurrency_honeypot_flood (Atomic thread-safe counting under 1,000 threads)  |
+----------------------------------------------------------------------------------------------------+
```

---

## 6. Verification Plan for R1: Fraud Playback Timeline

### 6.1 Feature Specifications
- **Component:** `frontend/src/components/constellation/NetworkConstellation.jsx`
- **Interactive UI Controls:**
  - Range Slider (`<input type="range" ...>`) allowing scrubbing across transaction timestamps.
  - Play Button: Animates edges and connected nodes onto canvas in chronological timestamp order.
  - Pause Button: Freezes animation at current timestamp/step.
  - Reset Button: Resets timeline to $t=0$, returning graph to initial state.
  - Usable per-case in `CaseDrawer` when case topology is loaded.
- **Frontend Verification Method:**
  - AST / regex structural contract testing in `tests/frontend_contracts_test.py`.
  - Mathematical projection and chronological sort validation.
  - Production build verification via `cd frontend && bun run build`.

### 6.2 Multi-Tier Test Cases

```
+----------------------------------------------------------------------------------------------------+
|                                    R1 VERIFICATION TEST MATRIX                                     |
+----------------------------------------------------------------------------------------------------+
| Tier 1: AST & Mathematical Contracts                                                               |
|   - test_r1_01_network_constellation_timeline_ast (Slider, Play, Pause, Reset in JSX AST)          |
|   - test_r1_02_timeline_playback_state_variables (isPlaying, playbackTime, currentStep defined)    |
|   - test_r1_03_chronological_edge_sorting_math (Edges sorted strictly by timestamp ascending)     |
|   - test_r1_04_timeline_frame_filtering_logic (Only edges with t_edge <= t_current rendered)      |
|   - test_r1_05_case_drawer_timeline_integration (Case topology passed to constellation timeline)   |
+----------------------------------------------------------------------------------------------------+
| Tier 2: Boundary & Corner Cases                                                                    |
|   - test_r1_b01_empty_topology_playback_graceful (0 edges does not throw TypeError or crash)      |
|   - test_r1_b02_single_transaction_timeline (1 edge handles range [0, 1] without division by 0)   |
|   - test_r1_b03_identical_timestamps_batch (Simultaneous edges render without NaN)                 |
|   - test_r1_b04_disordered_timestamps_resilience (Unordered transactions sorted correctly)         |
|   - test_r1_b05_reset_invariants (Reset returns progress to 0 and clears animation timer)         |
+----------------------------------------------------------------------------------------------------+
| Tier 3: Integration Invariants                                                                     |
|   - test_r1_pipe_case_detail_to_constellation_topology (Topology timestamps match txn stream)      |
|   - test_r1_pipe_progress_to_timestamp_interpolation (Linear mapping ratio * (t_max - t_min))     |
+----------------------------------------------------------------------------------------------------+
| Tier 4: Real-World Fraud Scenario                                                                  |
|   - test_r1_scenario_mule_ring_cinematic_playback (Multi-hop ring reveals hops in causal sequence) |
+----------------------------------------------------------------------------------------------------+
| Tier 5: Adversarial Math & Production Build                                                        |
|   - test_r1_adv_spatial_hit_testing_during_playback (Hit detection maintains precision while active)|
|   - test_r1_adv_frontend_production_build_clean (bun run build exits 0 with complete dist output)  |
+----------------------------------------------------------------------------------------------------+
```

---

## 7. Potential Pitfalls, Performance Criteria & Regression Safeguards

### 7.1 Identified Pitfalls & Mitigation Strategies

1. **Pytest Duplicate Collection Overlap**:
   - *Observation:* `tests/test_e2e_suite.py` imports classes from individual test files, leading pytest to collect 231 tests from `test_e2e_suite.py` and 231 from standalone modules (total 492).
   - *Mitigation:* Ensure all test cases are strictly stateless, using unique IDs and clean tear-downs (`asyncTearDown`) so executing tests repeatedly produces 0 cross-test side effects.

2. **Adversarial Timing Threshold Contention**:
   - *Observation:* In `tests/test_tier5_adversarial.py`, `test_07_high_density_canvas_graph_node_and_edge_hit_testing` computes 1,000,000 point-to-segment distance calculations. In heavy concurrent pytest runs, execution may reach ~2.9s vs a strict 2.0s limit.
   - *Mitigation:* Calibrate performance thresholds to accommodate varying CI runner CPU capacities without sacrificing rigorous correctness checks.

3. **Federation Hash Case & Salt Standardization**:
   - *Observation:* VPA strings could have varying case (`Alice@OkAxis` vs `alice@okaxis`).
   - *Mitigation:* Always compute SHA-256 over `vpa.strip().lower().encode("utf-8")`.

4. **Honeypot Thread Safety**:
   - *Observation:* Concurrent requests hitting honeypots must not lose counter increments.
   - *Mitigation:* Use atomic thread-safe structures or `threading.Lock()` for the honeypot hit tracking registry.

5. **Sub-5ms Cache Latency Guarantee**:
   - *Observation:* Federation query must be served under 5ms.
   - *Mitigation:* Store query payloads directly in-memory / Redis hot cache as pre-serialized JSON or dictionaries, avoiding DB round-trips on query path.

---

## 8. Verification Strategy & Commands

1. **Full Pytest Execution**:
   ```bash
   .venv/bin/pytest tests/ -v
   ```
2. **Master Standalone Test Runner**:
   ```bash
   .venv/bin/python3 tests/test_e2e_suite.py
   ```
3. **Targeted Tier Execution**:
   ```bash
   .venv/bin/python3 tests/test_e2e_suite.py --tier 1
   .venv/bin/python3 tests/test_e2e_suite.py --tier 2
   .venv/bin/python3 tests/test_e2e_suite.py --tier 3
   .venv/bin/python3 tests/test_e2e_suite.py --tier 4
   .venv/bin/python3 tests/test_e2e_suite.py --tier 5
   ```
4. **Frontend Production Build**:
   ```bash
   cd frontend && bun run build
   ```
