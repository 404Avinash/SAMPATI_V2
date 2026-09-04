# Explorer Survey 1 Task Assignment

## Mission: Survey R1 (Geographic India Map) and R2 (Threat Intel Page Crash)

### Context
Read `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (under timestamp 2026-09-04T12:04:16Z).
Project Root: `/home/avi/Downloads/Sampati_v2`
Working Directory: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1`

### Objectives
1. **R2 Investigation**:
   - Inspect `frontend/src/pages/ThreatIntelPage.jsx` (and related components/hooks/APIs).
   - Diagnose why the `/threat-intel` route is crashing with a blank white screen / React runtime error.
   - Trace all API calls (`/intel/signals`, `/intel/campaigns`, etc.), state hooks, and render mappings. Identify exact lines where `undefined` or `null` is dereferenced or mapped.
   - Propose a robust fix ensuring safe defaults, proper loading/fallback states, and error handling.
2. **R1 Investigation**:
   - Inspect where the Geographic India Map (`GeoMuleMap.jsx` or similar) can be added (e.g. in `ThreatIntelPage.jsx` or `OverviewPage.jsx` / tabs).
   - Check `frontend/package.json` to see if libraries like `react-simple-maps`, `deck.gl`, `lucide-react`, or SVG rendering utilities are installed.
   - Investigate lightweight, high-performance approaches for rendering a stylized map of India with animated connection lines (arcs or vectors) between major Indian tech/financial hubs (e.g. Mumbai, Bangalore, Delhi, Jamtara, NCR).
   - Propose concrete component architecture and data source (live fraud topology / simulated coordinates).

### Output
Write your comprehensive investigation report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md` with:
- Exact file paths, line numbers, and root causes identified.
- Concrete, actionable implementation recommendations.
- Commands to verify your findings.

## 2026-09-04T12:07:22Z

You are Explorer Survey 1. Read your task description in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/DISPATCH.md and /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md.
Investigate R1 (Geographic India Map component integration, styling, libraries, SVG map approach) and R2 (Threat Intel Page Crash white screen root cause in ThreatIntelPage.jsx).
Investigate thoroughly using view_file and grep_search.
Write your detailed report to /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md.
Communicate back to orchestrator when finished using send_message.
