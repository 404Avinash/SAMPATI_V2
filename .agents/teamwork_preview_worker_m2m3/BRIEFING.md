# BRIEFING — 2026-09-03T10:58:00Z

## Mission
Execute Milestones M2 and M3: Zero-dependency custom Toast system, Threat Intelligence Dashboard (3 pillars), UI button wiring & live chart streaming, and global Terminology Overhaul ("Dormant-to-Active Velocity", "Suspected Mule Cluster", cap confidence at 98%, tagline insertion, contract test updates).

## 🔒 My Identity
- Archetype: teamwork_preview_worker_m2m3
- Roles: implementer, qa, specialist
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2m3
- Original parent: 708f3126-0948-4197-8593-5296c58527f6
- Milestone: M2 & M3

## 🔒 Key Constraints
- Rebrand GeminiCopilotService to GeminiAssistantService with 100% backward compatibility alias GeminiCopilotService = GeminiAssistantService.
- Deep Context Injection: Call encyclopedia_kb.build_case_encyclopedia_context to inject formulas and detection rationales into LLM prompts.
- Implement rich offline/fallback explanations when Gemini API is unconfigured or in tests (e.g. DMV math, dormancy gap, outflow velocity).
- Implement autonomous agentic operations (block_vpa_or_transaction, trigger_federation_round, export_sar_pdf, simulate_transactions) with dual-mode execution (Gemini native function calling + deterministic intent parser).
- Maintain 100% backward compatibility of existing endpoints/models.
- Ensure all pytest tests pass and ruff check passes.
- DO NOT CHEAT. All implementations must be genuine. No hardcoding or dummy facades.
- Zero ESLint warnings (`--max-warnings 0`) and clean Vite build.
- 0 grep occurrences of "Dead Money Velocity" and "Criminal Network" in frontend/src.
- Cap displayed confidence at 98%.

## Current Parent
- Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4
- Updated: 2026-09-03T10:58:00Z

## Task Summary
- **What to build**:
  1. Zero-dependency custom Toast notification system (`ToastContext.jsx`, `ToastContainer.jsx`, mounted in `App.jsx`/`MainLayout.jsx`).
  2. Threat Intelligence Dashboard (`Navbar.jsx`, `App.jsx`, `api.js`, `ThreatIntelPage.jsx` with 3 pillars: animated entity extraction flow, suspected campaign clustering card "Campaign similarity: 94%", real-time pre-transaction signal feed).
  3. Terminology find-and-replace ("Dead Money Velocity" -> "Dormant-to-Active Velocity", verify 0 hits for "Criminal Network", cap confidence at 98%, add tagline "Everyone sees a piece. SAMPATI connects the dots.", update `tests/frontend_contracts_test.py`).
  4. Operational button wiring & toasts ("Start Live Feed", "Run batch simulation", "Federation round", "Export SAR"), chart update fix in `autofeed.py`, `useWebSocket.js`, and `AppStateContext.jsx`, constellation auto-advance in `NetworkConstellation.jsx`.
- **Success criteria**:
  - `npm run lint` clean (0 warnings with `--max-warnings 0`)
  - `npm run build` clean (0 errors)
  - `pytest tests/frontend_contracts_test.py -v` passes
  - `pytest tests/test_threat_intel_r1.py -v` passes
  - `pytest tests/ -q` passes 100%
  - `ruff check app tests` 0 violations
- **Interface contracts**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`
- **Code layout**: `frontend/src/`, `app/services/autofeed.py`, `tests/frontend_contracts_test.py`

## Change Tracker
- **Files modified**: None yet for M2 & M3
- **Build status**: Initial inspection complete
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pending verification
- **Lint status**: Pending verification
- **Tests added/modified**: Pending

## Loaded Skills
- **Source**: `/home/avi/Downloads/Sampati_v2/.agents/skills/safe-push/SKILL.md`
- **Local copy**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2m3/skills/safe-push.md`
- **Core methodology**: Automated zero-friction safe commit and push protocol validating backend tests, ruff, frontend lint, and Vite build.

## Key Decisions Made
- Use framer-motion (already in package.json) for smooth zero-dependency toast animations.
- Add `/threat-intel` route and nav link between Overview and Investigations.
- Fallback mock data in `api.js` for threat signals to ensure flawless frontend demo capability while directly integrating with backend endpoints `/intel/signals`, `/intel/campaigns`, etc.
- In `autofeed.py`, include current stats in `UPI_EVALUATED` payload, and update `AppStateContext.jsx` to accumulate/update stats so the real-time velocity chart smoothly updates.
