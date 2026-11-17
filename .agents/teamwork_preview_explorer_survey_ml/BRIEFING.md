# BRIEFING — 2026-09-05T03:37:30+05:30

## Mission
Conduct an exhaustive architectural survey of the ML and Generative AI subsystems in SAMPATI V2 (covering app/ml, app/rules, app/services, ensemble logic, and Gemini GenAI integration) and produce a comprehensive technical report and handoff.

## 🔒 My Identity
- Archetype: explorer
- Roles: Teamwork explorer (ML & AI Engine Architecture Explorer)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ml
- Original parent: d7ee2688-0be6-4bc5-b9ec-8b4f7ccf2e64
- Milestone: ML & AI Subsystem Survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement or modify project source code
- Write analysis artifacts only in .agents/teamwork_preview_explorer_survey_ml
- Document exact file paths, line references, code snippets, mathematical formulas, feature lists, and prompt templates
- Complete 5-component handoff report (handoff.md) and send message to parent upon completion

## Current Parent
- Conversation ID: d7ee2688-0be6-4bc5-b9ec-8b4f7ccf2e64
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `app/engine/upi_rules.py`, `app/engine/dmv.py`, `app/engine/campaign.py`, `app/engine/honeypot.py`
  - `app/engine/isolation_forest.py`
  - `app/engine/supervised_classifier.py`, `app/engine/train_supervised.py`
  - `app/engine/upi_scorer.py`, `app/engine/encyclopedia_kb.py`
  - `app/services/gemini_service.py`, `app/services/threat_intel_service.py`, `app/services/upi_cases.py`
  - `app/forensics/sar_pdf.py`, `app/forensics/upi_sar.pyc`, `app/forensics/token_economy.pyc`
  - `tests/test_isolation_forest.py`, `tests/test_supervised_model.py`, `tests/test_gemini_copilot.py`, `tests/test_gemini_assistant_agentic.py`
- **Key findings**:
  - Layer 1 employs deterministic rules (honeypots, impossible travel, SIM/device swaps, datacenter IPs, campaign DNA) and an advanced Dead Money Velocity (DMV) state machine with non-linear synergistic escalation.
  - Layer 2 implements the canonical Liu et al. (2008) Isolation Forest in pure NumPy (50 trees, max depth 7) with a normalized zero-regression baseline and 13 standardized features.
  - Layer 3 implements a pure NumPy Random Forest classifier (30 trees, max depth 6, Gini splitting, class-weight balanced bootstrap) trained on PaySim benchmark data, achieving 0.9627 F1 and an 83.3% relative False Negative reduction over Isolation Forest alone.
  - Ensemble scoring arbitrates across Layer 1 (0-100 pts), Layer 2 Adaptive (0-25 pts), Layer 3 Network (0-40 pts), and Layer 2 ML (0-25 pts), with strict override floors (ML >= 0.85, Supervised >= 0.85, Network >= 0.70 force HOLD).
  - Layer 4 integrates Google Gemini 1.5 Flash (with fallback hierarchy) for automated forensic briefings, multimodal context compression (333 tokens vs 15k text tokens, 45x ratio), autonomous agentic tool execution, and two-page FIU-IND Form 17B SAR PDF generation with deterministic offline intent routing fallbacks.
- **Unexplored areas**: None within ML/AI scope; full investigation completed.

## Key Decisions Made
- Conducted deep code-level analysis verifying actual formulas, thresholds, feature sets, prompt structures, and test suites.
- Compiled an exhaustive 9-section master architectural survey to `report.md`.

## Artifact Index
- `report.md` — Exhaustive architectural report on ML & GenAI subsystems
- `handoff.md` — 5-component handoff report for orchestrator
- `progress.md` — Milestone tracking and heartbeat
- `DISPATCH.md` — Initial task dispatch archive

