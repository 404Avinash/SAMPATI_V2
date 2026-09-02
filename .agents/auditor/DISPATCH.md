## 2026-09-02T07:31:41Z
<USER_REQUEST>
<original_task>
This is a single self-contained feature integration; keep it small and focused.
Integrate Google Gemini API into the SAMPATI V2 FastAPI/React platform to act as an intelligent Fraud Analyst Copilot. This includes generating automated case briefings, interactive case Q&A, and regulatory SAR narrative drafting, all with a zero-latency impact on core payment scoring and a deterministic graceful fallback.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. Backend Gemini Service
Create a resilient `GeminiCopilotService` (using `httpx` or Google SDK) that handles case briefing generation, case chat, and SAR narrative drafting. It must gracefully fall back to a deterministic rule-based output if the API key is missing or fails. Do NOT block or slow down the main `/upi/check` payment scoring endpoint.

### R2. API Endpoints
Expose FastAPI routes (e.g., `GET /cases/{case_id}/ai-briefing` and `POST /cases/{case_id}/ai-chat`) to serve the Copilot features to the frontend.

### R3. Frontend Copilot UI
Update the React `CaseDrawer.jsx` (or add a related component) to include an "AI Copilot" tab with markdown-rendered briefings, scam pattern badges, and an interactive chat interface.

## Acceptance Criteria

### Integration & Fallback Verification
- [ ] Programmatic: The command `./.venv/bin/pytest tests/ -v` must pass all tests successfully.
- [ ] Programmatic: The test suite must pass even when the `GEMINI_API_KEY` environment variable is deliberately unset, proving the fallback logic works.

### Feature Verification
- [ ] Programmatic/Manual: The backend API endpoints successfully return structured JSON for AI briefings and chat without crashing.
- [ ] Manual: The React frontend successfully compiles (`npm run build`) and renders the AI Copilot tab, handling loading and error states cleanly.
</original_task>

Your metadata working directory is `/home/avi/Downloads/Sampati_v2/.agents/auditor`.
Repository root is `/home/avi/Downloads/Sampati_v2`.

Please conduct an independent post-victory audit:
1. Verify git timeline and commit history / diffs.
2. Check for cheating / mock abuse / weakened test assertions.
3. Run independent execution of the test suite and build pipeline:
   - `./.venv/bin/pytest tests/ -v`
   - `./.venv/bin/pytest tests/test_gemini_copilot.py -v` (with `GEMINI_API_KEY` unset)
   - `./.venv/bin/ruff check app tests`
   - `cd frontend && npm run lint` (`--max-warnings 0`)
   - `cd frontend && npm run build`
4. Write your audit report and deliver your structured verdict (CONFIRMED / REJECTED) to `/home/avi/Downloads/Sampati_v2/.agents/auditor/handoff.md`.
Send a message when finished.
</USER_REQUEST>
