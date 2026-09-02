# Project: SAMPATI_V2 Gemini Assistant Upgrade

## Architecture
The SAMPATI_V2 platform upgrade transitions the reactive "AI Copilot" into an autonomous, deeply context-aware "Gemini Assistant".
- **Knowledge Layer (`app/engine/encyclopedia_kb.py`)**: Indexes algorithmic definitions, formulas, and plain-English detection rationales from `ENCYCLOPEDIA.md` (Dead Money Velocity, Adaptive EWMA, Structuring/Smurfing, Pass-Through Conduits, Mule Rings, Graph ML roles, Honeypot Decoys, Campaign DNA).
- **Service Layer (`app/services/gemini_service.py`)**: `GeminiAssistantService` (with backward-compatible aliases for `GeminiCopilotService`).
  - Injects deep case context (raw transactions, rule breakdown, graph topology, encyclopedia algorithmic explanations).
  - Implements an agentic loop with native Gemini function calling declarations and robust fallback intent routing.
  - Connects to platform services: `UpiCaseService.update_case_status` / `HotState`, `UpiCaseService.run_federation`, `build_sar_pdf`, and `UpiCaseService.simulate`.
- **API Endpoints (`app/api/upi.py` and `app/main.py`)**:
  - `POST /cases/{case_id}/ai-briefing`: Returns deep context briefing explaining triggered rules in plain English.
  - `POST /cases/{case_id}/ai-chat`: Accepts messages, executes tool calling when requested (Federation, Simulation, Block/Hold, SAR PDF), and returns response markdown + `tool_executions` metadata.
  - `POST /cases/{case_id}/ai-sar`: Retains SAR narrative generation capability.
- **Frontend Layer (`frontend/src/`)**:
  - Rebrands UI from "AI Copilot" to "Gemini Assistant" in `CaseDrawer.jsx`, navigation, and views.
  - `CaseAiCopilotView.jsx` (or `CaseGeminiAssistantView.jsx`) displays system tool execution badges/cards in chat log when assistant performs platform actions.
  - Zero-warning ESLint (`npm run lint`) and successful Vite production build (`npm run build`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Encyclopedia Algorithmic Knowledge Base | Extract & index mathematical formulas & explanations from ENCYCLOPEDIA.md (DMV, Gini, Smurfing, Mule, etc.) | M1 | R1 |
| 2 | Deep Context Injection & System Prompt Assembly | Enrich system prompt with raw transactions, evaluated rule breakdown, graph topology & encyclopedia rationale | M2 | R1 |
| 3 | Backend Rebranding & Backward Compatibility | Rename GeminiCopilotService to GeminiAssistantService with aliases in API and models | M2 | R1 |
| 4 | Agentic Tool Calling: Block/Hold VPA or Transaction | Autonomous tool execution to freeze/hold suspect VPA/transaction with audit log | M3 | R2 |
| 5 | Agentic Tool Calling: Trigger Federation Round | Autonomous invocation of Federated Intelligence round via UpiCaseService | M3 | R2 |
| 6 | Agentic Tool Calling: Export SAR to PDF | Autonomous generation & export of Suspicious Activity Report PDF | M3 | R2 |
| 7 | Agentic Tool Calling: Simulate Transaction Batch | Autonomous synthetic transaction batch injection & evaluation | M3 | R2 |
| 8 | Frontend Rebranding to Gemini Assistant | Update UI text, headers, drawer tabs, and view titles to Gemini Assistant | M4 | R1, R3 |
| 9 | Frontend Tool Execution UI Cards/Badges | Render system status cards/badges in chat log for autonomous tool executions | M4 | R3 |
| 10 | 100% E2E Test Suite & Adversarial Hardening | Comprehensive 4-tier test suite passing 100% + white-box coverage hardening | M5 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| T1 | E2E Test Suite Track | Design 4-tier test harness covering R1, R2, R3 and publish TEST_READY.md | none | DONE |
| M1 | Encyclopedia Knowledge Base | Create `app/engine/encyclopedia_kb.py` to extract & explain rule triggers | none | DONE |
| M2 | Context Injection & Rebranding | Update `gemini_service.py`, `upi.py`, `main.py` with deep context & GeminiAssistantService | M1 | DONE |
| M3 | Agentic Function Calling Operations | Implement tool declarations, executor routing for Block/Hold, Federation, SAR PDF, Simulation | M1, M2 | DONE |
| M4 | Frontend UI Tool Status & Rebranding | Update `CaseAiCopilotView.jsx`, `CaseDrawer.jsx`, `api.js` for tool cards & Gemini Assistant | M2, M3 | DONE |
| M5 | Final Milestone: E2E Pass & Hardening | Pass 100% E2E test suite (Tiers 1-4) and Tier 5 Adversarial Hardening | T1, M1, M2, M3, M4 | DONE |

## Code Layout
- `app/engine/encyclopedia_kb.py`: Encyclopedia Knowledge Base and rule rationale extractor.
- `app/services/gemini_service.py`: `GeminiAssistantService` with deep context assembly and agentic tool dispatch.
- `app/services/upi_service.py`: Platform operations integration (`run_federation`, `simulate`, `update_case_status`, `generate_sar_pdf`).
- `app/api/upi.py` & `app/main.py`: AI endpoint routes and request/response schemas.
- `frontend/src/views/CaseAiCopilotView.jsx`: Gemini Assistant view with chat and tool execution cards.
- `frontend/src/components/CaseDrawer.jsx`: Drawer tab rebranding to "Gemini Assistant".
- `frontend/src/services/api.js`: API client methods for Gemini Assistant.
- `tests/test_gemini_assistant.py`: Unit and integration tests for context injection, encyclopedia KB, and agentic function routing.
- `tests/test_e2e_gemini_assistant.py`: Opaque-box E2E test suite for user scenarios.

## Interface Contracts
### Knowledge Base Contract: `app/engine/encyclopedia_kb.py`
```python
def get_rule_explanation(rule_code: str, metric_value: float = None, context: dict = None) -> dict:
    """Returns { "rule_code": str, "name": str, "mathematical_definition": str, "plain_english_explanation": str }"""

def build_case_encyclopedia_context(evaluated_rules: list[dict], metrics: dict = None) -> str:
    """Returns formatted markdown string explaining all fired and evaluated rules for prompt injection."""
```

### Agentic Execution Contract: `app/services/gemini_service.py`
```python
class ToolExecutionResult(BaseModel):
    tool_name: str
    arguments: dict
    status: str # "success" | "error"
    result_summary: str
    data: Optional[dict] = None

class GeminiChatResponse(BaseModel):
    reply: str
    model: str
    tool_executions: list[ToolExecutionResult] = []
```
