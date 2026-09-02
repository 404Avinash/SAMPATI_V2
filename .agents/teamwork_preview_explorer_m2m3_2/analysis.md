# Technical Architecture & Blueprint: Agentic Operations & Autonomous Tool Dispatch (Milestones M2/M3)

## 1. Executive Summary & Objective
This document provides the definitive architectural specification for upgrading the reactive "AI Copilot" into an autonomous **"Gemini Assistant"** within the SAMPATI V2 platform.

Milestones M2/M3 equip the assistant with:
1. **Live Gemini Function Calling** declarations enabling the LLM to autonomously invoke core platform operations.
2. **Deterministic Offline/Fallback Intent Router** using resilient regex and semantic parameter extraction when offline, without API keys, or when running heuristic fallbacks.
3. **Execution Handlers for 4 Core Operations**:
   - `block_vpa_or_transaction`: Immediate enforcement in HotState cache, Case DB, DPIP signal mesh, and Adaptive behavior models.
   - `trigger_federation_round`: Multi-PSP consensus round execution, ring clustering, and SAR attachment.
   - `export_sar_pdf`: Dynamic high-fidelity PDF artifact compilation with compliance ledger.
   - `simulate_transactions`: Synthetic labeled traffic generation, inline scoring, and anomaly detection.
4. **Enhanced API Contracts & Schemas**: Pydantic models with `tool_executions: List[ToolExecutionResult]` supporting zero-breaking-change backward compatibility.
5. **Comprehensive Unit & Integration Test Plan** validating tool routing, parameter extraction, and execution failure recovery.

---

## 2. Architectural Overview & Component Topology

```
+-----------------------------------------------------------------------------------+
|                              Analyst Client / UI                                  |
|         (CaseAiCopilotView.jsx / CaseDrawer.jsx / HTTP REST / WebSockets)        |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v  POST /cases/{case_id}/ai-chat
+-----------------------------------------------------------------------------------+
|                        app/api/upi.py (API Gateway Layer)                         |
|   - Resolves case from DB / Memory via UpiCaseService.get_case(case_id)           |
|   - Injects case context & invokes GeminiAssistantService.chat_with_case_assistant|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                  app/services/gemini_service.py (Assistant Layer)                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Context Assembly Engine:                                                   |  |
|  | - Case Raw Ledger + Evaluated Rules + Topology Graph + Encyclopedia KB      |  |
|  +-----------------------------------------------------------------------------+  |
|                                         |                                         |
|                    +--------------------+--------------------+                    |
|                    |                                         |                    |
|                    v (Online Mode with API Key)              v (Offline Fallback) |
|  +-----------------------------------+     +-----------------------------------+  |
|  | Live Gemini Function Calling      |     | Heuristic Intent Router           |  |
|  | - Declares 4 tools in payload     |     | - Regex & Semantic Pattern Match  |  |
|  | - Parses candidate functionCall   |     | - Extracts params (VPA, txns, etc)|  |
|  +-----------------+-----------------+     +-----------------+-----------------+  |
|                    |                                         |                    |
|                    +--------------------+--------------------+                    |
|                                         |                                         |
|                                         v                                         |
|  +-----------------------------------------------------------------------------+  |
|  |                       Tool Dispatch & Execution Engine                      |  |
|  | - _execute_block_vpa_or_transaction()                                       |  |
|  | - _execute_trigger_federation_round()                                       |  |
|  | - _execute_export_sar_pdf()                                                 |  |
|  | - _execute_simulate_transactions()                                          |  |
|  +--------------------------------------+--------------------------------------+  |
+-----------------------------------------|-----------------------------------------+
                                          |
                                          v Underlying Platform Services
+-----------------------------------------------------------------------------------+
|                   Core Platform Services & Storage Engines                        |
|  +-----------------------------+  +--------------------------------------------+  |
|  | UpiCaseService              |  | UpiHotState & Scorer                       |  |
|  | - update_case_status()      |  | - mark_confirmed_fraud()                   |  |
|  | - run_federation()          |  | - sliding window memory updates            |  |
|  | - simulate()                |  +--------------------------------------------+  |
|  | - generate_sar_pdf()        |  +--------------------------------------------+  |
|  +-----------------------------+  | DpipFeed & AdaptiveBehaviorModel           |  |
|  +-----------------------------+  | - publish_confirmed_ring()                 |  |
|  | Forensics: sar_pdf.py       |  | - ingest_external_signal()                 |  |
|  | - build_sar_pdf()           |  | - feedback(confirmed_fraud=True)           |  |
|  +-----------------------------+  +--------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Pydantic Models & API Schema Specifications

Target File: `app/models/upi_models.py`

### 3.1. `ToolExecutionResult` Schema
Captures structured metadata for any tool executed during a turn:
```python
class ToolExecutionResult(BaseModel):
    """Structured outcome and audit telemetry for an agentic tool execution."""
    tool_name: str = Field(..., description="Canonical identifier of the executed tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments parsed and passed to the executor")
    status: Literal["success", "error", "skipped"] = Field("success", description="Outcome status")
    result_summary: str = Field(..., description="Human-readable outcome summary")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Detailed structured output payload")
