## 2026-09-04T14:15:37Z
You are the Independent Victory Auditor for SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_victory_auditor_sentinel_9
Your workspace is: /home/avi/Downloads/Sampati_v2
Original User Request: /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md (specifically the latest request under ## 2026-09-04T13:13:26Z)

You must conduct an independent 3-phase audit (Phase A: Timeline, Phase B: Anti-cheating & Forensic Integrity, Phase C: Independent Test Execution) against the latest user request:

Requirements to Audit:
1. R1. Redesign Geographic India Map: The current SVG map of India in GeoMuleMap.jsx is replaced with a professional, high-fidelity mapping solution (accurate vector cartography/TopoJSON/Leaflet with sleek modern fintech/cybersecurity aesthetic, glowing arcs for connections, clear city labels, calibrated coordinates).
2. R2. Dedicated Topology Sub-Navbar / Page: Topology Visualizers (NetworkConstellation and GeoMuleMap) are moved out of the cramped Overview page into a dedicated space with sub-navbar navigation (e.g. /topology in Navbar, TopologyPage.jsx) allowing full-bleed real estate.
3. R3. Ambient Traffic in Verdict Velocity Chart: VerdictVelocityChart / VerdictHistoryChart always displays continuous simulated ambient traffic (2-5 TPS background ALLOW traffic) so it moves and looks alive even during idle demo states.
4. R4. Threat Intelligence UI Cleanup: ThreatIntelPage has a uniform clean white background across all panels, refined professional typography and spacing, and zero cluttered or low-quality AI slop appearance.

Verification Commands to Execute Independently:
1. ./.venv/bin/pytest tests/ -v (must pass all 969 tests with 0 failures)
2. cd frontend && npm run lint (must pass with 0 ESLint warnings, --max-warnings 0)
3. cd frontend && npm run build (must complete production build cleanly with 0 errors)
4. ./.venv/bin/ruff check app tests
