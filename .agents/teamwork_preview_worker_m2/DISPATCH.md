## 2026-08-31T15:39:26Z
You are Worker 2 for SAMPATI V2 Sprint 3 Milestone 2 (Cinematic NetworkConstellation: R3).

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2
Workspace root: /home/avi/Downloads/Sampati_v2

You EXCLUSIVELY own and are permitted to modify:
- `frontend/src/components/NetworkConstellation.jsx`

Context & Input:
- Read /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (Sprint 3 section)
- Read /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md for component blueprint and physics equations.

Requirements to implement in `NetworkConstellation.jsx`:
1. Continuous spring force physics simulation:
   - Nodes drift and settle organically using spring-force simulation with harmonic ambient micro-forces (`Math.sin(t * 1.2 + n.y * 0.01) * 0.035`) and edge rest-length oscillations (`95 + Math.sin(t * 2.0) * 3.5`) even when paused or settled.
2. Pulsing node glow effects based on verdict:
   - BLOCK verdict nodes pulse with red glow animation on canvas (`rgba(220, 38, 38, 0.45)` with `Math.sin(t * 4)`).
   - HOLD verdict nodes pulse with amber glow animation (`rgba(245, 158, 11, 0.40)` with `Math.sin(t * 2.5)`).
   - ALLOW nodes have subtle neutral glow.
3. Edge risk gradient & animated particle flow:
   - Edges colored by risk score: Low (<40) = Teal (`#14b8a6`), Medium (40-70) = Amber (`#f59e0b`), High (>70) = Crimson (`#ef4444`).
   - Animated particle flow dots travel along high-risk edges in the direction of money transfer.
4. Auto-play on load:
   - When cases exist on mount, automatically start timeline playback from t=0 so graph builds itself smoothly without requiring manual user interaction.
5. Canvas zoom and pan support:
   - Mouse scroll-to-zoom (scale) and click-drag-to-pan (offsetX, offsetY) on canvas. Convert mouse screen coordinates to world coordinates for hit detection.
6. Node click selection:
   - Clicking a node opens the CaseDrawer for that case (via `onSelectCase`).

Lint & Build rules:
- Respect ESLint in React Hooks guidelines in AGENTS.md (`--max-warnings 0` enforced).
- Test build with `cd frontend && npm run lint && npm run build`.

Write your completion report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2/handoff.md`.
Use `send_message` to notify parent when complete.
