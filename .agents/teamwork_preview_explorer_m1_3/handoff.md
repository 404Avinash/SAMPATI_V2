# Handoff Report: Milestone M1 — Prompt Injection Format & Unit Test Suite Design

**Author:** Explorer 3 (`teamwork_preview_explorer_m1_3`)  
**Parent / Recipient:** Orchestrator (`708f3126-0948-4197-8593-5296c58527f6`)  
**Artifact Path:** `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_3/analysis.md`  
**Date:** 2026-09-02T17:49:00Z  

---

## 1. Observation
1. **Encyclopedia Rule & Algorithmic Inventory (`ENCYCLOPEDIA.md:321-438`)**:
   - The platform defines 13 deterministic rules in `app/engine/upi_rules.py` (`R_HONEYPOT_HIT`, `R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`, `R_CAMPAIGN_MATCH`, `NEW_PAYEE_VPA`, `PASS_THROUGH_CONDUIT`, `FAN_IN_BURST`, `FAN_OUT_DISPERSAL`, `DEVICE_FARM`, `NEW_ACCOUNT_HIGH_VALUE`, `LIMIT_SKIRTING`, `KNOWN_FRAUD_ENTITY`), plus adaptive EWMA (`app/engine/adaptive.py`), Dead Money Velocity (`app/engine/dmv.py`), campaign DNA fingerprinting (`app/engine/campaign.py`), and federated mule ring graph analysis (`app/services/upi_cases.py`).
2. **Current System Prompt & Context Deficit (`app/services/gemini_service.py:308-326, 414-420, 480-493`)**:
   - Currently, `GeminiCopilotService` passes raw JSON `case_data` to Gemini prompts without explaining mathematical formulas, thresholds, or forensic typologies for why specific rules fired. This causes LLMs to generate generic or heuristic summaries.
3. **Target Interface Contract (`PROJECT.md:55-63`)**:
   - `get_rule_explanation(rule_code: str, metric_value: float = None, context: dict = None) -> dict` returning `rule_code`, `name`, `mathematical_definition`, `plain_english_explanation`, `severity`, `default_points`, `regulatory_typology`.
   - `build_case_encyclopedia_context(evaluated_rules: list, metrics: dict = None) -> str` generating formatted markdown for system prompt injection.
4. **Existing Test Infrastructure (`tests/`)**:
   - The repository uses `pytest` across Python 3.14 with standard `unittest.TestCase` / `unittest.IsolatedAsyncioTestCase` patterns and 559+ passing tests.

---

## 2. Logic Chain
1. **Prompt Comprehension & Token Economy Optimization**:
   - *Observation Reference*: Ingesting raw JSON (`gemini_service.py:326`) requires LLMs to deduce complex rule semantics without domain knowledge.
   - *Reasoning*: Introducing a Two-Tier Markdown structure (Tier 1: High-density summary table; Tier 2: Deep per-rule algorithmic and mathematical breakdown) minimizes prompt token bloat (~150-250 tokens/rule) while maximizing factual grounding and mathematical fidelity.
2. **Dynamic Metric Interpolation**:
   - *Observation Reference*: `PROJECT.md:57` requires `metric_value` and `context` parameters.
   - *Reasoning*: A static dictionary of strings cannot explain *why* a specific score (e.g. `DMV=82.5`, `EWMA=0.92`, `speed=1250km/h`) occurred. Dynamic interpolation string templates ensure exact runtime metrics are formatted with currency symbols (₹), percentages, and unit measures.
3. **Alias Normalization & Fallback Safety**:
   - *Observation Reference*: Rule hits may arrive as raw strings (`"dmv"`, `"structuring"`, `"mule"`), dictionaries (`{"code": "...", "detail": "..."}`), or `RuleHit` dataclasses (`upi_rules.py:19`).
   - *Reasoning*: The engine must normalize case variations, hyphens/underscores, and known aliases to canonical codes in $O(1)$ time, while unindexed or malformed inputs must return safe fallback dictionaries to guarantee zero runtime crashes.
4. **Unit Test Suite Completeness**:
   - *Observation Reference*: Acceptance criteria require comprehensive coverage of all known codes, unknown fallbacks, interpolation, context building, and zero latency regressions.
   - *Reasoning*: Designed an 8-group, 25+ case unit test suite blueprint (`tests/test_encyclopedia_kb.py`) asserting schema conformity, LaTeX math representation, metric presence, edge case handling, and sub-millisecond execution (< 1ms).

---

## 3. Caveats
- **Read-Only Investigation Scope**: Per agent instructions, no source files in `app/` or `tests/` were directly created or modified during this investigation. The full analysis, prompt templates, and unit test code blueprint are published in `.agents/teamwork_preview_explorer_m1_3/analysis.md`.
- **Milestone Scope Isolation**: Prompt injection updates to `app/services/gemini_service.py` belong to Milestone M2; this deliverable specifies the format, prompt templates, and integration contracts for M2 implementers.

---

## 4. Conclusion
- The prompt injection format for `app/engine/encyclopedia_kb.py` is fully designed with a Two-Tier markdown format (Summary Table + Mathematical / Forensic Breakdown per rule).
- All 18 platform rules, models, and graph heuristics have canonical mathematical definitions and plain-English detection rationales mapped.
- Dynamic metric interpolation handles scalar numbers, currency amounts, percentages, and multi-key context dictionaries.
- A comprehensive unit test suite blueprint (`tests/test_encyclopedia_kb.py`) has been authored and documented in `analysis.md`.

---

## 5. Verification Method
1. **Inspect Analysis Deliverables**:
   - View `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_3/analysis.md` for full prompt templates, rule dictionary, metric interpolation specs, and unit test code blueprint.
2. **Independent Verification of Unit Test Plan**:
   - When implementer creates `app/engine/encyclopedia_kb.py` and `tests/test_encyclopedia_kb.py`, run:
     ```bash
     ./.venv/bin/pytest tests/test_encyclopedia_kb.py -v
     ./.venv/bin/pytest
     ./.venv/bin/ruff check app tests
     ```
   - Invalidation conditions: Any test failure, average latency exceeding 1.0ms, or unhandled exceptions on malformed rule inputs.
