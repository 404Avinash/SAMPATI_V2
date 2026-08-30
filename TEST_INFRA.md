# E2E Test Infra: SAMPATI V2 Federated Fraud Intelligence Mesh

## Test Philosophy
- Opaque-box, requirement-driven, and regression-free.
- Target: 100% pass on baseline (492 tests) + comprehensive coverage across Tiers 1-5 for new features.

## Feature Inventory & Test Matrix
| # | Feature | Requirement | Tier 1 (Unit) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (E2E Scenarios) | Tier 5 (Adversarial) |
|---|---------|-------------|:-------------:|:-----------------:|:-----------------:|:----------------------:|:--------------------:|
| 1 | POST /federation/signal | R2 | 5 | 5 | ✓ | ✓ | ✓ |
| 2 | GET /federation/query | R2 | 5 | 5 | ✓ | ✓ | ✓ (<5ms latency) |
| 3 | Dynamic network_score in /upi/check | R2 | 5 | 5 | ✓ | ✓ | ✓ |
| 4 | Seeded Honeypot VPA Registry | R3 | 5 | 5 | ✓ | ✓ | ✓ |
| 5 | R_HONEYPOT_HIT Rule & BLOCK Verdict | R3 | 5 | 5 | ✓ | ✓ | ✓ |
| 6 | Honeypot Hit Tracking & Stats API | R3 | 5 | 5 | ✓ | ✓ | ✓ |
| 7 | Timeline Controls & Step Animation | R1 | 5 | 5 | ✓ | ✓ | ✓ |
| 8 | Honeypot KPI Strip Tile | R3 | 5 | 5 | ✓ | ✓ | ✓ |

## Test Architecture
- Master Runner: `.venv/bin/python3 tests/test_e2e_suite.py`
- Pytest Suite: `.venv/bin/pytest tests/ -v`
- Frontend Build: `cd frontend && npm run build` or `bun run build`
- Frontend Contracts: `.venv/bin/pytest tests/frontend_contracts_test.py -v`

## Coverage Thresholds
- Baseline: 492 existing tests passing with 0 regressions.
- New test cases: >= 30 new unit and integration tests across Federation, Honeypot, and Timeline features.
- Performance SLA: GET `/federation/query` responds in < 5ms for cached keys.
