# Backend Architectural Survey: AI Copilot to Gemini Assistant Upgrade

## 1. Executive Summary & Architectural Scope

The SAMPATI V2 platform currently incorporates a Gemini-powered copilot service (`GeminiCopilotService` in `app/services/gemini_service.py`) that generates executive fraud briefings, answers analyst queries about specific cases, and drafts FIU-IND compliant Suspicious Activity Report (SAR) narratives.

The objective of this upgrade is to evolve this component from a passive advisory copilot into an **autonomous "Gemini Assistant"** with:
1. **Deep Context Injection & Encyclopedia Knowledge Awareness**: Maximize forensic prompt context by extracting raw case transaction history, structured rule breakdowns, graph network topology, and core algorithmic definitions from `ENCYCLOPEDIA.md` (e.g., Dead Money Velocity, EWMA behavioral anomaly scoring, Haversine travel checks, honeypot traps).
2. **Autonomous Function Calling & Agentic Loop**: Equip the assistant with native Gemini tool declarations and an execution dispatch loop enabling it to autonomously:
   - Block or Hold a specific transaction/VPA (updating case state, hot state memory, and broadcasting threat signals).
   - Trigger a Federation Intelligence Round (`UpiCaseService.run_federation()`).
   - Export SAR PDF documents (`sar_pdf.build_sar_pdf()` / `/cases/{case_id}/sar/pdf`).
   - Simulate a new batch of synthetic transactions (`UpiCaseService.simulate()`).
3. **Resilient Heuristic Fallback with Intent Routing**: Ensure 100% offline functionality and zero regression when API keys are missing or the system is disconnected from the internet.
4. **Backend Rebranding**: Systematically transition all backend terminology from "AI Copilot" / "Copilot" to "Gemini Assistant" while maintaining backwards-compatible aliases.

---

## 2. Backend Endpoints & API Topology Survey

### 2.1 Endpoint Mounting Matrix
All AI-related endpoints are registered in two locations to ensure universal access across root routes and `/upi` prefix routes:
1. `app/api/upi.py` (mounted under prefix `/upi` in `app/main.py:182`)
2. `app/main.py` (mounted at the application root for convenience)

| HTTP Method | Route | Handler Function | Purpose |
|---|---|---|---|
| `GET`, `POST` | `/cases/{case_id}/ai-briefing`<br>`/upi/cases/{case_id}/ai-briefing` | `get_case_ai_briefing_root`<br>`get_case_ai_briefing` | Generates or refreshes executive forensic briefing, scam classification, and remediation actions. |
| `POST` | `/cases/{case_id}/ai-chat`<br>`/upi/cases/{case_id}/ai-chat` | `chat_with_case_ai_root`<br>`chat_with_case_ai` | Interactive context-aware analyst Q&A and agentic tool execution. |
| `GET`, `POST` | `/cases/{case_id}/ai-sar`<br>`/upi/cases/{case_id}/ai-sar` | `get_case_ai_sar_root`<br>`get_case_ai_sar` | Drafts regulatory FIU-IND compliant SAR narrative. |
| `GET` | `/cases/{case_id}/sar/pdf`<br>`/upi/cases/{case_id}/sar/pdf` | `get_case_sar_pdf_root`<br>`get_case_sar_pdf` | Exports complete SAR report as a PDF document. |
| `POST` | `/upi/federation/run` | `run_federation` | Triggers a cross-PSP federated intelligence consensus round. |
| `POST` | `/upi/simulate` | `simulate_traffic` | Simulates a batch of synthetic UPI transactions. |
| `PATCH` | `/cases/{case_id}/status`<br>`/upi/cases/{case_id}/status` | `update_case_status_root`<br>`update_upi_case_status` | Updates case status (reviewed, escalated, dismissed, open), triggering DPIP signals. |

### 2.2 Case Lookup Mechanism
Both `app/main.py` and `app/api/upi.py` use a two-tier lookup:
1. **Tier 1 (PostgreSQL DB)**: If SQLAlchemy async session is active, queries `UpiCaseModel` by `case_id` (`select(UpiCaseModel).where(UpiCaseModel.case_id == case_id)`).
2. **Tier 2 (In-Memory Hot State Cache)**: If DB returns `None` or raises an exception, retrieves the case dictionary from `UpiCaseService.get_case(case_id)`.
3. If neither produces a record, raises `HTTPException(status_code=404, detail=f"UPI case '{case_id}' not found")`.

