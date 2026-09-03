# DISPATCH: teamwork_preview_explorer_m1_2

## Identity
- Role: Explorer 2 for Milestone 1 (Central Fraud Graph & Threat Intel Service)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2
- Parent: teamwork_preview_orchestrator_11

## Mission & Inputs
- Read authoritative request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (lines 336–379, R1 Early Warning Intelligence Layer).
- Read project scope & architecture: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`.
- Read previous survey findings: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md`.
- Inspect existing services: `app/engine/campaign.py`, `app/services/upi_cases.py`, `app/api/websocket.py`.

## Assignment
1. Investigate and specify the Central Fraud Graph Service in `app/services/graph_service.py`:
   - Use `networkx.DiGraph` (networkx is verified installed at version 3.6.1).
   - Node types: `VPA`, `PHONE`, `URL`, `CAMPAIGN`, `CASE`, `SIGNAL`.
   - Edge types: `EXTRACTED_FROM`, `ASSOCIATED_WITH`, `TRANSACTED_TO`, `MEMBER_OF_CAMPAIGN`, `LINKED_TO_CASE`.
   - Methods: `add_threat_signal(signal_data)`, `link_vpa_to_case(vpa, case_id)`, `get_subgraph(entity_id, depth=2)`, `export_graph() -> dict(nodes, edges)`, `get_stats()`.
   - Thread-safe singleton `get_fraud_graph()`.
2. Investigate and specify `ThreatIntelService` in `app/services/threat_intel_service.py`:
   - Dual-mode storage: thread-safe in-memory dictionary `_signals` + asynchronous/optional DB session persistence.
   - Campaign matching: calculate token/keyword similarity against `FRAUD_KEYWORD_CLUSTERS` from `app/engine/campaign.py` (e.g., match "Bank impersonation" + "KYC" to `CAMP-KYC-PHISH-01` with ~94% similarity).
   - Graph linkage: automatically add nodes/edges to `FraudGraphService`. If UPI ID or phone matches an existing case or ring, link them immediately.
   - Real-time broadcast: call `broadcast_event("THREAT_SIGNAL_RECEIVED", signal_dict)` via `app/api/websocket.py`.
   - Simulation helper: `simulate_signals(count=5)` for seeding realistic threat signals.
   - Thread-safe singleton `get_threat_intel_service()`.
3. Write your complete findings and implementation plan to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/handoff.md`.
4. Report completion back to parent via `send_message`.

## 2026-09-03T10:12:04Z
- User request received:
Investigate and design:
1. Central Fraud Graph Service in `app/services/graph_service.py` using `networkx.DiGraph`. Include node types (VPA, PHONE, URL, CAMPAIGN, CASE, SIGNAL), edge types, graph export, and singleton getter.
2. Threat Intel Service in `app/services/threat_intel_service.py`: signal ingestion, regex extraction coordination, campaign matching (using `app/engine/campaign.py` keyword clusters -> ~94% similarity for KYC phishing), graph updates, WebSocket broadcast, and in-memory caching.
Write findings and technical specifications to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/handoff.md`.
Report completion back to parent via `send_message`.
