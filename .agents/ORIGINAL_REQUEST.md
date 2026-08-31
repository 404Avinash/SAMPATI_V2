# Original User Request

## 2026-08-31T05:50:22Z

# SAMPATI V2 — Sprint 2 Continuation (M2–M5)

SAMPATI V2 is a UPI fraud detection platform. **Milestone 1 is already complete** — the backend risk engine has been extended with DMV Score (`app/engine/dmv.py`), Campaign Fingerprinting (`app/engine/campaign.py`), and three new device-telemetry scoring rules (SIM-Device Mismatch, Impossible Travel, Datacenter IP) in `app/engine/upi_rules.py`. These changes are in the working tree but not yet committed.

**This task is to build the remaining three backend features and all frontend dashboard changes, then commit everything together.** The exact API contracts for every feature are already defined in `tests/test_sprint2_e2e_suite.py` — the team must make all 18 currently-failing tests pass without breaking any of the 92 already-passing tests in that file or any of the original 559 tests.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: demo

## Current State

Run `.venv/bin/pytest tests/test_sprint2_e2e_suite.py --tb=no -q` to see the 18 failing tests. They all fall into exactly 4 areas:

### Area 1 — SAR PDF Export (tests 26, 27, 28, 29, 31)
Tests expect `GET /cases/{case_id}/sar/pdf` AND `GET /upi/cases/{case_id}/sar/pdf` to return HTTP 200 with `Content-Type: application/pdf`. The existing SAR generation code is in `app/services/upi_cases.py` (`generate_upi_sar()`) and already produces a text narrative and a ring PNG. The endpoint must render this into a real PDF binary. Use `reportlab` (already in the Python environment at `.venv`) — do NOT use WeasyPrint.

### Area 2 — Workload Heatmap (tests 32, 36)
Tests expect `/upi/stats/analytics` (and `/stats/analytics`) to include a `workload_heatmap` key in the response. The heatmap must be a 7×24 grid (day_of_week 0..6 × hour 0..23) counting flagged case volume from the last 30 days. The cases are already tracked in `UpiCaseService._cases`. Add `workload_heatmap` to the `AnalyticsResponse` model and populate it from in-memory case data.

### Area 3 — Live Auto-Feed Engine (tests 37, 38, 39, 41, b05, c04, c07, scenario 4, 5)
Tests expect three new endpoints on the UPI router:
- `POST /upi/autofeed/start` — accepts `{rate_tps: float, fraud_ratio: float, bursty: bool}`, starts a background async loop, returns `{status: "started"|"already_running", active: True, rate_tps: float}`
- `GET /upi/autofeed/status` — returns `{active: bool, rate_tps: float, txns_generated: int, ...}`
- `POST /upi/autofeed/stop` — stops the loop, returns `{status: "stopped"|"not_running", active: False}`

The background loop must call the existing `UpiCaseService.evaluate()` pipeline and broadcast results via the existing WebSocket `broadcast_event()`. It must be idempotent (double start → `already_running`, double stop → `not_running`). It must be stoppable cleanly. Max allowed TPS is 50.

### Area 4 — Scoring Fix (test b02 and tests that cascade from it)
A transaction with `amount=10_000_000` and `payer_account_age_days=1` currently returns `ALLOW` but tests expect `HOLD` or `BLOCK`. The existing `NEW_ACCOUNT_HIGH_VALUE` rule fires for amounts ≥ 10,000 but scores too few points for mega-transfers. Add escalating risk points for very large amounts on new accounts (e.g., amounts ≥ 100,000 on a fresh account should push score ≥ 45).

## Requirements

### R1. SAR PDF Endpoint
Implement `GET /cases/{case_id}/sar/pdf` (and mirror at `/upi/cases/{case_id}/sar/pdf`) returning a valid PDF binary of the case's Suspicious Activity Report, including narrative text and ring member list. Use reportlab. Return 404 for unknown case IDs.

### R2. Workload Heatmap in Analytics
Add `workload_heatmap` to the analytics API response — a 7×24 grid (7 days × 24 hours) of flagged case volume from the last 30 days. Populate from in-memory case data.

### R3. Live Auto-Feed Engine
Implement three endpoints (`POST /upi/autofeed/start`, `GET /upi/autofeed/status`, `POST /upi/autofeed/stop`) backed by an async background loop that continuously generates and evaluates synthetic UPI transactions through the live pipeline and broadcasts events via WebSocket. Must be idempotent and cleanly stoppable.

### R4. Frontend Dashboard Updates
Update the React frontend:
- **CaseDrawer**: Add a DMV Score gauge (green < 40, amber 40–70, red > 70) reading `dmv_score` from case data
- **Analytics Page**: Add "Top VPAs by DMV Score" table using existing `/upi/stats/analytics` or `/upi/analytics/dmv/top` endpoint (add endpoint if needed)
- **Analytics Page**: Add the 7×24 workload heatmap visualization using `workload_heatmap` from the analytics response
- **Overview / ControlBar**: Add a Live Auto-Feed toggle button that calls `/upi/autofeed/start` and `/upi/autofeed/stop`
- **"Export SAR" button** in CaseDrawer that downloads from `/cases/{case_id}/sar/pdf`

### R5. Commit Everything
After all tests pass, commit all changes (M1 engine work + M2–M5) in a single well-structured commit. Then run the full original suite to verify zero regressions: `.venv/bin/pytest tests/ -v --ignore=tests/test_sprint2_e2e_suite.py` — must stay at 559 passed. Then run the sprint2 suite: `.venv/bin/pytest tests/test_sprint2_e2e_suite.py -v` — must be 0 failures. Then build the frontend: `cd frontend && npm run build`.

## Verification Resources

The test file `tests/test_sprint2_e2e_suite.py` is the ground truth for acceptance. Do not modify this file. Make the code pass the tests.

Currently failing (18 tests):
- TestTier1Feature6SarPdfExport: test_26, test_27, test_28, test_29, test_31
- TestTier1Feature7WorkloadHeatmap: test_32, test_36
- TestTier1Feature8AutoFeedEngine: test_37, test_38, test_39, test_41
- TestTier2BoundaryAndEdgeCases: test_tier2_b02, test_tier2_b05
- TestTier3CrossFeatureCombinations: test_tier3_c04, test_tier3_c07
- TestTier4RealWorldScenarios: test_scenario_1, test_scenario_4, test_scenario_5

## Acceptance Criteria

### Backend (programmatic — run the test suite)
- [ ] `.venv/bin/pytest tests/test_sprint2_e2e_suite.py -v` → 0 failures (all 110 tests pass)
- [ ] `.venv/bin/pytest tests/ --ignore=tests/test_sprint2_e2e_suite.py -q` → 559 passed, 0 failures

### Frontend
- [ ] `cd frontend && npm run build` → 0 errors, clean build

### Commit
- [ ] `git log --oneline -1` shows a new commit on main with all Sprint 2 changes