### 2.3 Existing Request / Response Models (`app/models/upi_models.py`)
```python
class AiChatRequest(BaseModel):
    question: str = Field(..., description="Analyst query regarding the case")
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous conversation turns")

class AiChatResponse(BaseModel):
    case_id: str = Field(..., description="Target Case ID")
    question: str = Field(..., description="Analyst question asked")
    answer: str = Field(..., description="Gemini Assistant response text")
    source: str = Field("gemini-ai", description="Generator source")
    model: Optional[str] = Field(None, description="Model name used")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Executed tool operations")
```

---

## 3. LLM Service Layer Architecture (`app/services/gemini_service.py`)

### 3.1 Current Implementation Details
- **Class**: `GeminiCopilotService` (lines 177–656)
- **Singleton Accessor**: `get_gemini_copilot_service()`
- **API Base**: `https://generativelanguage.googleapis.com/v1beta/models`
- **Default Model**: `gemini-1.5-flash`
- **Fallback Hierarchy**: `["gemini-1.5-flash-8b", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-flash-latest", "gemini-pro-latest"]`
- **Cache**: In-memory LRU-bounded dictionary (max 500 entries) caching case briefings by `case_id`.

### 3.2 Network Resilience & Fallback Engine
When `GEMINI_API_KEY` is not set or network connectivity is unavailable:
1. `is_available()` returns `False`.
2. The service seamlessly redirects to local deterministic fallback handlers:
   - `_generate_fallback_briefing(case_data)`: Uses heuristic rule patterns and DMV scores to classify scams (e.g. Honeypot, SIM-swap, Dormant mule drain, Phishing campaign) and formulate remediation steps.
   - `_generate_fallback_chat_reply(case_data, question)`: Keyword-based intent classification answering queries about triggers, entities, DMV velocity, remediation, and SAR generation.
   - `_generate_fallback_sar_text(case_data)`: Generates formal FIU-IND compliant SAR text.
3. This guarantees **zero test failures** and **zero user-facing downtime** in offline environments.

---

## 4. Data Structures & Platform Models

### 4.1 Case Data Schema (`UpiCaseModel` / `UpiCaseService._cases[case_id]`)
Each case in the system contains:
```python
{
    "case_id": "upi_case_a1b2c3d4e5",
    "trigger_txn_id": "TXN_12345678",
    "trigger_txn": {
        "txn_id": "TXN_12345678",
        "timestamp": "2026-09-02T12:00:00Z",
        "amount": 75000.0,
        "payer_vpa": "victim@okhdfcbank",
        "payer_psp": "okhdfcbank",
        "payee_vpa": "mule_hub@icici",
        "payee_psp": "icici",
        "device_id": "DEV-998811",
        "sim_id": "SIM-445566",
        "ip": "192.168.1.50",
        "location": "Mumbai",
        "note": "Urgent verification fee",
        "txn_type": "P2P",
        "payee_is_new_for_payer": True,
        "payer_account_age_days": 450,
        "payee_vpa_age_days": 8,
    },
    "payer_vpa": "victim@okhdfcbank",
    "payee_vpa": "mule_hub@icici",
    "amount": 75000.0,
    "verdict": "HOLD",            # ALLOW | HOLD | BLOCK
    "risk_score": 85,             # 0 to 100
    "reasons": ["R_HONEYPOT_HIT", "PASS_THROUGH_CONDUIT"],
    "rule_hits": [
        {"code": "R_HONEYPOT_HIT", "points": 100, "detail": "Synthetic Honeypot Trap Hit"},
        {"code": "PASS_THROUGH_CONDUIT", "points": 30, "detail": "Rapid Conduit Pass-Through"}
    ],
    "adaptive_score": 0.82,       # EWMA anomaly score (0.0 to 1.0)
    "network_score": 0.75,        # Federation graph score (0.0 to 1.0)
    "dmv_score": 82.5,            # Dead Money Velocity score (0.0 to 100.0)
    "campaign_id": "CAMP-KYC-PHISH-01", # Active fraud campaign ID if matched
    "status": "OPEN",             # OPEN | REVIEWED | ESCALATED | DISMISSED | INVESTIGATED
    "ring_hash": "RING-7788AABB",
    "ring_members_vpas": ["mule_hub@icici", "conduit_2@ybl", "cashout_3@paytm"],
    "token_economy": { ... },     # Flow efficiency, velocity ratio, cashout proportion
    "topology": {
        "psps": ["okhdfcbank", "icici", "ybl", "paytm"],
        "member_count": 3,
        "total_amount": 185000.0,
        "fan_in": 2,
        "hops": 1,
        "fan_out": 1,
    },
    "sar_markdown": "...",
    "visual_path": "static/upi_cases/upi_case_a1b2c3d4e5_ring.png",
    "created_at": "2026-09-02T12:00:00Z",
    "resolution": None,
    "resolution_notes": None,
    "investigated_at": None,
}
```

