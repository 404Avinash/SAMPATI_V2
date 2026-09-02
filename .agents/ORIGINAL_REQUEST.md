# Original User Request

## Initial Request — 2026-09-02T17:40:48Z

Upgrade the existing Gemini AI Copilot into an autonomous "Gemini Assistant". The assistant must have deep contextual awareness of the platform's inner workings and the ability to execute platform operations autonomously via function calling.

Requirements:
1. R1. Deep Context Injection & Rebranding:
   - Rename UI and backend references from "AI Copilot" to "Gemini Assistant".
   - Enhance `/cases/{case_id}/ai-briefing` and `/cases/{case_id}/ai-chat` backend endpoints to inject maximum context into the LLM system prompt (raw case transaction history, evaluated rule breakdown, network topology data, core algorithmic definitions extracted directly from `ENCYCLOPEDIA.md` to explain *exactly* why a rule fired in plain English).
2. R2. Agentic Operations (Function Calling):
   - Equip Gemini Assistant with an agentic loop (Gemini native function calling or robust prompt routing) allowing operations:
     a) Block or Hold a specific transaction/VPA.
     b) Trigger a Federation Intelligence Round.
     c) Export the SAR (Suspicious Activity Report) to PDF.
     d) Simulate a new batch of transactions.
3. R3. UI Command Integration:
   - Update frontend (e.g. `CaseAiCopilotView.jsx` or equivalent renamed component) to seamlessly display tool execution statuses in the chat log (e.g. showing system messages when Assistant triggers a federation round).

Acceptance Criteria:
- Automated Testing & Regression: Existing pytest suite (`.venv/bin/pytest tests/ -v`, 737+ tests) passes with 0 failures.
- New unit tests specifically verifying that the Gemini Assistant's chat endpoint can successfully parse and route tool execution requests for Federation and Simulation.
- Frontend UI displays "Gemini Assistant" instead of "AI Copilot".
- When a user types "Trigger a federation round" into Assistant chat, system calls backend federation execution logic and reports success.
- When a user asks "Explain why the DMV score spiked", response incorporates algorithmic definitions from Encyclopedia context.
- Frontend ESLint (`cd frontend && npm run lint`) has 0 errors/warnings and `npm run build` succeeds.
