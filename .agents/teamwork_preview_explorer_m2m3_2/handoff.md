# Handoff Report: Milestones M2/M3 (Agentic Operations & Tool Dispatch)

## 1. Observation
1. **Gemini Service Inspection (`app/services/gemini_service.py:177-656`)**:
   - `GeminiCopilotService` provides `generate_case_briefing`, `chat_with_case_copilot`, and `generate_sar_report`.
   - Lines 202–289 define `_call_gemini` which calls `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}` using `httpx.AsyncClient`.
   - The current implementation is strictly reactive and text-oriented; it lacks Gemini function declarations in the `tools` payload and does not execute platform operations autonomously.
   - Lines 578–634 implement `_generate_fallback_chat_reply`, which performs basic keyword matching ("why", "who", "dmv", "action", "sar") without intent routing for operational tool triggers (e.g., "trigger federation", "simulate batch", "block vpa", "export sar pdf").

2. **Platform Services Inspection (`app/services/upi_cases.py` & `app/forensics/sar_pdf.py`)**:
   - `UpiCaseService.update_case_status` (`app/services/upi_cases.py:637-750`) updates case review status (OPEN, REVIEWED, ESCALATED, DISMISSED), propagates confirmed fraud feedback to `AdaptiveBehaviorModel` (`line 719`) and `UpiHotState.mark_confirmed_fraud` (`line 720`), publishes confirmed rings to `DpipFeed` (`line 710`), and schedules async DB persistence.
   - `UpiCaseService.run_federation` (`app/services/upi_cases.py:1125-1131`) runs cross-PSP federation consensus rounds, attaches discovered mule rings, builds SARs, and broadcasts telemetry.
   - `UpiCaseService.simulate` (`app/services/upi_cases.py:1151-1168`) simulates labeled synthetic streams, evaluates transactions through the inline gate, and returns verdict counts and opened cases.
   - `build_sar_pdf` (`app/forensics/sar_pdf.py:29-239`) and `UpiCaseService.generate_sar_pdf` (`app/services/upi_cases.py:1201-1207`) generate high-fidelity binary PDF streams formatted for FIU-IND compliance.

3. **API & Models Inspection (`app/api/upi.py` & `app/models/upi_models.py`)**:
   - `AiChatRequest` (`app/models/upi_models.py:300-304`) takes `question: str` and `history: Optional[List[Dict[str, str]]]`.
   - `AiChatResponse` (`app/models/upi_models.py:306-313`) returns `case_id`, `question`, `answer`, `source`, `model`, but lacks `tool_executions`.
   - Route `POST /cases/{case_id}/ai-chat` (`app/api/upi.py:377-414`) invokes `chat_with_case_copilot` and returns the JSON dictionary matching `AiChatResponse`.

4. **Encyclopedia Knowledge Base Integration (`app/engine/encyclopedia_kb.py`)**:
   - Completed in M1 with 100% test pass rate (36 tests in `tests/test_encyclopedia_kb.py`).
   - Exports `build_case_encyclopedia_context` and `get_rule_explanation`, enabling deep context injection with algorithmic definitions and formulas (e.g. DMV, Gini, Smurfing, Honeypots).

5. **Existing Pytest Suite Status**:
   - `./.venv/bin/pytest tests/test_gemini_copilot.py` passed with 27/27 tests (0 failures).
   - `./.venv/bin/pytest tests/test_encyclopedia_kb.py` passed with 36/36 tests (0 failures).

---

## 2. Logic Chain
1. **Agentic Capabilities Requirement**:
   - Requirement R2 mandates autonomous agentic operations: (a) Block/Hold VPA/Transaction, (b) Trigger Federation Round, (c) Export SAR PDF, (d) Simulate Transactions.
   - Requirement R3 mandates frontend visibility of tool execution cards in chat.
   - Based on Observations 1 and 2, the underlying platform methods already exist in `UpiCaseService` and `sar_pdf.py`, but are disconnected from the LLM assistant service.

2. **Dual-Mode Autonomous Routing Architecture**:
   - To achieve robust zero-failure behavior in both cloud-connected and offline environments:
     - **Online Mode**: Declare native Gemini `functionDeclarations` in the API payload and parse returned `functionCall` candidates.
     - **Offline/Fallback Mode**: Use a regex and semantic parameter extraction router to detect intents such as "trigger federation", "simulate 100 txns", "block vpa", "export sar pdf".
   - Both modes route through the same unified `_execute_*` handlers, ensuring consistency.

3. **Structured API Response Contract**:
   - Adding `ToolExecutionResult` and `GeminiChatResponse(tool_executions: List[ToolExecutionResult] = [])` to `app/models/upi_models.py` allows the frontend to render system status cards when actions are executed, while `AiChatResponse = GeminiChatResponse` guarantees backward compatibility with existing tests and API callers.

4. **Deep Context Enrichment**:
   - Ingesting `build_case_encyclopedia_context` into the assistant's system prompt provides plain-English explanations of mathematical formulas and why specific rules fired.

---

## 3. Caveats
1. Matplotlib PDF Generation in restricted environments: `sar_pdf.py` sets `MPLCONFIGDIR=/tmp/matplotlib` to ensure writable cache paths across containerized sandboxes.
2. WebSockets for background operations: While tool execution returns structured results synchronously in the HTTP response, background events (such as `FEDERATION_ROUND` or `UPI_CASE_RESOLVED`) are also broadcast via WebSocket to maintain live UI state.

---

## 4. Conclusion
The technical architecture blueprint for Milestones M2/M3 is fully designed, detailed, and documented in `.agents/teamwork_preview_explorer_m2m3_2/analysis.md`.
The design provides:
1. Complete Pydantic schemas (`ToolExecutionResult`, `GeminiChatResponse`).
2. Live Gemini Function Calling schema declarations for 4 platform operations.
3. Resilient offline/fallback intent router with parameter extraction.
4. Execution handlers integrating `UpiCaseService`, `UpiHotState`, `DpipFeed`, `AdaptiveBehaviorModel`, and `build_sar_pdf`.
5. 10-point comprehensive unit test plan covering all routing and failure scenarios.

---

## 5. Verification Method
1. **Inspect Blueprint Artifacts**:
   - View `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m2m3_2/analysis.md`
2. **Verify Existing Tests**:
   - Run `./.venv/bin/pytest tests/test_gemini_copilot.py`
   - Run `./.venv/bin/pytest tests/test_encyclopedia_kb.py`
3. **Validate Architecture Compliance**:
   - Check that all 4 required operations are specified with exact signatures, parameters, and return schemas.
   - Verify that backward-compatibility aliases are preserved.
