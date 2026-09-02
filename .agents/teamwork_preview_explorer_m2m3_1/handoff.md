# Handoff Report: Deep Context Injection & System Prompt Assembly (Milestones M2/M3)

## 1. Observation

1. **`app/services/gemini_service.py` Structure & Aliases**:
   - `GeminiCopilotService` is defined at line 177 (`class GeminiCopilotService:`) and instantiated via `get_gemini_copilot_service()` at line 660.
   - Remote calling method `_call_gemini` at line 202 accepts `prompt`, `system_instruction`, and `json_mode`.
   - `generate_case_briefing()` (line 291) currently sends raw case JSON into prompt line 326: `prompt = f"Case Data Payload:\n```json\n{json.dumps(case_data, default=str, indent=2)}\n```"`.
   - `chat_with_case_copilot()` (line 395) prompts with a basic case dump and does not attach algorithmic formulas or graph topology details.
   - `_generate_fallback_chat_reply()` (line 578) uses static string heuristics for questions containing `why`, `who`, `dmv`, `action`, `sar` without dynamic interpolation of `ENCYCLOPEDIA.md` formulas.

2. **`app/engine/encyclopedia_kb.py` Knowledge Base Interface**:
   - Declares `RULE_DEFINITIONS` covering 22+ canonical rules with complete mathematical formulas and plain-English AML rationales.
   - Exposes `build_case_encyclopedia_context(evaluated_rules, metrics)` (lines 808–973) which formats a markdown table and detailed numbered breakdowns.
   - Exposes `get_rule_explanation(rule_code, value, metadata, context)` (lines 752–806) and `search_encyclopedia(query, limit)` (lines 975–1038).

3. **`app/api/upi.py` and `app/main.py` Endpoints**:
   - Endpoints `/cases/{case_id}/ai-briefing`, `/cases/{case_id}/ai-chat`, and `/cases/{case_id}/ai-sar` exist in both `app/api/upi.py` (lines 371–448) and `app/main.py` (lines 290–396).
   - Both import `from app.services.gemini_service import get_gemini_copilot_service`.

4. **`app/models/upi_models.py` Data Schemas**:
   - Contains `AiCaseBriefingResponse`, `AiChatRequest`, and `AiChatResponse` (lines 284–313).

5. **Existing Regression Test Suite**:
   - `tests/test_gemini_copilot.py` contains 27 test cases validating `GeminiCopilotService`, fallback classification matrices, chat intent keywords, and FastAPI endpoints.
   - Executing `./.venv/bin/pytest tests/test_gemini_copilot.py` passes 27/27 tests with 0 failures.
   - `tests/test_encyclopedia_kb.py` passes 36/36 tests with 0 failures.

---

## 2. Logic Chain

1. **Rebranding & Non-Breaking Compatibility (Observation 1 & 5)**:
   - Rebranding `GeminiCopilotService` to `GeminiAssistantService` can break existing imports and tests if not aliased.
   - By creating `GeminiAssistantService` as the primary implementation and defining `GeminiCopilotService = GeminiAssistantService`, `get_gemini_copilot_service = get_gemini_assistant_service`, and `chat_with_case_copilot` forwarding to `chat_with_case_assistant`, 100% backward compatibility is guaranteed across all 27 unit tests and external consumers.

2. **Context Enrichment via Deep Dossier Assembly (Observation 1, 2, & 3)**:
   - Passing only raw unformatted JSON to Gemini fails to guide the LLM on specific mathematical formulas and graph structures.
   - By implementing `build_case_dossier_text(case_data)` that extracts:
     - Primary transaction telemetry (VPA, PSP, device ID, SIM ID, IP, amounts, timestamps).
     - Multi-layer scoring breakdown (L1 Rules, L2 Adaptive EWMA, L3 Graph, DMV score).
     - Full transaction ledger table.
     - Graph topology (mule ring members, fan-in, hops, fan-out).
     - Dynamic markdown from `build_case_encyclopedia_context(evaluated_rules, metrics)`.
   - The LLM receives complete domain intelligence in its system instruction and is equipped to explain exact reasons and mathematical thresholds for all rule triggers.

3. **High-Fidelity Heuristic Fallback via Encyclopedia KB (Observation 1 & 2)**:
   - When Gemini is running in offline/test mode, user questions such as *"Explain why DMV score spiked"* or *"What is the formula for Dead Money Velocity?"* should not return generic answers.
   - Calling `get_rule_explanation("DMV_RAPID_DRAIN", value=dmv)` and `search_encyclopedia(question)` within `_generate_fallback_chat_reply()` allows the assistant to return exact mathematical formulas, dormancy thresholds, and AML typologies deterministically.

4. **Forward Compatibility for Agentic Operations M3 (Observation 4)**:
   - Adding `tool_executions: List[Dict[str, Any]] = Field(default_factory=list)` to `AiChatResponse` in `app/models/upi_models.py` prepares the backend response model for Milestone M3 autonomous tool execution without breaking existing frontend response parsing.

---

## 3. Caveats

1. **Transaction Ledger Depth in Memory**:
   - In ephemeral in-memory cases where only `trigger_txn` is populated, the ledger will display the primary trigger transaction. When `transactions` or `history` is populated on the case dictionary (or retrieved from `UpiHotState`), all rows will be formatted into the ledger.
2. **Network Sandbox for Remote Gemini Calls**:
   - Remote Gemini API calls require `GEMINI_API_KEY`. When the key is unset or network calls are blocked, the fallback engine gracefully activates and utilizes the exact same Encyclopedia Knowledge Base and dossier context.

---

## 4. Conclusion

The deep context injection architecture is fully designed and documented in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m2m3_1/analysis.md`.
The design satisfies all requirements:
1. Rebrands `GeminiCopilotService` to `GeminiAssistantService` while preserving seamless backward compatibility aliases.
2. Injects comprehensive case telemetry, multi-layer scores, transaction ledger, graph topology, and dynamic Encyclopedia formulas (`build_case_encyclopedia_context`) into the system prompt.
3. Empowers offline and fallback chat responses with exact mathematical formulas and plain-English rationales from `encyclopedia_kb`.
4. Extends response schemas with `tool_executions` for seamless Milestone M3 agentic function calling integration.

---

## 5. Verification Method

### 5.1 Independent Test Commands
```bash
# 1. Run existing Gemini Copilot test suite (must pass 27/27)
./.venv/bin/pytest tests/test_gemini_copilot.py -v

# 2. Run Encyclopedia Knowledge Base test suite (must pass 36/36)
./.venv/bin/pytest tests/test_encyclopedia_kb.py -v

# 3. Run full test suite to ensure zero regressions across all 737+ tests
./.venv/bin/pytest tests/ -v
```

### 5.2 Files to Inspect
- Blueprint: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m2m3_1/analysis.md`
- Target Service: `app/services/gemini_service.py`
- Target API Routes: `app/api/upi.py` and `app/main.py`
- Target Models: `app/models/upi_models.py`
- Knowledge Base: `app/engine/encyclopedia_kb.py`

### 5.3 Invalidation Conditions
- Any failure in `tests/test_gemini_copilot.py` indicates a broken backward-compatible alias or signature mismatch.
- Failure of fallback chat reply to return mathematical formulas for DMV questions indicates disconnection from `app.engine.encyclopedia_kb`.

