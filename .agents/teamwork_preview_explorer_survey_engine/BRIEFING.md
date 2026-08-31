# BRIEFING — 2026-08-31T03:25:00+05:30

## Mission
Investigate Core Risk Engine, DMV Score, Device Telemetry Rules, and Campaign Fingerprinting for SAMPATI V2 Sprint 2.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, synthesizer
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_engine
- Original parent: 1a77121b-3a79-4485-bfe4-db30788be55e
- Milestone: Sprint 2 Survey Phase

## 🔒 Key Constraints
- Read-only investigation — do NOT implement in source code
- Analyze codebase and design DMV Score, Device Telemetry Rules, and Campaign Fingerprinting
- Ensure 100% backward compatibility with existing 559 tests
- Produce structured 5-component handoff report

## Current Parent
- Conversation ID: 1a77121b-3a79-4485-bfe4-db30788be55e
- Updated: 2026-08-31T03:25:00+05:30

## Investigation State
- **Explored paths**: `app/engine/upi_scorer.py`, `app/engine/upi_rules.py`, `app/models/upi_models.py`, `app/services/upi_cases.py`, `app/engine/honeypot.py`, `app/engine/adaptive.pyc`, `app/engine/upi_state.pyc`, `tests/`
- **Key findings**:
  - Baseline: 559 tests passing across all 5 tiers.
  - Complete mathematical formula and sliding window state model for DMV Score (0-100).
  - Telemetry rules designed: `R_SIM_DEVICE_MISMATCH` (30 pts), `R_IMPOSSIBLE_TRAVEL` (35 pts), `R_DATACENTER_IP` (25 pts).
  - Campaign fingerprinting layer designed: 5-dim behavioral DNA extractor, similarity matching ($\ge 0.82 \implies$ `R_CAMPAIGN_MATCH` [30 pts]), dynamic store ingestion on `BLOCK`/`CONFIRMED_FRAUD`.
  - Full backward compatibility strategy with zero regressions on existing test contracts.
- **Unexplored areas**: None (investigation complete).

## Key Decisions Made
- Designed DMV Score formula as composite of Dormancy Index ($D$) and Burst Outflow Velocity ($V$).
- Compiled complete cloud CIDR list (AWS, GCP, Azure, DO, Tor) for `R_DATACENTER_IP`.
- Used Haversine great-circle distance algorithm with coordinate/city lookup table for `R_IMPOSSIBLE_TRAVEL`.
- Preserved existing schema structure by adding optional fields with defaults to `UpiEvaluationResponse`.

## Artifact Index
- handoff.md — Complete 5-component investigation and architectural design report for Core Risk Engine & Telemetry