---

## 5. Knowledge Base & Algorithmic Context Injection

### 5.1 Algorithmic Definitions Extracted from `ENCYCLOPEDIA.md`
To ensure the assistant can explain *exactly* why scores spiked or rules fired in plain English, the knowledge definitions below must be injected into the system prompt and context builder:

```python
ENCYCLOPEDIA_KNOWLEDGE = {
    "SCORER_ARCHITECTURE": (
        "SAMPATI uses a 3-Layer Composite Risk Scorer:\n"
        "• Layer 1 (Deterministic Rules): 0-100 pts from expert rule hits (white-box explainable).\n"
        "• Layer 2 (Adaptive EWMA Anomaly): 0-25 pts from online streaming z-score against historical moving mean & variance.\n"
        "• Layer 3 (Federation Graph Network): 0-40 pts from cross-PSP privacy-preserving hashed signal mesh.\n"
        "Verdict Thresholds: ALLOW (< 45 pts), HOLD (45-69 pts), BLOCK (>= 70 pts or network score >= 0.70)."
    ),
    "DMV_SCORE": (
        "Dead Money Velocity (DMV) quantifies how rapidly incoming funds are drained following an account dormancy period.\n"
        "Formula: f(dormancy_gap_hours, outflow_velocity_inr_hr, depletion_ratio).\n"
        "Risk Tiers: Normal (< 40), Elevated (40-69), Critical (>= 70).\n"
        "A critical DMV score indicates that a dormant account suddenly received funds and evacuated >= 90% within minutes, "
        "the defining signature of an active mule pass-through conduit."
    ),
    "RULES": {
        "R_HONEYPOT_HIT": "Payee VPA matches a registered synthetic honeypot trap. Triggers automatic 100 points and instant BLOCK.",
        "R_SIM_DEVICE_MISMATCH": "Hardware device fingerprint or SIM IMSI changed for known payer session (40 pts), indicating SIM-swap fraud or device spoofing.",
        "R_IMPOSSIBLE_TRAVEL": "Payer geographic location changed faster than 800 km/h calculated via Haversine great-circle distance (35 pts), indicating account takeover or credential sharing.",
        "R_DATACENTER_IP": "Transaction originated from a datacenter, cloud host (AWS/GCP/Azure/DO), VPN, or Tor exit node subnet (25 pts), indicating automated script/bot execution.",
        "R_CAMPAIGN_MATCH": "Transaction DNA matches an active syndicate fraud campaign signature with weighted cosine similarity >= 0.82 (30 pts).",
        "PASS_THROUGH_CONDUIT": "Account received funds and evacuated >= 90% of inflow within 30-day fresh account window (30 pts).",
        "FAN_IN_BURST": "Account received inflow from >= 5 distinct payers within the sliding window (25 pts), indicating a collector hub.",
        "FAN_OUT_DISPERSAL": "Account dispersed outflow to >= 5 distinct payees within the sliding window (25 pts), indicating a cash-out dispersal node.",
        "NEW_PAYEE_VPA": "Payee VPA created fewer than 15 days ago (25 pts).",
        "NEW_ACCOUNT_HIGH_VALUE": "Account < 30 days old initiating transfer >= INR 10,000 (25 pts).",
        "DEVICE_FARM": "Single hardware device ID or SIM ID linked to >= 3 distinct VPAs (20 pts).",
        "LIMIT_SKIRTING": "Amount sits within 2% below regulatory reporting thresholds (10 pts), indicating structuring/smurfing.",
        "KNOWN_FRAUD_ENTITY": "Entity VPA appears in historical confirmed fraud memory (35 pts).",
        "ADAPTIVE_ANOMALY": "EWMA streaming anomaly z-score >= 0.60 against rolling transaction baseline (up to 25 pts).",
    }
}
```

### 5.2 Deep Context Assembly Strategy
When building the prompt for `/cases/{case_id}/ai-briefing` or `/cases/{case_id}/ai-chat`:
1. **Format Trigger Transaction**: Include amount, currency (INR), timestamp, payer/payee VPAs, PSP handles, device ID, SIM ID, IP, location, and payment remarks.
2. **Format Rule Breakdown with Encyclopedia Explanations**: For every rule in `case_data["rule_hits"]` or `case_data["reasons"]`, retrieve the plain-English explanation from `ENCYCLOPEDIA_KNOWLEDGE["RULES"]` and pair it with the exact points and trigger details.
3. **Format DMV Analysis**: Include the numerical score, the category (Normal/Elevated/Critical), and the behavioral explanation.
4. **Format Graph Topology**: Include ring hash, total ring member count, member VPAs, graph hierarchy (victim -> fan-in collector -> layering hops -> fan-out cashout), total ring volume, and involved PSP institutions.

