# Dispatch — Worker 15.M1: Geographic India Map High-Fidelity Replacement

Read:
- `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md`
- `/home/avi/Downloads/Sampati_v2/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_1/analysis.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_1/handoff.md`

Your working directory is: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m1`

File Write Ownership (Exclusive):
- `frontend/src/components/overview/GeoMuleMap.jsx`

Task:
Implement the High-Fidelity, Topologically Accurate Vector Cartography Map in `frontend/src/components/overview/GeoMuleMap.jsx`:
1. Replace the crude 20-point bezier blob with the authentic 139-vertex calibrated geographic boundary path of India (including Kashmir, Gujarat Saurashtra & Kutch, Konkan & Malabar coast, Kanyakumari cape, Coromandel coast, Bengal delta, Siliguri corridor, and the Northeast Seven Sisters).
2. Geodetically calibrate `INDIAN_HUBS` coordinates so each city matches true latitude/longitude from backend `CITY_COORDINATES` in `app/engine/upi_rules.py` (Mumbai, Delhi NCR, Bengaluru, Hyderabad, Kolkata, Chennai, Mewat, Jamtara, Ahmedabad, etc.).
3. Update `MULE_CORRIDORS` quadratic bezier paths (`d`) to anchor cleanly to the new hub coordinates.
4. Maintain and polish the sleek modern fintech/cybersecurity aesthetic:
   - Clean monochromatic basemap (slate-50/white with subtle coordinates/graticule lines).
   - Dual-layer glowing bezier arcs with `<feGaussianBlur>`.
   - Animated flow particles using `<animateMotion>`.
   - Pulsating radar hotspot rings at Jamtara and Mewat epicenters.
   - Clear, legible city labels and interactive tooltips.
   - Severity filters (`ALL`, `CRITICAL`, `HIGH`) and interactive `onSelectCase` callback.
5. Verify:
   - `cd frontend && npm run lint` must pass with 0 warnings (`--max-warnings 0`).
   - `cd frontend && npm run build` must complete cleanly with 0 errors.
   - `./.venv/bin/pytest tests/ -v` must remain 100% passing.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes, run tests, and write your completion report in `handoff.md` in your working directory. Send a message to parent when done.

## 2026-09-04T13:22:54Z
You are Worker 15.M1 for SAMPATI V2.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m1
Read DISPATCH.md in your working directory and follow all instructions.
Your exclusive file ownership: frontend/src/components/overview/GeoMuleMap.jsx
Implement the authentic 139-vertex India vector cartography map, calibrate hubs to true lat/long from app/engine/upi_rules.py, update glowing arcs and animated flow particles, and ensure clean monochromatic styling.
MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
Run verification: cd frontend && npm run lint && npm run build, and pytest tests/ -v.
Write your handoff report to handoff.md and send a completion message to parent.

