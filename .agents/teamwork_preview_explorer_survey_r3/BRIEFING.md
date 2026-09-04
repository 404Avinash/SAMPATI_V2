# BRIEFING — 2026-09-03T20:20:00Z

## Mission
Investigate R3: Mobile App Push Notification System (FCM Integration) & End-to-End Latency Benchmarking for SAMPATI V2.

## 🔒 My Identity
- Archetype: explorer
- Roles: survey, analysis, synthesis
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r3
- Original parent: dcfa3ce2-0d8a-4c92-b530-f081ee91ac86
- Milestone: Survey & Investigation for R3 FCM Integration & Latency Benchmarking

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Work only inside working directory (.agents/teamwork_preview_explorer_survey_r3/)
- Ensure compatibility with existing 902+ tests, ruff, and frontend builds
- Deliver findings in handoff.md

## Current Parent
- Conversation ID: dcfa3ce2-0d8a-4c92-b530-f081ee91ac86
- Updated: 2026-09-03T20:15:37Z

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`, `AGENTS.md`, `pyproject.toml`, `requirements.txt`
  - `app/main.py`, `app/api/upi.py`, `app/api/intel.py`, `app/services/upi_cases.py`, `app/services/threat_intel_service.py`
  - `tests/test_threat_intel_r1.py`, `tests/test_isolation_forest.py`, `tests/test_adversarial_m1.py`, `tests/test_sprint2_e2e_suite.py`
- **Key findings**:
  - Existing suite passes 902/902 tests (100% green in ~118s).
  - Ruff check passes with 0 errors.
  - Frontend builds cleanly in 12s with 0 ESLint warnings (`--max-warnings 0`).
  - `firebase-admin` is NOT in `requirements.txt` or `.venv`. Integration must use lightweight HTTP v1 FCM client (via existing `httpx`) with a robust `MockFcmProvider` fallback.
  - Device token registration endpoint `POST /notifications/register` requires thread-safe storage, deduplication, and platform/vpa metadata.
  - Two key trigger points: (1) `POST /intel/signals` with `severity in ("HIGH", "CRITICAL")`, and (2) `POST /upi/check` or case evaluation with verdict `BLOCK`.
  - Notification payload structure: `risk_score`, `verdict`, and `top_reason` (plus title, body, and forensic metadata).
  - End-to-end latency benchmark design: local execution runs in 2-15ms, easily satisfying the < 500ms SLA with full percentile metrics (p50, p95, p99).
- **Unexplored areas**: None. All objectives for R3 surveyed and verified.

## Key Decisions Made
- Recommended architectural separation: `app/services/notification_service.py` (models, token store, FCM provider abstraction) and `app/api/notifications.py` (FastAPI router).
- Selected dual-mode FCM provider: Mock provider by default for hermetic tests/local demo, HTTP v1 client when credentials are provided.
- Defined notification payload contract explicitly matching user requirements (`risk_score`, `verdict`, `top_reason`).
- Benchmark test architecture designed to run 50-100 iterations measuring both `POST /intel/signals` and `POST /upi/check`.

## Artifact Index
- DISPATCH.md — Dispatch instructions
- BRIEFING.md — Situational awareness
- progress.md — Liveness heartbeat
- handoff.md — Comprehensive 5-component survey & investigation report
