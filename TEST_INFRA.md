# E2E Test Infra: SAMPATI_V2 Gemini Assistant Upgrade

## Test Philosophy
- Opaque-box, requirement-driven, derived strictly from `ORIGINAL_REQUEST.md`.
- Verifies:
  1. Deep context injection in `/cases/{case_id}/ai-briefing` and `/cases/{case_id}/ai-chat` (transactions, rules, topology, Encyclopedia definitions).
  2. Autonomous agentic operations (Federation trigger, Simulation batch, Block/Hold VPA/Txn, SAR PDF export) via chat endpoint and intent routing.
  3. Frontend branding to "Gemini Assistant" and UI rendering of tool execution statuses in chat log.
  4. Non-regression of existing 737+ pytest test suite and frontend ESLint/Build.

## Feature Inventory & Test Matrix
| # | Feature | Source (Requirement) | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Scenario) |
|---|---------|----------------------|:----------------:|:-----------------:|:-----------------:|:-----------------:|
| 1 | Encyclopedia KB & Algorithmic Explanations | R1 | 5 | 5 | ✓ | ✓ |
| 2 | Deep Context Injection in Briefing/Chat | R1 | 5 | 5 | ✓ | ✓ |
| 3 | Backend Rebranding (Gemini Assistant) | R1 | 5 | 5 | ✓ | ✓ |
| 4 | Agentic Tool: Block / Hold VPA & Txn | R2(a) | 5 | 5 | ✓ | ✓ |
| 5 | Agentic Tool: Trigger Federation Round | R2(b) | 5 | 5 | ✓ | ✓ |
| 6 | Agentic Tool: Export SAR to PDF | R2(c) | 5 | 5 | ✓ | ✓ |
| 7 | Agentic Tool: Simulate Transaction Batch | R2(d) | 5 | 5 | ✓ | ✓ |
| 8 | Frontend Rebranding & Tool Status UI | R3 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Unit/Integration Test Suite: `tests/test_gemini_assistant.py` (executed via `./.venv/bin/pytest tests/test_gemini_assistant.py -v`)
- E2E Test Suite: `tests/test_e2e_gemini_assistant.py` (executed via `./.venv/bin/pytest tests/test_e2e_gemini_assistant.py -v`)
- Full Regression Test: `./.venv/bin/pytest tests/ -v` (737+ tests)
- Frontend Checks: `cd frontend && npm run lint && npm run build`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Expected Outcome |
|---|----------|--------------------|------------------|
| 1 | Analyst asks "Explain why DMV score spiked for case X" | Encyclopedia KB + Context Injection | Assistant details dormancy gap, outflow velocity, math formula, and plain English explanation |
| 2 | Analyst commands "Trigger a federation round to sync intelligence" | Agentic Tool: Federation Round | Assistant triggers federation coordinator, returns success summary and structured tool execution object |
| 3 | Analyst commands "Simulate a batch of 50 mule transactions" | Agentic Tool: Simulation Batch | Assistant executes simulation stream, returns generated counts, anomalies detected, and tool execution status |
| 4 | Analyst commands "Block VPA suspect@upi and export SAR to PDF" | Agentic Tool: Block + SAR PDF | Assistant marks VPA frozen in hot state, compiles PDF SAR, and returns download link / summary |
| 5 | Full investigation cycle from briefing to mitigation | All Features | Analyst gets enriched briefing, asks clarifying algorithm questions, triggers federation, blocks suspect, verifies frontend card display |

## Coverage Thresholds
- Tier 1: ≥5 per feature
- Tier 2: ≥5 per feature
- Tier 3: Pairwise coverage of multi-tool queries and combined context queries
- Tier 4: ≥5 realistic operational scenarios
