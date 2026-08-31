# E2E Test Infra: SAMPATI V2 Sprint 2

## Test Philosophy
- Opaque-box, requirement-driven testing. Derived strictly from `ORIGINAL_REQUEST.md`.
- Zero-tolerance for regressions: All existing 559 tests must remain 100% green.
- Multi-tier systematic coverage: Category-Partition (Tier 1), Boundary & Corner Cases (Tier 2), Combinations (Tier 3), Real-World Scenarios (Tier 4), and Adversarial Hardening (Tier 5).

## Feature Inventory & Test Mapping
| # | Feature | Source (Requirement) | Tier 1 (Isolation) | Tier 2 (Boundaries) | Tier 3 (Interactions) | Tier 4 (E2E Scenarios) |
|---|---------|----------------------|:------------------:|:-------------------:|:---------------------:|:----------------------:|
| 1 | Dead Money Velocity (DMV) Score | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | SIM-Device Mismatch Rule (`R_SIM_DEVICE_MISMATCH`) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 3 | Impossible Travel Rule (`R_IMPOSSIBLE_TRAVEL`) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 4 | Datacenter / VPN IP Rule (`R_DATACENTER_IP`) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 5 | Transaction DNA Campaign Fingerprinting (`R_CAMPAIGN_MATCH`) | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 6 | One-Click SAR PDF Export (`GET /cases/{case_id}/sar/pdf`) | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| 7 | Analyst Workload Heatmap (7x24 Grid) | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |
| 8 | Autonomous Live Auto-Feed Mode | ORIGINAL_REQUEST §R6 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Test runner: `./.venv/bin/pytest tests/ -v`
- Python linter: `./.venv/bin/ruff check app tests`
- Frontend lint: `cd frontend && npm run lint`
- Frontend build: `cd frontend && npm run build`
- Dedicated Sprint 2 Test Suite: `tests/test_sprint2_e2e_suite.py`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Dormant Mule Ring Drain & Campaign Clustering | DMV + Campaign DNA + Telemetry + SAR PDF | High |
| 2 | High-Speed Cross-City SIM-Swap Attack | SIM-Device Mismatch + Impossible Travel + Blocking | High |
| 3 | Cloud-Hosted Botnet Surge with Auto-Feed Live Rail | Datacenter IP + Live Auto-Feed + WebSocket + KPI Ticking | High |
| 4 | Enterprise Compliance Investigator Workflow | SAR PDF Export + 7x24 Heatmap + Top DMV Ranked Table | Medium |
| 5 | Clean Lifecycle & Invariant Defense | Auto-Feed Start/Stop + State Preservation + Zero Leaks | High |