---

## 6. Agentic Operations & Function Calling Architecture

### 6.1 Supported Autonomous Operations
The Gemini Assistant will be equipped with 4 core tool capabilities:

| Operation | Tool Name | Parameters | Target Backend Invocation | Effect |
|---|---|---|---|---|
| **1. Block / Hold Entity** | `block_vpa`<br>`hold_case` | `vpa: str, reason: str`<br>`case_id: str, notes: str` | `state.mark_confirmed_fraud([vpa])`<br>`federation.record_signal(vpa_hash, 1.0)`<br>`dpip.ingest_external_signal(vpa, 1.0)`<br>`case_svc.update_case_status(case_id, "ESCALATED")` | Freezes VPA, publishes confirmed threat hash across Federation mesh, ingests to DPIP, and updates case status. |
| **2. Trigger Federation Round** | `trigger_federation_round` | `None` | `case_svc.run_federation()` | Executes cross-PSP consensus round, detects multi-PSP mule rings, generates SARs, and broadcasts `FEDERATION_ROUND` event. |
| **3. Export SAR to PDF** | `export_sar_pdf` | `case_id: str` | `case_svc.generate_sar_pdf(case_id)` | Builds formal FIU-IND SAR PDF using `sar_pdf.py` and returns download URL `/cases/{case_id}/sar/pdf`. |
| **4. Simulate Transactions** | `simulate_transactions` | `count: int = 50, fraud_ratio: float = 0.2` | `case_svc.simulate(count, fraud_ratio)` | Generates and evaluates labeled synthetic stream through the 3-layer inline scoring gate. |

### 6.2 Native Gemini Function Declarations Schema
```json
[
  {
    "name": "block_vpa",
    "description": "Block or freeze a malicious VPA account node and broadcast privacy-preserving threat signals to peer PSPs.",
    "parameters": {
      "type": "OBJECT",
      "properties": {
        "vpa": {"type": "STRING", "description": "The UPI VPA identifier to block"},
        "reason": {"type": "STRING", "description": "Forensic rationale for blocking"}
      },
      "required": ["vpa"]
    }
  },
  {
    "name": "hold_case",
    "description": "Place an investigative case on HOLD status pending compliance review.",
    "parameters": {
      "type": "OBJECT",
      "properties": {
        "case_id": {"type": "STRING", "description": "The case ID to put on hold"},
        "notes": {"type": "STRING", "description": "Investigator notes"}
      },
      "required": ["case_id"]
    }
  },
  {
    "name": "trigger_federation_round",
    "description": "Trigger a cross-PSP federated intelligence round to detect multi-institutional mule rings.",
    "parameters": {
      "type": "OBJECT",
      "properties": {}
    }
  },
  {
    "name": "export_sar_pdf",
    "description": "Generate and export the formal FIU-IND Suspicious Activity Report (SAR) as a PDF document.",
    "parameters": {
      "type": "OBJECT",
      "properties": {
        "case_id": {"type": "STRING", "description": "The case ID to export SAR PDF for"}
      },
      "required": ["case_id"]
    }
  },
  {
    "name": "simulate_transactions",
    "description": "Simulate a batch stream of synthetic UPI transactions through the inline risk scoring gate.",
    "parameters": {
      "type": "OBJECT",
      "properties": {
        "count": {"type": "INTEGER", "description": "Number of transactions to simulate (default 50)"},
        "fraud_ratio": {"type": "NUMBER", "description": "Ratio of fraudulent transactions (0.0 to 1.0, default 0.2)"}
      }
    }
  }
]
```

### 6.3 Tool Execution & Intent Routing Loop (Dual-Mode Execution)
1. **Remote Gemini API Mode**:
   - `_call_gemini` passes `tools=[{"functionDeclarations": TOOL_DECLARATIONS}]`.
   - When Gemini returns `functionCall` in candidate parts:
     - Dispatches call to corresponding Python handler.
     - Formats execution result.
     - Appends tool result to response and generates natural language summary.
