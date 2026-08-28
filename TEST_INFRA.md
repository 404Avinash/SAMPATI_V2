# SAMPATI V2 — End-to-End Test Infrastructure & Verification Architecture

## 1. Test Philosophy & Architecture

SAMPATI V2 is a real-time UPI switch-level mule-network fraud interception platform. The E2E test suite adheres to an **opaque-box, behavior-driven testing methodology** that verifies the system across four rigorous tiers plus adversarial stress verification.

```
+-----------------------------------------------------------------------------------+
|                           SAMPATI V2 E2E TEST MATRIX                              |
+-----------------------------------------------------------------------------------+
| Tier 1: Feature Isolation Coverage (F1 - F15)                                     |
|   -> 15 features x >= 5 tests = >= 75 tests verifying primary contracts & happy paths|
+-----------------------------------------------------------------------------------+
| Tier 2: Boundary, Extreme Values & Negative Resilience (F1 - F15)                 |
|   -> 15 features x >= 5 tests = >= 75 tests verifying limits, errors & corner cases  |
+-----------------------------------------------------------------------------------+
| Tier 3: Cross-Feature Integration Pipelines                                       |
|   -> End-to-end flows: Check -> Scoring -> DB -> WebSocket -> Stats -> SAR -> DPIP  |
+-----------------------------------------------------------------------------------+
| Tier 4: Real-World Fraud Scenarios & High-Concurrency Resilience                   |
|   -> Multi-hop mule rings, 500-txn bursts, analyst feedback loops, reboot recovery |
+-----------------------------------------------------------------------------------+
```

---

## 2. Feature Coverage Matrix (F1 through F15)

| Feature ID | Feature Name | Tier 1 (Isolation) | Tier 2 (Boundary) | Tier 3 (Integration) | Tier 4 (Scenario) | Target Scope |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **F1** | RDS PostgreSQL Persistence Models | 6 tests | 6 tests | Yes | Yes | `app/models/upi_persistence.py` |
| **F2** | Connection Pooling & Auto-Migration | 5 tests | 5 tests | Yes | Yes | `app/db/session.py`, `app/main.py` |
| **F3** | Database-Backed Case & Stats APIs | 6 tests | 6 tests | Yes | Yes | `app/api/upi.py` (`/cases`, `/stats`) |
| **F4** | Dependency & Deployment Packaging | 5 tests | 5 tests | Yes | Yes | `requirements.txt`, `Dockerfile`, `deploy/` |
| **F5** | WebSocket Broadcast Hub | 6 tests | 6 tests | Yes | Yes | `app/api/websocket.py` (`ConnectionManager`) |
| **F6** | Transaction & Case Event Emitters | 5 tests | 5 tests | Yes | Yes | `app/services/upi_cases.py`, `app/api/upi.py` |
| **F7** | Frontend WebSocket Hook & Stream | 5 tests | 5 tests | Yes | Yes | `frontend/src/hooks/useWebSocket.js` |
| **F8** | Reactive KPI Counters | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/KpiStrip.jsx` |
| **F9** | Interactive Constellation Hit Detection | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/NetworkConstellation.jsx` |
| **F10** | Node Tooltip & Role Tagging | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/NetworkConstellation.jsx` |
| **F11** | Constellation Click-to-Case Drawer | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/CaseDrawer.jsx` |
| **F12** | Continuous Risk-Score Edge Gradient | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/NetworkConstellation.jsx` |
| **F13** | Transaction Amount Tooltip on Hover | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/NetworkConstellation.jsx` |
| **F14** | Verdict History Recharts Component | 5 tests | 5 tests | Yes | Yes | `frontend/src/components/VerdictHistoryChart.jsx` |
| **F15** | Dashboard Layout & History Ingestion | 5 tests | 5 tests | Yes | Yes | `frontend/src/App.jsx` |
| **Total** | **All 15 Features** | **79 tests** | **79 tests** | **7 suites** | **5 scenarios** | **170+ Executable Tests** |

---

## 3. Test Suite Structure & Layout

All test implementations are stored under `tests/`:

```
tests/
├── test_e2e_suite.py          # Master CLI test runner & orchestrator
├── test_tier1_features.py     # Tier 1: Feature isolation tests (F1 - F15)
├── test_tier2_boundary.py     # Tier 2: Boundary & negative tests (F1 - F15)
├── test_tier3_combinations.py # Tier 3: Cross-feature integration pipelines
├── test_tier4_scenarios.py    # Tier 4: Production fraud scenarios & reboot recovery
└── frontend_contracts_test.py # Frontend AST, JSX, and visualizer mathematical contract verifications
```

---

## 4. Execution Commands

### 4.1 Master Self-Contained Test Runner (Zero-Dependency Async Runner)
```bash
# Run entire test suite across all 4 tiers:
python tests/test_e2e_suite.py

# Run specific tier:
python tests/test_e2e_suite.py --tier 1
python tests/test_e2e_suite.py --tier 2
python tests/test_e2e_suite.py --tier 3
python tests/test_e2e_suite.py --tier 4

# Run specific feature filter:
python tests/test_e2e_suite.py --feature F1
python tests/test_e2e_suite.py --feature F12

# Run with verbose output and latency logs:
python tests/test_e2e_suite.py --verbose
```

### 4.2 Standard Pytest Invocation (if pytest is installed)
```bash
pytest tests/ -v
```

---

## 5. Verification Protocol & Quality Gates

Each test execution validates:
1. **Contract Invariants**: Return types, JSON schemas, status codes, and database foreign key integrity.
2. **Deterministic Outputs**: Compares against authoritative specifications in `PROJECT.md` and `ORIGINAL_REQUEST.md`.
3. **Performance Boundaries**: Ensures scoring latency is $< 10\text{ms}$ and WebSocket broadcast latency is $< 2.0\text{s}$.
4. **State Persistence**: Asserts that cases and aggregate stats survive simulated restarts with persistent storage.
