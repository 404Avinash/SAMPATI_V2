## 2026-09-02T06:55:00Z
<USER_REQUEST>
You are the SWE Light orchestrator for this project.
Your working directory is `/home/avi/Downloads/Sampati_v2/.agents/swe`.
The original user request is recorded at `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md`.

Mission:
Integrate Google Gemini API into the SAMPATI V2 FastAPI/React platform to act as an intelligent Fraud Analyst Copilot (briefings, chat, SAR narrative drafting) with deterministic graceful fallback and zero payment scoring latency impact.

Repository Guidelines & Rules from AGENTS.md:
- Virtualenv: `./.venv/bin/python`, `./.venv/bin/pytest`, `./.venv/bin/ruff`
- Frontend: `frontend/` (Node.js / Vite, ESLint with `--max-warnings 0`)
- Validation: `./.venv/bin/pytest tests/ -v`, `./.venv/bin/ruff check app tests`, `cd frontend && npm run lint && npm run build`
- All tests must pass both with and without GEMINI_API_KEY.

Execute the SWE Light protocol and report back when finished.
</USER_REQUEST>
