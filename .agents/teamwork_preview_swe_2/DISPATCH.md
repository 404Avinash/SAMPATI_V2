## 2026-09-04T16:19:46Z

<USER_REQUEST>
You are the SWE Light orchestrator for SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_swe_2
Project root: /home/avi/Downloads/Sampati_v2
Original request file: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md

Task:
Single self-contained fix; keep it small and focused. Replace the current custom SVG map in SAMPATI V2's `GeoMuleMap.jsx` component with a robust open-source mapping library (`react-simple-maps`) and a high-fidelity TopoJSON file of India to accurately plot the fraud hubs and corridors using real geographic coordinates.

Requirements:
1. R1. High-Fidelity Offline Map: Replace existing GeoMuleMap.jsx implementation to use react-simple-maps. Embed high-fidelity TopoJSON or GeoJSON of India's boundaries. The map must work 100% offline without fetching external tiles or assets.
2. R2. Accurate Coordinate Plotting: Plot existing financial hubs and fraud corridors using their actual latitude and longitude coordinates over the new map projection. Maintain the existing visual language (nodes, glowing corridors, labels).
3. Acceptance Criteria:
   - Frontend compiles successfully without errors (`cd frontend && npm run build`).
   - Existing test suite passes without regressions (`.venv/bin/pytest tests/`).
   - `GeoMuleMap.jsx` does not make any external network requests for map tiles or assets.

Please read the user requirements from ORIGINAL_REQUEST.md and execute the SWE Light workflow: dispatch to implementer, review via reviewer, verify with tests/checks, and report completion when all acceptance criteria are met.
</USER_REQUEST>
