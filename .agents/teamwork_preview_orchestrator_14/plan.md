# Orchestrator Execution Plan

## Objectives
Resolve 3 critical UI bugs and implement 1 visual demo feature:
- R1: Geographic India Map Visualization (`GeoMuleMap.jsx` or similar, rendering stylized India map, animated connections between major hubs like Mumbai, Bangalore, Delhi, Jamtara, NCR, fintech/cybersecurity aesthetic)
- R2: Fix Threat Intel Page Crash (White Screen in `ThreatIntelPage.jsx`, safe data handling / loading fallbacks)
- R3: Whitewash Constellation Graph Background (`NetworkConstellation.jsx` canvas background to white/transparent, updating node/edge/label colors for high contrast)
- R4: Fix Verdict Velocity Graph to Show Rolling Rate, Not Cumulative (`VerdictVelocityChart.jsx` or data aggregation logic)

## Phases

### Phase 0: Survey & Investigation
- Dispatch 3 parallel Explorers:
  - Explorer 1: Investigate R2 (ThreatIntelPage crash causes, API responses, undefined access) & R1 (Dashboard structure, where to insert GeoMuleMap, map rendering options/libraries available in package.json or SVG approaches).
  - Explorer 2: Investigate R3 (NetworkConstellation styling, dark/slate canvas colors, nodes/edges/labels contrast against white background).
  - Explorer 3: Investigate R4 (VerdictVelocityChart and live feed/history data structures, cumulative accumulation vs rolling rate calculation).
- Synthesize survey findings into `PROJECT.md`.

### Phase 1: Implementation
- Dispatch Worker(s) with clear write boundaries:
  - Implement R1 GeoMuleMap & integrate into Threat Intel / Overview dashboard.
  - Implement R2 fix in ThreatIntelPage.jsx.
  - Implement R3 whitewash in NetworkConstellation.jsx.
  - Implement R4 rolling rate calculation in VerdictVelocityChart.jsx / data aggregation.
- Require Workers to verify:
  - `pytest tests/ -v` (0 failures, 969 tests)
  - `cd frontend && npm run lint` (0 warnings)
  - `cd frontend && npm run build` (0 errors)

### Phase 2: Review & Challenge
- Dispatch 2 independent Reviewers to review code correctness, completeness, and visual quality.
- Dispatch 2 Challengers to verify edge cases and empirical functionality.
- Dispatch Forensic Auditor for integrity verification.

### Phase 3: Gate & Human Reporting
- Check gate criteria in GATE_STATUS.md.
- Pass report back to caller/parent.