2. **Offline / Fallback Heuristic Mode (Resilient Intent Routing)**:
   - When API key is not present or remote call fails, `_generate_fallback_chat_reply` inspects analyst question using regex/keyword matching:
     - `"federation"` or `"round"` -> triggers `case_svc.run_federation()` and formats ring/entity count.
     - `"simulate"` or `"simulation"` -> triggers `case_svc.simulate()` and formats processed/verdict count.
     - `"block"` or `"freeze"` -> blocks target VPA/case and formats confirmation.
     - `"sar pdf"` or `"export sar"` or `"download pdf"` -> verifies PDF generation and provides link.
     - `"dmv"` or `"dead money"` -> provides Encyclopedia explanation of DMV and case score.
     - `"why"` or `"rule"` or `"flag"` -> provides Encyclopedia explanation of all triggered rules.

---

## 7. Comprehensive Backend Rebranding Matrix

An exhaustive codebase search identified all occurrences of "AI Copilot" / "Copilot" requiring rebranding to "Gemini Assistant":

| File Path | Line Range | Current Identifier / String | Proposed Rebranding |
|---|---|---|---|
| `app/services/gemini_service.py` | 1 | `"""Gemini AI Fraud Analyst Copilot Service..."""` | `"""Gemini Assistant Autonomous Fraud Analyst Service..."""` |
| `app/services/gemini_service.py` | 177 | `class GeminiCopilotService:` | `class GeminiAssistantService:` (with `GeminiCopilotService = GeminiAssistantService` alias) |
| `app/services/gemini_service.py` | 395 | `async def chat_with_case_copilot(...)` | `async def chat_with_case_assistant(...)` (with `chat_with_case_copilot` alias) |
| `app/services/gemini_service.py` | 415 | `"You are SAMPATI AI Copilot..."` | `"You are SAMPATI Gemini Assistant, an autonomous Senior Financial Crime & AML Intelligence Analyst..."` |
| `app/services/gemini_service.py` | 660 | `def get_gemini_copilot_service():` | `def get_gemini_assistant_service():` (with `get_gemini_copilot_service` alias) |
| `app/models/upi_models.py` | 284 | `# --- Gemini AI Copilot Models ---` | `# --- Gemini Assistant Models ---` |
| `app/models/upi_models.py` | 301 | `"""Request payload for interactive analyst chat with case copilot."""` | `"""Request payload for interactive analyst chat with Gemini Assistant."""` |
| `app/models/upi_models.py` | 310 | `answer: str = Field(..., description="AI Copilot response text")` | `answer: str = Field(..., description="Gemini Assistant response text")` |
| `app/api/upi.py` | 88 | `from app.services.gemini_service import get_gemini_copilot_service` | `from app.services.gemini_service import get_gemini_assistant_service, get_gemini_copilot_service` |
| `app/api/upi.py` | 377 | `summary="Interactive Case AI Copilot Chat"` | `summary="Interactive Case Gemini Assistant Chat"` |
| `app/main.py` | 293, 324, 367 | `from app.services.gemini_service import get_gemini_copilot_service` | `from app.services.gemini_service import get_gemini_assistant_service, get_gemini_copilot_service` |
| `app/main.py` | 323 | `"""Interactive context-aware chat with AI Copilot..."""` | `"""Interactive context-aware chat with Gemini Assistant..."""` |

---

## 8. Test Infrastructure & Verification Plan

### 8.1 Existing Test Suite Baseline
- **Total Pytest Tests**: 737 tests passing (0 failures, 6 minor font warnings in PDF test).
- **Dedicated Gemini Test Suite**: `tests/test_gemini_copilot.py` (27 unit and integration tests passing in 2.29s).

### 8.2 New Test Cases for Gemini Assistant
To satisfy acceptance criteria, `tests/test_gemini_copilot.py` should be expanded with:
1. `test_gemini_assistant_tool_routing_federation`: Verifies asking "Trigger a federation round" calls backend federation logic and returns discovered rings count.
2. `test_gemini_assistant_tool_routing_simulation`: Verifies asking "Simulate 25 transactions" drives synthetic transactions and returns verdict distribution.
3. `test_gemini_assistant_tool_routing_block_vpa`: Verifies asking "Block payee_vpa@xyz" marks fraud in hot state and returns confirmation.
4. `test_gemini_assistant_tool_routing_export_sar`: Verifies asking "Export SAR PDF" generates PDF bytes and returns file path.
5. `test_gemini_assistant_encyclopedia_context_dmv`: Verifies asking "Explain why the DMV score spiked" incorporates algorithmic definitions (dormancy gap, velocity, depletion).
6. `test_gemini_assistant_encyclopedia_rule_explanations`: Verifies system context includes plain-English definitions for all triggered rules (Honeypot, Impossible Travel, Pass-Through Conduit).
7. `test_backwards_compatibility_aliases`: Verifies `GeminiCopilotService`, `get_gemini_copilot_service()`, and `chat_with_case_copilot()` continue to work seamlessly.
