## 2026-09-02T18:01:27Z
<USER_REQUEST>
You are Explorer 1 for Milestones M2/M3 (Deep Context Injection & System Prompt Assembly).
Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m2m3_1
Scope Document: /home/avi/Downloads/Sampati_v2/PROJECT.md
Original Request: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md

Task:
Investigate `app/services/gemini_service.py`, `app/api/upi.py`, `app/main.py`, and `app/engine/encyclopedia_kb.py`.
Design the deep context injection architecture:
1. Rebrand `GeminiCopilotService` to `GeminiAssistantService` while preserving `GeminiCopilotService` as an alias for backward compatibility.
2. In `generate_case_briefing()` and `chat_with_case_copilot()` (and new `chat_with_case_assistant()`):
   - Extract the case, raw transaction history, evaluated rules list, network graph topology (nodes, edges, risk scores).
   - Call `app.engine.encyclopedia_kb.build_case_encyclopedia_context(evaluated_rules, metrics)` to dynamically attach mathematical formulas and plain-English detection rationales for all fired rules.
   - Assemble a comprehensive, structured system prompt so the LLM knows all case details, transaction timestamps, amounts, accounts, risk signals, and algorithmic definitions.
3. Ensure fallback/mock responses in offline/test mode also utilize the enriched context (e.g. if the user asks "Explain why DMV score spiked", the assistant explains dormancy gap and outflow velocity math from Encyclopedia KB).

Deliverables:
Write blueprint to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m2m3_1/analysis.md` and complete `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m2m3_1/handoff.md`.
Send message back when completed.
</USER_REQUEST>
