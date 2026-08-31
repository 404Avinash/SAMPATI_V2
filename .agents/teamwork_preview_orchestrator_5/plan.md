# Plan — SAMPATI V2 Sprint 2

## Objective
Implement and verify all 6 requirements (R1: DMV Score, R2: 3 Telemetry Scoring Rules, R3: Campaign Fingerprinting, R4: One-Click SAR PDF Export, R5: Analyst Workload Heatmap, R6: Live Auto-Feed Mode) with 100% backend test pass and clean frontend build.

## Phase 0: Survey & Scoping
- Spawn 3 parallel Explorers / Spec Miners:
  1. Explorer 1: Risk Engine & Telemetry & Campaign & DMV architecture (`app/engine/`, `app/models/`, `app/services/`)
  2. Explorer 2: Analytics & SAR PDF & API routes (`app/api/`, reporting libraries, PDF generation, data structures)
  3. Explorer 3: Live Auto-Feed Engine & Frontend Dashboard (`app/synthetic/`, WebSocket feed, `frontend/src/`)

## Phase 1: Architecture Specification
- Consolidate explorer findings into `PROJECT.md` and `TEST_INFRA.md`.
- Establish interfaces, data contracts, and milestones.

## Phase 2: Dual Track Execution
- Implementation Track:
  - M1: DMV + Device Telemetry Rules (`R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`) + Campaign DNA (`R_CAMPAIGN_MATCH`).
  - M2: SAR PDF Export (`GET /cases/{case_id}/sar/pdf`) + Workload Heatmap API (`GET /stats/analytics` or `/stats/workload-heatmap`).
  - M3: Live Auto-Feed Engine (background generator at 5-20 tx/s, full pipeline scoring, `/ws/feed` broadcast, clean start/stop API).
  - M4: Frontend Integration (CaseDrawer gauge & SAR button, Analytics Heatmap & DMV table, Auto-Feed toggle & live ticks).
- E2E Testing Track:
  - Parallel development of Tiers 1-4 comprehensive test suite.
  - Publish `TEST_READY.md`.

## Phase 3: Final Verification & Adversarial Coverage Hardening
- Run full test suite with 0 regressions.
- Verify frontend builds and lints cleanly.
- Reviewer, Challenger, and Forensic Auditor verification.

## Phase 4: Delivery & Handoff
- Soft/Hard Handoff to Sentinel.
