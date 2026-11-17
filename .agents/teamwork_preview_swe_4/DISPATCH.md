## 2026-09-04T19:07:19Z

Task:
Fix the "India Mule Corridors" map component in the SAMPATI_V2 frontend so that it loads reliably, correctly renders transaction flow lines, and doesn't slide when clicked. This is a single self-contained fix; keep it small and focused.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: development

Requirements:
1. R1. Reliable Map Loading: The map component must load reliably and quickly without showing a blank ("blind") state or failing to initialize.
2. R2. Transaction Flow Visualization: The map must display directional arrows connecting the data points (dots) to clearly indicate the flow of transactions.
3. R3. Stable Interaction: Clicking on the map or its data points must not cause the map panel to slide out of view, collapse, or behave erratically.

Acceptance Criteria:
- An independent agent can load the dashboard and visually confirm the map renders its tiles immediately upon initialization.
- An independent agent can visually verify that directional arrows are rendered between the dots on the map.
- An independent agent can click on the map and its data points without the map panel sliding out of view or collapsing.
- All repo standards pass: `.venv/bin/pytest tests/` passes with 0 failures, `.venv/bin/ruff check app tests` passes, `cd frontend && npm run lint` passes with 0 warnings, `cd frontend && npm run build` succeeds.
