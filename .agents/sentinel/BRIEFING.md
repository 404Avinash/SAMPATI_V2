# BRIEFING — 2026-09-04T16:22:00Z

## Mission
Orchestrate SWE Light fix for SAMPATI V2: Replace custom SVG map in `GeoMuleMap.jsx` with `react-simple-maps` and embedded high-fidelity offline TopoJSON/GeoJSON of India, plotting financial hubs and fraud corridors with accurate geographic coordinates.

## 🔒 My Identity
- Archetype: sentinel
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/sentinel
- Orchestrator: 633a9079-d863-4bd1-9c75-d637844689ae (.agents/teamwork_preview_orchestrator_13)
- Victory Auditor: 88f31fe7-0a06-4daa-8ee7-09925a4ca391 (.agents/teamwork_preview_victory_auditor_sentinel_7)
- Active Orchestrator: 7f8b92d3-b4aa-4f57-8eed-0a730f162d25 (.agents/teamwork_preview_orchestrator_15)
- Active Victory Auditor: c943e3c0-c665-4c20-ab60-a7384e4848fb (.agents/teamwork_preview_victory_auditor_sentinel_9)
- Orchestrator (active assigned): 7f8b92d3-b4aa-4f57-8eed-0a730f162d25 (.agents/teamwork_preview_orchestrator_15)
- SWE Orchestrator: cdc65fba-8fa3-4f10-bc4b-2fb2d5cf22cf (.agents/teamwork_preview_swe_2)

## 🔒 Key Constraints
- No technical decisions — relay only
- Victory Audit is MANDATORY before reporting completion
- Route: General (teamwork_preview_orchestrator) - multi-part SWE project with full team requested
- All visible buttons must have onClick or be removed
- Frontend grep must yield 0 matches for overclaims/placeholders
- Pytest (969 tests) must pass with 0 failures, ESLint with 0 warnings, Vite build clean
- R1: Geographic India map visualization (active mule network connections, inter-city animated connections)
- R2: Fix Threat Intel page crash / white screen
- R3: Whitewash NetworkConstellation canvas background & contrast
- R4: Fix Verdict Velocity graph to show rolling rate instead of cumulative total
- New R1: Redesign Geographic India Map (high-fidelity mapping like Leaflet, Deck.gl or TopoJSON)
- New R2: Separate Topology Visualizers into dedicated sub-navbar / page
- New R3: Ambient background traffic simulation in VerdictVelocityChart (2-5 TPS)
- New R4: Threat Intel UI cleanup (uniform white, typography, spacing)
- Route: SWE Light (teamwork_preview_swe) - single self-contained code change with explicit small/focused team request
- R1: Replace GeoMuleMap.jsx with react-simple-maps + embedded TopoJSON/GeoJSON (100% offline)
- R2: Accurate coordinate plotting for fraud hubs and corridors using real lat/lng
- Acceptance: cd frontend && npm run build succeeds; .venv/bin/pytest tests/ passes; 0 external network requests

## User Context
- **Last user request**: Single self-contained fix: replace GeoMuleMap.jsx with react-simple-maps + offline India TopoJSON, accurate coordinate plotting. Small focused team requested.
- **Pending clarifications**: none
- **Delivered results**:
  - Previous sprint UI redesign and bug fixes completed and verified.

## Project Status
- **Phase**: in progress
- **Active Orchestrator**: cdc65fba-8fa3-4f10-bc4b-2fb2d5cf22cf (.agents/teamwork_preview_swe_2)
- **Active Victory Auditor**: none
- **Cron 1 (Progress)**: task-41 (active)
- **Cron 2 (Liveness)**: task-43 (active)

## Victory Audit Status
- **Triggered**: no
- **Verdict**: pending
- **Retry count**: 0

## Artifact Index
- /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md — Root User Request record
- /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md — Agent User Request record
- /home/avi/Downloads/Sampati_v2/.agents/sentinel/BRIEFING.md — Sentinel Briefing
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_swe_2/DISPATCH.md — SWE Light Orchestrator dispatch instructions
