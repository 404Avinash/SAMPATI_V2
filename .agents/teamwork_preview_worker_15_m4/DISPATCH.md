# Dispatch — Worker 15.M4: Threat Intelligence UI Uniform White Redesign

Read:
- `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md`
- `/home/avi/Downloads/Sampati_v2/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_3/analysis.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_3/handoff.md`

Your working directory is: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m4`

File Write Ownership (Exclusive):
- `frontend/src/pages/ThreatIntelPage.jsx`

Task:
Overhaul `frontend/src/pages/ThreatIntelPage.jsx` into a uniform, clean white, executive cybersecurity interface:
1. Uniform Clean White Background:
   - Replace all 7 undefined `className="card ..."` instances with `bg-white border border-hairline rounded-xl shadow-xs` or `panel` classes so containers have explicit white backgrounds and crisp borders.
   - Whitewash the dark hero header (`bg-gradient-to-r from-ink-900 via-slate-900 to-ink-900`) into an executive white panel with crisp typography, dark ink title text, and subtle saffron/blue accents.
   - Whitewash the pitch-black campaign clustering card (`bg-gradient-to-br from-slate-900 via-slate-800 to-ink-900`) into a luminous clean white card with dark text, clear stat badges, and crisp hairline dividers.
2. 3-Stage Entity Extraction Pipeline Redesign:
   - Replace fragmented pastel backgrounds (`bg-amber-50/50`, `bg-indigo-50/50`, `bg-emerald-50/50`) with pure white cards (`bg-white border border-hairline rounded-xl p-4`) highlighted by clean accent borders (`border-amber-400`, `border-indigo-400`, `border-emerald-500`).
   - Remove clunky nested white boxes and gray background strips (`bg-surface-muted/60`).
3. Typography, Spacing & Slop Purge:
   - Purge emoji spam (`⚡`, `▶`, `📱`, `🔗`, `🏷️`, `☍`) and replace with crisp SVG icons from `lucide-react` (e.g. `Zap`, `Play`, `Phone`, `Link2`, `Tag`, `Share2`).
   - Fix all unreadable `text-[9px]` classes — standardize on `text-xs` (12px) or `text-[11px]` with proper line-height and contrast.
   - Replace buzzwords (e.g., "Vector Cosine Correlation" -> "Cosine Match: 0.94").
   - Ensure the layout is breathable with consistent padding (`p-5`, `p-6`) and clean grid gaps.
4. Bug Fix:
   - Fix the latent null-pointer bug at line 1080: ensure `node && typeof node === "object"` so `null` objects don't trigger `node.id` TypeError.
5. Verify:
   - `cd frontend && npm run lint` must pass with 0 warnings (`--max-warnings 0`).
   - `cd frontend && npm run build` must complete cleanly with 0 errors.
   - `./.venv/bin/pytest tests/test_threat_intel_r1.py -v` must PASS.
   - `./.venv/bin/pytest tests/ -v` must pass 969 tests.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes, run tests, and write your completion report in `handoff.md` in your working directory. Send a message to parent when done.

## 2026-09-04T13:22:54Z
You are Worker 15.M4 for SAMPATI V2.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m4
Read DISPATCH.md in your working directory and follow all instructions.
Your exclusive file ownership: frontend/src/pages/ThreatIntelPage.jsx.
Overhaul ThreatIntelPage.jsx to a uniform clean white background across all cards (replace undefined .card with explicit white panels), whitewash the dark hero and dark campaign boxes, refine the 3-stage entity extraction cards, clean up typography, purge emoji spam with Lucide icons, and fix the line 1080 null check bug.
MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
Run verification: cd frontend && npm run lint && npm run build, and pytest tests/test_threat_intel_r1.py -v, and full pytest tests/ -v.
Write your handoff report to handoff.md and send a completion message to parent.

