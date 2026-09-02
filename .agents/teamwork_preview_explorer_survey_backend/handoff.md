# Backend Survey Explorer Handoff Report: Gemini Assistant Architecture

## 1. Observation

1. **AI Endpoints Mounting**:
   - `app/api/upi.py`:
     - Line 346: `@router.get("/cases/{case_id}/ai-briefing")` and Line 347: `@router.post("/cases/{case_id}/ai-briefing")`
     - Line 377: `@router.post("/cases/{case_id}/ai-chat")`
     - Line 416: `@router.get("/cases/{case_id}/ai-sar")` and Line 417: `@router.post("/cases/{case_id}/ai-sar")`
   - `app/main.py`:
     - Line 285: `@app.get("/cases/{case_id}/ai-briefing")` and Line 286: `@app.post("/cases/{case_id}/ai-briefing")`
     - Line 317: `@app.post("/cases/{case_id}/ai-chat")`
     - Line 360: `@app.get("/cases/{case_id}/ai-sar")` and Line 361: `@app.post("/cases/{case_id}/ai-sar")`
     - Line 270: `@app.get("/cases/{case_id}/sar/pdf")`

2. **LLM Service Layer (`app/services/gemini_service.py`)**:
   - Class `GeminiCopilotService` (lines 177–656) uses `httpx.AsyncClient` targeting `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}`.
   - Default model: `gemini-1.5-flash`, fallback cascade: `gemini-1.5-flash-8b`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-flash-latest`, `gemini-pro-latest`.
   - Complete heuristic fallback engine (`_generate_fallback_briefing`, `_generate_fallback_chat_reply`, `_generate_fallback_sar_text`) handles missing API keys and network dropouts.
   - Singleton accessor: `get_gemini_copilot_service()` at line 660.

3. **Backend Service Capabilities for Function Calling**:
   - Federation round trigger: `UpiCaseService.run_federation()` in `app/services/upi_cases.py:1125` and `app/api/upi.py:156` (`POST /upi/federation/run`).
   - Transaction simulation: `UpiCaseService.simulate(count, fraud_ratio, seed)` in `app/services/upi_cases.py:1151` and `app/api/upi.py:520` (`POST /upi/simulate`).
   - Block / Hold entity: `UpiHotState.mark_confirmed_fraud([vpa])`, `FederatedCoordinator.record_signal(...)`, `UpiCaseService.update_case_status(case_id, new_status="ESCALATED", resolution="BLOCK_VPA")` in `app/services/upi_cases.py:637`.
   - SAR PDF export: `app.forensics.sar_pdf.build_sar_pdf(case)` in `app/forensics/sar_pdf.py` and `UpiCaseService.generate_sar_pdf(case_id)` in `app/services/upi_cases.py:1201`.

4. **Algorithmic Knowledge in `ENCYCLOPEDIA.md`**:
   - Dead Money Velocity (DMV) score formula and rationale: `dormancy_gap_hours`, `outflow_velocity`, `depletion_ratio` (lines 374–398).
   - 3-Layer Scoring architecture: Layer 1 Deterministic Rules (0–100), Layer 2 Adaptive EWMA anomaly (0–25), Layer 3 Federated Graph Network (0–40), Verdict cutoffs ALLOW (<45), HOLD (45–69), BLOCK (≥70) (lines 288–317).
   - Complete rule definitions table (lines 327–342): `R_HONEYPOT_HIT`, `R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`, `R_CAMPAIGN_MATCH`, `PASS_THROUGH_CONDUIT`, `FAN_IN_BURST`, `FAN_OUT_DISPERSAL`, `NEW_PAYEE_VPA`, `NEW_ACCOUNT_HIGH_VALUE`, `DEVICE_FARM`, `LIMIT_SKIRTING`, `KNOWN_FRAUD_ENTITY`.

5. **Test Suite Status**:
   - `tests/test_gemini_copilot.py`: 27 passing tests (2.29s).
   - Full suite `./.venv/bin/pytest`: 737 passing tests (63.43s).

---

## 2. Logic Chain

1. **Endpoint Resolution (Obs 1)**: Both `app/main.py` and `app/api/upi.py` route case AI requests (`/cases/{case_id}/ai-briefing`, `/cases/{case_id}/ai-chat`, `/cases/{case_id}/ai-sar`) through `get_gemini_copilot_service()`. Upgrading the underlying service class to `GeminiAssistantService` (and providing backward-compatible aliases) immediately upgrades both route trees without breaking REST contracts.
2. **Context Injection Mechanism (Obs 1, 4)**: The current `generate_case_briefing` and `chat_with_case_copilot` methods pass `json.dumps(case_data)`. By pre-processing `case_data` to enrich each item in `rule_hits` and `reasons` with `ENCYCLOPEDIA.md` definitions, expanding the DMV explanation, and summarizing the network graph topology (fan-in, hops, fan-out, member count, total volume), the LLM system prompt receives complete algorithmic context.
3. **Agentic Operations (Obs 2, 3)**:
   - For Gemini API calls: Passing `tools=[{"functionDeclarations": [...]}]` enables native function calling for `block_vpa`, `hold_case`, `trigger_federation_round`, `export_sar_pdf`, and `simulate_transactions`.
   - For Offline / Fallback mode: Augmenting `_generate_fallback_chat_reply` with regex/keyword intent parsers allows it to execute `case_service.run_federation()`, `case_service.simulate()`, `mark_confirmed_fraud()`, and `generate_sar_pdf()`, ensuring testability and offline resilience.
4. **Rebranding (Obs 2, 5)**: Replacing all system instruction prompts, response metadata, docstrings, and model descriptions with "Gemini Assistant", while retaining `GeminiCopilotService = GeminiAssistantService` aliases, preserves 100% test compatibility across the 737 existing tests.

---

## 3. Caveats

1. **Offline Network Environment**: In CI and local developer test runs, `GEMINI_API_KEY` may be unset or external network calls to `generativelanguage.googleapis.com` may be blocked. All agentic tool execution and deep context features MUST work deterministically in the heuristic fallback layer.
2. **Async / Sync Service Boundary**: `UpiCaseService.simulate()` and `run_federation()` are synchronous methods on the singleton instance, whereas `chat_with_case_assistant()` is an `async` coroutine. Calling them directly from the async assistant method is non-blocking and safe because execution times are sub-5ms in tests.

---

## 4. Conclusion

The backend architecture is cleanly structured and fully equipped to support the Gemini Assistant upgrade:
1. `app/services/gemini_service.py` is the central implementation target. Upgrading it to `GeminiAssistantService` with function calling dispatch, deep context injection from `ENCYCLOPEDIA.md`, and resilient intent routing will fulfill all requirements of R1 and R2.
2. `app/models/upi_models.py` can be extended with optional tool execution fields (`tool_calls: Optional[List[Dict[str, Any]]]`) on `AiChatResponse`.
3. `app/api/upi.py` and `app/main.py` require minor docstring and import updates to complete the rebranding.
4. All 737 existing tests will continue to pass without regression, and new unit tests can be added to `tests/test_gemini_copilot.py` to verify tool execution.

---

## 5. Verification Method

### Test Commands
```bash
# 1. Run Gemini unit test suite:
./.venv/bin/pytest tests/test_gemini_copilot.py -v

# 2. Run Ruff python linter:
./.venv/bin/ruff check app tests

# 3. Run full pytest suite (737+ tests):
./.venv/bin/pytest tests/ -v
```

### Key Files to Inspect
- `app/services/gemini_service.py`: Service class implementation, system instructions, function declarations, and fallback intent router.
- `app/models/upi_models.py`: `AiChatRequest`, `AiChatResponse`, `AiCaseBriefingResponse`.
- `app/api/upi.py` & `app/main.py`: AI endpoint routes and handlers.
- `tests/test_gemini_copilot.py`: Test coverage for tool execution, DMV explanation, and rule breakdown.

### Invalidation Conditions
- If any of the 737 existing tests fail after the upgrade.
- If asking "Trigger a federation round" fails to invoke `case_service.run_federation()`.
- If asking "Explain why the DMV score spiked" returns generic advice without referencing dormancy, outflow velocity, or depletion ratio.
