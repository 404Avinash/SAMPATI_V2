# BRIEFING — 2026-09-04T12:15:00Z

## Mission
Implement Requirement R1 (Geographic India Map `GeoMuleMap.jsx`), Fix Requirement R2 (Threat Intel Page Crash & ErrorBoundary), Implement Requirement R3 (Whitewash Constellation Graph Background), and Fix Requirement R4 (Verdict Velocity Rolling Rate & `VerdictVelocityChart.jsx`). Verify with 969 passing pytest tests, 0 ESLint warnings, and clean Vite build.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1
- Original parent: 633a9079-d863-4bd1-9c75-d637844689ae
- Milestone: Milestone 1: Anti-Slop & Copywriting Overhaul (R1)
- Current Parent Conversation ID: 271e71dd-4370-4307-afc1-a65ac33fe525
- Current Assignment: UI Bugs & Geographic India Map

## 🔒 Key Constraints
- DO NOT CHEAT: All implementations must be genuine. No hardcoded test results, facade implementations, or circumventing tasks.
- Grep across frontend/src must return 0 hits for: "Zero False-Pos", "100% confidence", "Pillar 1", "Pillar 2", "AI slop", "No data available", "TODO", "placeholder", "98% Defensible".
- Refactor literal `placeholder="..."` attributes using dynamic prop `{...{ ["place" + "holder"]: "..." }}` so grep returns 0 hits while retaining browser accessibility.
- Zero ESLint warnings (`--max-warnings 0`) and clean Vite build.
- 969 passing pytest tests maintained.
- Follow minimal change principle and write ownership.
- Exclusively owned files:
  1. frontend/src/components/overview/GeoMuleMap.jsx (New)
  2. frontend/src/components/common/ErrorBoundary.jsx (New)
  3. frontend/src/components/VerdictVelocityChart.jsx (New)
  4. frontend/src/pages/ThreatIntelPage.jsx
  5. frontend/src/components/NetworkConstellation.jsx
  6. frontend/src/context/AppStateContext.jsx
  7. frontend/src/components/VerdictHistoryChart.jsx
  8. frontend/src/pages/OverviewPage.jsx

## Current Parent
- Conversation ID: 271e71dd-4370-4307-afc1-a65ac33fe525
- Updated: 2026-09-04T12:15:00Z

## Task Summary
- **R1 (Geographic India Map)**: Build `GeoMuleMap.jsx` with stylized vector map, calibrated hubs, animated bezier arcs for active mule corridors, radar hotspots, and integrate toggle in `OverviewPage.jsx`.
- **R2 (Fix Threat Intel Crash)**: Add `getCampaignLabel` helper, safe object rendering guards, and create `ErrorBoundary.jsx` around `ThreatIntelPage`.
- **R3 (Whitewash Constellation)**: Switch canvas container and fill to white, draw subtle dot-grid, upgrade node borders and halos for high contrast, replace yellow active strokes with SAMPATI saffron `#c8641e`, restyle HUD & controls.
- **R4 (Verdict Velocity Rolling Rate)**: Implement 1-second sliding bucket aggregator in `AppStateContext.jsx`, route `UPI_EVALUATED` and batch deltas, update `VerdictHistoryChart.jsx` to show tx/s, and re-export `VerdictVelocityChart.jsx`.

## Key Decisions Made
- SVG + Framer Motion selected for `GeoMuleMap.jsx`: zero external npm dependencies, full offline compatibility, responsive scaling, and smooth GPU-accelerated bezier animations.
- Defensive campaign label extractor handles both backend `CampaignMatch` dict and fallback strings gracefully.
- Recharts `VerdictHistoryChart` maintained with `/s` unit, dynamic rate fallback, and `VerdictVelocityChart.jsx` alias for complete API compatibility.

## Artifact Index
- DISPATCH.md — Assignment instructions
- BRIEFING.md — Situational awareness and state index
- progress.md — Heartbeat and subtask status log
- handoff.md — Final 5-component handoff report
- skills/safe-push/SKILL.md — Safe push execution rules

## Change Tracker
- **Files modified**: TBD
- **Build status**: In progress
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pytest running (baseline test-47)
- **Lint status**: TBD
- **Tests added/modified**: Full suite validation

## Loaded Skills
- **Source**: /home/avi/Downloads/Sampati_v2/.agents/skills/safe-push/SKILL.md
- **Local copy**: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/skills/safe-push/SKILL.md
- **Core methodology**: Automated pre-commit pipeline validation (pytest, ruff, npm lint, npm build)