```

### 3.2. `GeminiChatResponse` (with Backward-Compatible `AiChatResponse`)
```python
class GeminiChatResponse(BaseModel):
    """Response returned from Gemini Assistant interactive chat."""
    case_id: str = Field(..., description="Target Case ID under investigation")
    question: str = Field(..., description="Analyst question or instruction prompt")
    answer: str = Field(..., description="Assistant response text formatted in clean Markdown")
    reply: Optional[str] = Field(None, description="Direct alias for answer")
    source: str = Field("gemini-ai", description="Generator source (gemini-ai, agentic-tool, heuristic-fallback)")
    model: Optional[str] = Field(None, description="LLM or heuristic engine identifier used")
    tool_executions: List[ToolExecutionResult] = Field(
        default_factory=list,
        description="List of platform tools autonomously executed during this chat interaction"
    )

    def __init__(self, **data: Any):
        # Automatically synchronize reply and answer fields
        if "answer" in data and not data.get("reply"):
            data["reply"] = data["answer"]
        elif "reply" in data and not data.get("answer"):
            data["answer"] = data["reply"]
        super().__init__(**data)

# Backward-compatible alias for existing imports and endpoint return types
AiChatResponse = GeminiChatResponse
```

---

## 4. Live Gemini Function Calling Schema Definitions

Target File: `app/services/gemini_service.py`

The Google Gemini API specification requires tool declarations to follow the `functionDeclarations` structure:

```python
GEMINI_TOOL_DECLARATIONS: List[Dict[str, Any]] = [
    {
        "name": "block_vpa_or_transaction",
        "description": (
            "Block, hold, or restrict a suspect UPI VPA or transaction in the hot state cache "
            "and case management database, propagate high-priority risk signals to DPIP, "
            "and apply behavioral feedback."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "case_id": {
                    "type": "STRING",
                    "description": "Unique identifier of the case (defaults to active case context).",
                },
                "target_vpa": {
                    "type": "STRING",
                    "description": "Specific VPA address to block/restrict (e.g., mule_account@okicici).",
                },
                "action": {
                    "type": "STRING",
                    "enum": ["BLOCK", "HOLD", "ESCALATE"],
                    "description": "Enforcement action level. Default is 'BLOCK'.",
                },
                "reason": {
                    "type": "STRING",
                    "description": "Compliance or forensic justification for the enforcement action.",
                },
            },
            "required": ["reason"],
        },
    },
    {
        "name": "trigger_federation_round",
        "description": (
            "Trigger an immediate Federated Intelligence consensus round across all participating "
            "PSP nodes (HDFC, ICICI, SBI, Axis, Paytm, etc.) to discover cross-PSP mule rings and sync threat hashes."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "case_id": {
                    "type": "STRING",
                    "description": "Case ID triggering this federation round for context tracking.",
                },
                "force_sync": {
                    "type": "BOOLEAN",
                    "description": "Force immediate consensus synchronization across all peer nodes.",
                },
            },
        },
    },
    {
        "name": "export_sar_pdf",
        "description": (
            "Generate and compile a formal, legally structured Suspicious Activity Report (SAR) PDF "
            "artifact compliant with FIU-IND and RBI DPIP regulatory standards."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "case_id": {
                    "type": "STRING",
                    "description": "The case ID for which to export the SAR PDF (defaults to active case).",
                },
            },
        },
    },
    {
        "name": "simulate_transactions",
        "description": (
            "Simulate and evaluate a synthetic stream of labeled UPI transactions through the "
            "multi-layer risk scoring pipeline to test detection thresholds or demonstrate platform behavior."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "total_txns": {
                    "type": "INTEGER",
                    "description": "Number of synthetic transactions to generate and evaluate (default: 50).",
                },
                "fraud_ratio": {
                    "type": "NUMBER",
                    "description": "Ratio of fraudulent transactions between 0.0 and 1.0 (default: 0.20).",
                },
                "seed": {
                    "type": "INTEGER",
                    "description": "Deterministic random seed for reproducibility.",
                },
                "run_federation": {
                    "type": "BOOLEAN",
                    "description": "Whether to automatically run a federation round after simulation (default: true).",
                },
            },
        },
    },
]
```

---

## 5. Tool Execution Handlers Specification

Each execution handler is responsible for executing the requested platform action safely, logging audit records, updating state, handling errors gracefully, and returning a `ToolExecutionResult`.

### 5.1. Handler 1: `_execute_block_vpa_or_transaction`
- **Method Signature**:
  ```python
  def _execute_block_vpa_or_transaction(
      self,
      case_data: Dict[str, Any],
      args: Dict[str, Any],
  ) -> ToolExecutionResult:
  ```
- **Logic Sequence**:
  1. Extract `case_id` from `args.get("case_id")` or `case_data.get("case_id")` (default: `"UNKNOWN_CASE"`).
  2. Resolve target VPA from `args.get("target_vpa")` or `case_data.get("payee_vpa")` or `case_data.get("payer_vpa")`.
  3. Resolve action (`"BLOCK"` / `"HOLD"` / `"ESCALATE"`, defaulting to `"BLOCK"`) and justification reason.
  4. Acquire `service = get_upi_case_service()`.
  5. If case exists in service:
     - Invoke `service.update_case_status(case_id=case_id, new_status="ESCALATED", notes=reason, resolution=f"ASSISTANT_{action}_ENFORCED", escalate_to_dpip=True)`.
  6. Apply hot state memory & DPIP updates directly:
     - `service.state.mark_confirmed_fraud([target_vpa])`
     - `service.dpip.ingest_external_signal(target_vpa, risk=1.0, source="GEMINI_ASSISTANT_TOOL")`
     - `service.adaptive.feedback([target_vpa], confirmed_fraud=True)`
  7. Construct and return `ToolExecutionResult`:
     ```python
     return ToolExecutionResult(
         tool_name="block_vpa_or_transaction",
         arguments={"case_id": case_id, "target_vpa": target_vpa, "action": action, "reason": reason},
         status="success",
         result_summary=(
             f"Enforced {action} on suspect VPA `{target_vpa}` and escalated Case `{case_id}` "
             f"with immediate DPIP threat propagation and behavioral memory blacklisting."
         ),
         data={
             "case_id": case_id,
             "target_vpa": target_vpa,
             "action": action,
             "status": "ESCALATED",
             "dpip_published": True,
             "adaptive_updated": True,
         }
     )
     ```

### 5.2. Handler 2: `_execute_trigger_federation_round`
- **Method Signature**:
  ```python
  def _execute_trigger_federation_round(
      self,
      case_data: Dict[str, Any],
      args: Dict[str, Any],
  ) -> ToolExecutionResult:
  ```
- **Logic Sequence**:
  1. Acquire `service = get_upi_case_service()`.
  2. Invoke `fed_result = service.run_federation()`.
  3. Extract metrics:
     - `rings = fed_result.get("rings", [])`
     - `new_rings = fed_result.get("new_rings", [])`
     - `nodes = fed_result.get("participating_nodes", ["okaxis", "okhdfcbank", "okicici", "paytm", "oksbi"])`
     - `suspicious = fed_result.get("suspicious", fed_result.get("suspicious_entities", []))`
     - `suspicious_count = len(suspicious) if isinstance(suspicious, list) else int(suspicious or 0)`
  4. Construct and return `ToolExecutionResult`:
     ```python
     return ToolExecutionResult(
         tool_name="trigger_federation_round",
         arguments=args,
         status="success",
         result_summary=(
             f"Federation intelligence consensus round completed across {len(nodes)} PSP nodes. "
             f"Identified {len(rings)} cross-PSP mule ring(s) ({len(new_rings)} new) and {suspicious_count} suspicious entities."
         ),
         data={
             "rings_detected": len(rings),
             "new_rings": len(new_rings),
             "participating_nodes": nodes,
             "suspicious_entities_count": suspicious_count,
             "timestamp": datetime.now(timezone.utc).isoformat(),
         }
     )
     ```

### 5.3. Handler 3: `_execute_export_sar_pdf`
- **Method Signature**:
  ```python
  def _execute_export_sar_pdf(
      self,
      case_data: Dict[str, Any],
      args: Dict[str, Any],
  ) -> ToolExecutionResult:
  ```
- **Logic Sequence**:
  1. Extract `case_id` from `args.get("case_id")` or `case_data.get("case_id")`.
  2. Acquire `service = get_upi_case_service()`.
  3. Fetch full case object `case_record = service.get_case(case_id) or case_data`.
  4. Generate PDF binary stream via `from app.forensics.sar_pdf import build_sar_pdf; pdf_bytes = build_sar_pdf(case_record)`.
  5. Compute payload size in kilobytes: `size_kb = len(pdf_bytes) / 1024.0`.
  6. Construct and return `ToolExecutionResult`:
     ```python
     return ToolExecutionResult(
         tool_name="export_sar_pdf",
         arguments={"case_id": case_id},
         status="success",
         result_summary=(
             f"Successfully compiled formal FIU-IND / RBI DPIP Suspicious Activity Report (SAR) PDF "
             f"({size_kb:.1f} KB) for Case `{case_id}`. Ready for regulatory dispatch."
         ),
         data={
             "case_id": case_id,
             "pdf_size_bytes": len(pdf_bytes),
             "pdf_size_kb": round(size_kb, 2),
             "download_url": f"/cases/{case_id}/sar/pdf",
             "filename": f"SAR_{case_id}.pdf",
         }
     )
     ```

### 5.4. Handler 4: `_execute_simulate_transactions`
- **Method Signature**:
  ```python
  def _execute_simulate_transactions(
      self,
      case_data: Dict[str, Any],
      args: Dict[str, Any],
  ) -> ToolExecutionResult:
  ```
- **Logic Sequence**:
  1. Parse parameters:
     - `total_txns = int(args.get("total_txns", args.get("count", 50)))`
     - `fraud_ratio = float(args.get("fraud_ratio", 0.20))`
     - `seed = int(args.get("seed", 42)) if args.get("seed") is not None else 42`
     - `run_federation = bool(args.get("run_federation", True))`
  2. Acquire `service = get_upi_case_service()`.
  3. Execute simulation stream: `sim_result = service.simulate(count=total_txns, fraud_ratio=fraud_ratio, seed=seed)`.
  4. If `run_federation`:
     - `fed_result = service.run_federation()`
     - `sim_result["federation_rings"] = len(fed_result.get("rings", []))`
  5. Construct and return `ToolExecutionResult`:
     ```python
     verdicts = sim_result.get("verdicts", {})
     opened = sim_result.get("opened_cases", 0)
     return ToolExecutionResult(
         tool_name="simulate_transactions",
         arguments={
             "total_txns": total_txns,
             "fraud_ratio": fraud_ratio,
             "seed": seed,
             "run_federation": run_federation
         },
         status="success",
         result_summary=(
             f"Generated and scored synthetic batch of {total_txns} transactions (Fraud Ratio: {fraud_ratio * 100:.0f}%). "
             f"Breakdown: {verdicts.get('ALLOW', 0)} ALLOW, {verdicts.get('HOLD', 0)} HOLD, {verdicts.get('BLOCK', 0)} BLOCK. "
             f"Opened {opened} new investigative case(s)."
         ),
         data=sim_result
     )
     ```

---

## 6. Offline / Fallback Intent Router Specifications

When the Gemini API key is unset, unreachable, or returns text instead of structured function calls for an action instruction, the **Deterministic Offline Intent Router** intercepts the prompt:

### 6.1. Regex Matching Patterns
```python
ROUTER_PATTERNS = {
    "trigger_federation_round": [
        re.compile(r"\b(?:trigger|run|start|execute|launch|initiate|sync)\b.*\b(?:federation|federated|consensus|mesh|cross-psp)\b", re.I),
        re.compile(r"\b(?:federation\s+round|run\s+federation|federated\s+intelligence)\b", re.I),
    ],
    "simulate_transactions": [
        re.compile(r"\b(?:simulate|generate|inject|create)\b.*\b(?:batch|stream|traffic|synthetic|transactions?)\b", re.I),
        re.compile(r"\b(?:simulate\s+(?:\d+|batch|stream))\b", re.I),
    ],
    "block_vpa_or_transaction": [
        re.compile(r"\b(?:block|freeze|hold|restrict|blacklist|quarantine|escalate)\b.*\b(?:vpa|account|payee|payer|transaction|node|entity|case)\b", re.I),
        re.compile(r"\b(?:block\s+vpa|freeze\s+account|escalate\s+case)\b", re.I),
    ],
    "export_sar_pdf": [
        re.compile(r"\b(?:export|generate|download|build|create|save|get)\b.*\b(?:sar|pdf|fiu|report|suspicious\s+activity)\b", re.I),
        re.compile(r"\b(?:sar\s+pdf|export\s+sar|download\s+sar)\b", re.I),
    ],
}
```

### 6.2. Parameter Extraction Engine
- **Transaction Count**: Extracts integers following `simulate`, `count`, or preceding `txns/transactions`:
  `re.search(r"(?:simulate|generate|run)\s+(\d+)", text, re.I)` -> e.g. "simulate 200 transactions" -> `200`.
- **Fraud Ratio**: Extracts percentages:
  `re.search(r"(\d+(?:\.\d+)?)\s*%", text)` -> e.g. "with 30% fraud" -> `0.30`.
- **Target VPA**: Extracts UPI handle strings:
  `re.search(r"[\w\.\-]+@[\w]+", text)` -> e.g. "block suspect mule_99@paytm" -> `"mule_99@paytm"`.
- **Action Type**:
  `"HOLD"` if "hold" in prompt else `"BLOCK"`.

### 6.3. Fallback Markdown Response Synthesis
When a tool is executed via the intent router, the assistant automatically synthesizes an authoritative Markdown response:
```markdown
### ⚡ Gemini Assistant Action Executed: `trigger_federation_round`

