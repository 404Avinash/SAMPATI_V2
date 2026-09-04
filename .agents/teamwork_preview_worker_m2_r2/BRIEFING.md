# BRIEFING — 2026-09-04T03:31:30+05:30

## Mission
Implement Milestone 2 (R2): Simulated Institutional Signal Adapters (Mock NPCI MuleHunter, Mock DPIP Smart Registry, Mock PSP) & Frontend Dashboard Integration for SAMPATI V2.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2_r2/
- Original parent: dcfa3ce2-0d8a-4c92-b530-f081ee91ac86
- Milestone: M2 (R2)

## 🔒 Key Constraints
- Exclusive write ownership:
  - `app/models/threat_intel.py` (add `StandardFraudSignal`)
  - `app/models/upi_models.py` (add `mock_npci_score`, `mock_dpip_threat_level`, `contributing_signals` to `UpiEvaluationResponse`)
  - `app/adapters/` (new package: `__init__.py`, `npci.py`, `dpip.py`, `psp.py`, `service.py`)
  - `app/services/upi_cases.py` (populate institutional scores in `evaluate()`)
  - `app/api/adapters.py` (new router for adapter endpoints)
  - `app/main.py` (mount `adapters.router` at `/adapters` and `/upi/adapters`)
  - `frontend/src/components/CaseDrawer.jsx` (display institutional contributing signals)
  - `frontend/src/pages/ThreatIntelPage.jsx` (institutional badges & presets)
  - `frontend/src/components/LiveFeed.jsx` (institutional pill tags)
  - `frontend/src/services/api.js` (adapter API wrappers)
  - `tests/test_institutional_adapters.py` (new tests)
- DO NOT CHEAT: Genuine implementation, no hardcoding of test results or fake facades.
- All existing tests (923+) must pass.
- Ruff linter must pass with 0 errors.
- Frontend ESLint (--max-warnings 0) and build must pass cleanly.

## Current Parent
- Conversation ID: dcfa3ce2-0d8a-4c92-b530-f081ee91ac86
- Updated: 2026-09-04T03:31:30+05:30

## Task Summary
- **What to build**: Mock NPCI MuleHunter Adapter, Mock DPIP Smart Registry Adapter, Mock PSP Adapter, StandardFraudSignal schema, /upi/check integration, REST API endpoints, frontend dashboard integration, and comprehensive test suite.
- **Success criteria**: All tests pass (953 passed, 0 failures), ruff passes with 0 errors, frontend lint passes with 0 warnings, frontend build succeeds, deterministic high risk scores for honeypots / known-bad VPAs in /upi/check.
- **Interface contracts**: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md
- **Code layout**: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md § Code Layout

## Key Decisions Made
- Used in-memory data structures with deterministic hashing for sub-millisecond execution latency.
- Integrated with existing HoneypotRegistry and DPIP feeds for consistency.
- Added StandardFraudSignal to threat_intel.py inheriting from ThreatSignalCreateRequest.
- Mounted adapters router at both `/adapters` and `/upi/adapters` and whitelisted `/adapters` in SPA fallback 404 handler.
- Frontend displays detailed institutional breakdown in CaseDrawer, branded badges and presets in ThreatIntelPage, and pill tags in LiveFeed.

## Artifact Index
- /home/avi/Downloads/Sampati_v2/app/adapters/ - Adapter package (`npci.py`, `dpip.py`, `psp.py`, `service.py`, `__init__.py`)
- /home/avi/Downloads/Sampati_v2/app/api/adapters.py - REST API router
- /home/avi/Downloads/Sampati_v2/tests/test_institutional_adapters.py - Test suite (19 tests)

## Change Tracker
- **Files modified**:
  - `app/models/threat_intel.py`: Added `StandardFraudSignal(ThreatSignalCreateRequest)` with factory methods
  - `app/models/upi_models.py`: Added `mock_npci_score`, `mock_dpip_threat_level`, `contributing_signals` to `UpiEvaluationResponse`
  - `app/adapters/`: Created adapter package with NPCI, DPIP, PSP, and coordination service
  - `app/services/upi_cases.py`: Integrated institutional adapter evaluation in `evaluate()`, `_open_case()`, and `format_case_payload()`
  - `app/api/adapters.py`: Created REST API router for institutional adapters
  - `app/main.py`: Mounted adapters router at `/adapters` and `/upi/adapters`
  - `frontend/src/services/api.js`: Added adapter API wrappers
  - `frontend/src/components/CaseDrawer.jsx`: Added Institutional Contributing Signals card
  - `frontend/src/pages/ThreatIntelPage.jsx`: Added branded institution badges and presets
  - `frontend/src/components/LiveFeed.jsx`: Added institutional pill tags in Signals column
  - `tests/test_institutional_adapters.py`: Created 19 comprehensive unit and integration tests
- **Build status**: PASS (953 tests passed, ruff clean, frontend lint clean, frontend build clean)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 953 passed, 0 failures in 157.89s
- **Lint status**: 0 violations (ruff check clean, ESLint --max-warnings 0 clean)
- **Tests added/modified**: 19 new tests in `tests/test_institutional_adapters.py`

## Loaded Skills
- **Source**: /home/avi/Downloads/Sampati_v2/.agents/skills/safe-push/SKILL.md
- **Local copy**: /home/avi/Downloads/Sampati_v2/.agents/skills/safe-push/SKILL.md
- **Core methodology**: Automated safe push protocol: pytest + ruff + frontend lint + frontend build before git push.
