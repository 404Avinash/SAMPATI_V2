# BRIEFING — 2026-09-04T12:08:00Z

## Mission
Survey R1 (Geographic India Map component integration, styling, libraries, SVG map approach) and R2 (Threat Intel Page Crash white screen root cause in ThreatIntelPage.jsx).

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend & Threat Intel Explorer, Frontend Survey Explorer (R1 Anti-Slop)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1
- Original parent: 1d0e3cfc-1bcd-4db9-88c0-55fb7981a628
- Milestone: Survey R1 - Kill All Overclaims and AI-Sounding Copy
- Current Milestone: Survey R1 (India Map) & R2 (Threat Intel Crash)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement source code changes directly
- Output structured analysis report to handoff.md in own folder
- Notify parent agent via send_message when done
- Read-only on source code (frontend/src and app/)
- Deliver detailed catalogue in survey_r1_report.md and handoff.md

## Current Parent
- Conversation ID: 271e71dd-4370-4307-afc1-a65ac33fe525
- Updated: 2026-09-04T12:08:00Z

## Investigation State
- **Explored paths**:
  - `frontend/src/pages/ThreatIntelPage.jsx` (Identified lines 921–925 and line 1019 object-rendering React runtime crash)
  - `app/models/threat_intel.py` (`ThreatSignalResponse.matched_campaign` is `CampaignMatch` object)
  - `app/services/threat_intel_service.py` (stores and returns dict for `matched_campaign`)
  - `frontend/src/services/api.js` (investigated `getThreatSignals`, `getThreatCampaigns`)
  - `frontend/package.json` (no `deck.gl` or `react-simple-maps`, `framer-motion` available)
  - `frontend/src/pages/OverviewPage.jsx` & `NetworkConstellation.jsx` (Topology Visualizer placement for `GeoMuleMap.jsx`)
- **Key findings**:
  - **R2 Root Cause**: `ThreatIntelPage.jsx:923` renders `{signal.matched_campaign}` directly in JSX. In `INITIAL_FALLBACK_SIGNALS` this is a string, but the real backend response returns an object (`CampaignMatch`). Rendering an object throws `Objects are not valid as a React child`, unmounting the tree to a white screen. A secondary crash occurs at line 1019 when a signal is inspected.
  - **R1 Solution**: A pure React + SVG + Framer Motion component (`GeoMuleMap.jsx`) with 0 external dependencies is optimal, highly performant, and 100% offline-safe. Calibrated 9 Indian hubs (Mumbai, Delhi, Bengaluru, Jamtara, Mewat, Kolkata, Hyderabad, Ahmedabad, Chennai) with quadratic bezier arcs and glowing animated flows.
- **Unexplored areas**: None; complete surveys of R1 and R2 finished.

## Key Decisions Made
- Recommended safe extraction helper `getCampaignLabel()` in `ThreatIntelPage.jsx` to handle both string fallbacks and backend object models.
- Recommended adding a lightweight `ErrorBoundary` in `components/common/` to prevent any unhandled error from white-screening.
- Recommended integrating `GeoMuleMap.jsx` into `OverviewPage.jsx` via a view toggle in the Topology Visualizer panel (`[ Constellation | India Mule Corridors ]`).

## Artifact Index
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/BRIEFING.md` — Persistent working memory
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/progress.md` — Liveness heartbeat
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md` — Complete 5-component handoff report for R1 & R2
