# Orchestration Plan: SAMPATI V2 Anti-Slop & Polish Pass

## Objective
Execute a comprehensive anti-slop audit, copy overhaul, dynamic KPI wiring, button interaction fix, and quality verification across the SAMPATI V2 platform to make it a demo-grade product that satisfies all acceptance criteria.

## Phase 0: Scope Survey (In Progress)
- Dispatch 3 parallel Explorers:
  - `survey_explorer_1`: R1 Copywriting, AI buzzwords, overclaims, empty states, forbidden strings.
  - `survey_explorer_2`: R2 Dynamic KPI metrics, `/intel/signals`, `/intel/campaigns`, Overview 15s polling, Investigations badge count.
  - `survey_explorer_3`: R3 Dead buttons, Settings audit, Threat Intel "Simulate Flow", form validation, tab scroll preservation, toast notifications.
- Aggregate reports into `PROJECT.md` Feature Inventory & Architecture.

## Phase 1: Milestone Decomposition & Interface Contracts
- **Milestone 1 (M1) — Anti-Slop & Copywriting Overhaul (R1)**:
  - Eliminate all forbidden terms ("Zero False-Pos", "100% confidence", "Pillar 1", "Pillar 2", "AI slop", "No data available", "TODO", "placeholder", etc.).
  - Rephrase titles, subtitles, card copy, and empty states with professional, defensible fraud analyst terminology.
- **Milestone 2 (M2) — Dynamic KPIs & Live Counters (R2)**:
  - Wire Threat Intelligence counters ("21 signals", "3 campaigns", "42 nodes") to live `/intel/signals` and `/intel/campaigns` endpoints.
  - Ensure Overview KPI strip auto-refreshes every 15s.
  - Wire Investigations tab badge to actual open case count.
- **Milestone 3 (M3) — Interactive Polish & Dead Buttons (R3)**:
  - Wire or remove inert buttons on Settings page.
  - Wire Threat Intelligence "Simulate Flow" button to execute simulation and show real results.
  - Ensure all actionable `<button>` elements have `onClick` handlers and trigger reactive Toast notifications.
  - Fix tab navigation scroll preservation and blank screen flashing.
  - Ensure all form inputs validate and submit properly.
- **Milestone 4 (M4) — Verification, Build, Lint, Grep & Forensic Audit**:
  - Run `.venv/bin/pytest tests/ -v` (0 failures).
  - Run `cd frontend && npm run lint` (0 warnings with `--max-warnings 0`).
  - Run `cd frontend && npm run build` (0 errors).
  - Grep verification across frontend source for forbidden terms.
  - Grep verification for unhandled `<button>` elements.
  - Forensic Auditor integrity review.

## Gate Criteria
- Strict AND across all verification criteria.
- Binary veto by Forensic Auditor on any integrity violation.
