# BRIEFING — 2026-09-03T10:12:04Z

## Mission
Investigate and design the Central Fraud Graph Service (`app/services/graph_service.py`) and Threat Intel Service (`app/services/threat_intel_service.py`) for Milestone 1.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis, API design
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2
- Original parent: 708f3126-0948-4197-8593-5296c58527f6
- Milestone: M1 (Encyclopedia Knowledge Base)
- Updated Parent: 93ffe563-3fed-400b-b381-966248be98c4
- Milestone: M1 (Early Warning Threat Intel & Central Fraud Graph)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in app/
- Provide complete code blueprint and interface specification
- Standalone, fast, robust, no circular imports
- Thread-safe singleton pattern for services
- networkx.DiGraph based fraud graph
- Backward compatibility: zero regression on existing 833+ test suite

## Current Parent
- Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4
- Updated: 2026-09-03T10:12:04Z

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`, `PROJECT.md`, `teamwork_preview_explorer_survey_1/handoff.md`, `DISPATCH.md`
  - `app/engine/campaign.py` (FRAUD_KEYWORD_CLUSTERS, CampaignSignatureStore, similarity weights)
  - `app/services/upi_cases.py` (_cases cache, _schedule_db_save_case, emit_case_broadcast)
  - `app/api/websocket.py` (schedule_broadcast, broadcast_event, connection manager)
  - `app/federation/coordinator.py` (_rings, pseudonymize, current_rings)
  - `app/models/upi_persistence.py` (ThreatSignalModel, Base, AsyncSession)
- **Key findings**:
  - Designed `FraudGraphService` (`app/services/graph_service.py`) on `networkx.DiGraph` with 6 node types (`VPA`, `PHONE`, `URL`, `CAMPAIGN`, `CASE`, `SIGNAL`) and 5 edge types (`EXTRACTED_FROM`, `ASSOCIATED_WITH`, `TRANSACTED_TO`, `MEMBER_OF_CAMPAIGN`, `LINKED_TO_CASE`), ego-graph subgraph extraction, stats calculation, and thread-safe singleton `get_fraud_graph()`.
  - Designed `ThreatIntelService` (`app/services/threat_intel_service.py`) with dual-mode storage (thread-safe in-memory cache + async DB session persistence), regex entity extraction (Indian phone, UPI VPA, URL, tags), multi-factor campaign matching calibrated to ~94% similarity for KYC phishing attacks, graph linkage, WebSocket broadcast (`THREAT_SIGNAL_RECEIVED`), simulation helper (`simulate_signals(count=5)`), and singleton `get_threat_intel_service()`.
- **Unexplored areas**: None for M1_2 scope.

## Key Decisions Made
- Authored full Python drop-in code blueprints for both services in `analysis.md`.
- Completed 5-component handoff report in `handoff.md`.
- Successfully validated code blueprints and handoff assertions via Python execution.

## Artifact Index
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/DISPATCH.md` — Inbound task dispatch
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/BRIEFING.md` — Working memory
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/progress.md` — Liveness & progress tracking
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/analysis.md` — Detailed analysis and complete code blueprint
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/handoff.md` — 5-component handoff report