**Status**: ✅ Operation Completed Successfully

**Telemetry Summary**:
- **Participating PSP Nodes**: `okaxis`, `okhdfcbank`, `okicici`, `paytm`, `oksbi`
- **Cross-PSP Mule Rings Discovered**: **2** (1 newly formed)
- **Suspicious Conduit Entities Flagged**: **4**

**Forensic Impact**:
Updated privacy-preserving bloom filters and graph threat weights across all federated peer instances.
Updated SAR reports have been attached to Case `upi_case_test_01`.

*Next Recommended Step*: Review the ring topology constellation in the Graph tab or export Form 17B SAR PDF.
```

---

## 7. Deep Context Injection Integration

Target File: `app/services/gemini_service.py` & `app/engine/encyclopedia_kb.py`

When building the system prompt or user prompt for chat and briefings, the assistant dynamically injects the following context layers:
1. **Raw Case Transactions & Telemetry**: Amounts, timestamps, payer/payee VPAs, IP geolocation, Device IMEI, SIM IMSI.
2. **Evaluated Rule Breakdown**: Score contributions for `R_HONEYPOT_HIT`, `DMV_RAPID_DRAIN`, `R_SIM_DEVICE_MISMATCH`, etc.
3. **Graph Topology & Mule Ring Structure**: Number of hops, linked entities, fan-in/fan-out ratios.
4. **Encyclopedia Knowledge Base Context**: Calls `build_case_encyclopedia_context(case_data.get("rule_hits") or case_data.get("reasons"), metrics=case_data)` to append mathematical definitions (e.g. DMV formula, Dormancy Index, Drain Ratio, Gini coefficients) and plain English rationales.

---

## 8. Rebranding & Backward Compatibility Plan

To fulfill Requirement R1 and R3 seamlessly:

| Old Identifier | New Identifier | Compatibility Strategy |
|---|---|---|
| `GeminiCopilotService` | `GeminiAssistantService` | Define `GeminiCopilotService = GeminiAssistantService` alias |
| `get_gemini_copilot_service()` | `get_gemini_assistant_service()` | `get_gemini_copilot_service = get_gemini_assistant_service` |
| `chat_with_case_copilot()` | `chat_with_case_assistant()` | `chat_with_case_copilot = chat_with_case_assistant` method alias |
| `AiChatResponse` | `GeminiChatResponse` | Define `AiChatResponse = GeminiChatResponse` alias with `tool_executions` field |
| System Instructions | "You are SAMPATI Gemini Assistant..." | Updated across all system prompts |
| UI Header / Drawer Tabs | "Gemini Assistant" | Frontend strings updated with tool cards |

---

## 9. Comprehensive Unit Test Plan

Target Test Files: `tests/test_gemini_assistant_agentic.py` (New), additions to `tests/test_gemini_copilot.py` and `tests/test_e2e_suite.py`.

### 9.1. Test Cases Inventory

| Test ID | Test Name | Target Behavior | Expected Verification |
|---|---|---|---|
| **T-AGT-01** | `test_tool_definitions_schema` | Validates OpenAPI / Gemini JSON schema structure of all 4 tool declarations | Check parameter types, required fields, and non-empty descriptions |
| **T-AGT-02** | `test_intent_routing_federation` | Prompts: "Trigger a federation round", "Run federated consensus", "Execute federation" | Tool execution status is `"success"`, `tool_name == "trigger_federation_round"`, `tool_executions` non-empty |
| **T-AGT-03** | `test_intent_routing_simulation` | Prompts: "Simulate 100 transactions with 20% fraud", "Simulate synthetic batch" | `total_txns == 100`, `fraud_ratio == 0.20`, `tool_name == "simulate_transactions"`, opened cases recorded |
| **T-AGT-04** | `test_intent_routing_block_vpa` | Prompts: "Block payee VPA mule@icici", "Freeze suspect account", "Escalate case" | `tool_name == "block_vpa_or_transaction"`, target VPA marked in hot state fraud memory, case status is `ESCALATED` |
| **T-AGT-05** | `test_intent_routing_export_sar_pdf`| Prompts: "Export SAR to PDF", "Generate FIU report PDF", "Download SAR PDF" | `tool_name == "export_sar_pdf"`, valid PDF size > 0, `download_url` is `/cases/{case_id}/sar/pdf` |
| **T-AGT-06** | `test_mock_gemini_function_calling` | Mock HTTP 200 returning Gemini `functionCall` part for `trigger_federation_round` | Proper argument extraction, execution dispatch, and synthesis with `source == "gemini-ai"` |
| **T-AGT-07** | `test_tool_execution_error_recovery` | Tool execution with invalid/corrupt data | Tool status is `"error"`, error details logged in `result_summary`, chat endpoint does not raise 500 |
| **T-AGT-08** | `test_backward_compat_schema_aliases` | Verifies `GeminiCopilotService`, `get_gemini_copilot_service()`, `AiChatResponse` | All aliases instantiate properly and return valid schemas with `tool_executions` list |
| **T-AGT-09** | `test_encyclopedia_knowledge_in_chat` | Prompt: "Explain why DMV score spiked for this case" | Response contains mathematical formulas and algorithmic explanations from `ENCYCLOPEDIA.md` |
| **T-AGT-10** | `test_multi_turn_tool_state` | Consecutive turns with tool executions | History context is preserved and tool execution cards are reported |

---

## 10. Implementation Sequence & Next Steps
1. **Model Schemas**: Add `ToolExecutionResult` and `GeminiChatResponse` to `app/models/upi_models.py`.
2. **Assistant Service Core**: Implement `GeminiAssistantService` with tool declarations, execution handlers, and intent router in `app/services/gemini_service.py`.
3. **API Routing**: Update `/cases/{case_id}/ai-chat` in `app/api/upi.py` to return `tool_executions`.
4. **Unit Tests**: Add test suite `tests/test_gemini_assistant_agentic.py` and run full regression suite.
