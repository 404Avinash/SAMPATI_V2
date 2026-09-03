# DISPATCH: teamwork_preview_worker_m1

## Identity
- Role: Worker for Milestone 1 (Backend Early Warning Threat Intelligence Layer)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1
- Parent: teamwork_preview_orchestrator_11 (Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4)

## Mandatory Integrity Warning
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Mission & Inputs
- Read authoritative request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (lines 336–379, R1 Early Warning Intelligence Layer).
- Read project scope & architecture: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`.
- Read Explorer 1 blueprints: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/handoff.md` and `analysis.md`.
- Read Explorer 2 blueprints: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/handoff.md` and `analysis.md`.
- Read Explorer 3 blueprints: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_3/handoff.md` and `analysis.md`.

## File Ownership (Exclusively owned by this Worker)
1. `app/models/threat_intel.py`
2. `app/models/upi_persistence.py` (add `ThreatSignalModel`)
3. `app/services/graph_service.py`
4. `app/services/threat_intel_service.py`
5. `app/api/intel.py`
6. `app/main.py` (mount router, update `api_prefixes` with route disambiguation)
7. `tests/test_threat_intel_r1.py`

## Detailed Implementation Tasks
1. **`app/models/threat_intel.py`**:
   - Pydantic models: `ThreatSignalCreateRequest`, `ExtractedEntities`, `CampaignMatch`, `ThreatSignalResponse`, `ThreatSignalListResponse`, `ThreatGraphResponse`, `GraphNode`, `GraphEdge`, `ThreatSimulateRequest`, `ThreatSimulateResponse`.
   - Pure-Python regex entity extractor `extract_entities(text)` for:
     * Indian phones: 10 digits starting with [6-9], optional +91/0 prefix, boundary guards preventing 12-digit UTR confusion.
     * UPI VPAs: `username@handle` format, boundary guards excluding standard email domains.
     * URLs: `http://`, `https://`, IP-based URLs, phishing TLDs (`.xyz`, `.top`, `.online`, etc.).
     * Social engineering tags: 8 categories ("Bank impersonation", "KYC suspension", "Urgency", "Lottery/Reward", "Electricity/Bill", "APK/Malware", "Investment/Job", "Refund/Delivery").

2. **`app/models/upi_persistence.py`**:
   - Add `ThreatSignalModel` inheriting from `Base` (table `threat_signals`).
   - Fields: `id`, `signal_id`, `source`, `phone`, `upi_id`, `url`, `tags`, `raw_content`, `severity`, `confidence`, `extracted_entities`, `matched_campaign_id`, `matched_campaign_name`, `similarity_score`, `case_id`, `ring_hash`, `created_at`.
   - Four compound indexes, `__init__`, and `to_dict()` with safe fallbacks for SQLite/PostgreSQL/in-memory.

3. **`app/services/graph_service.py`**:
   - `FraudGraphService` using `networkx.DiGraph`.
   - Node types: `VPA`, `PHONE`, `URL`, `CAMPAIGN`, `CASE`, `SIGNAL`.
   - Edge types: `EXTRACTED_FROM`, `ASSOCIATED_WITH`, `TRANSACTED_TO`, `MEMBER_OF_CAMPAIGN`, `LINKED_TO_CASE`.
   - Methods: `add_threat_signal`, `link_vpa_to_case`, `get_subgraph`, `export_graph`, `get_stats`.
   - Singleton `get_fraud_graph()`.

4. **`app/services/threat_intel_service.py`**:
   - `ThreatIntelService` with dual-mode storage: thread-safe in-memory cache `_signals` + async DB persistence when session available.
   - Entity extraction coordination, campaign matching (against `FRAUD_KEYWORD_CLUSTERS` from `app/engine/campaign.py` calibrated to ~94% similarity for KYC phishing).
   - Central fraud graph updates, real-time WebSocket broadcast (`THREAT_SIGNAL_RECEIVED`), `simulate_signals(count=5)`.
   - Singleton `get_threat_intel_service()`.

5. **`app/api/intel.py`**:
   - APIRouter with endpoints:
     * `POST /signals` (201 Created)
     * `GET /signals` (filters: severity, source, campaign_id, pagination: limit, offset)
     * `GET /signals/{signal_id}` (200 OK or 404)
     * `GET /graph` (full graph or entity subgraph)
     * `GET /campaigns` (campaign metrics)
     * `POST /simulate` (synthetic signal ingestion)

6. **`app/main.py`**:
   - Import `from app.api import intel as intel_router`.
   - Mount router:
     * `app.include_router(intel_router.router, prefix="/intel", tags=["Threat Intel"])`
     * `app.include_router(intel_router.router, prefix="/threat-intel", tags=["Threat Intel"])`
     * `app.include_router(intel_router.router, prefix="/upi/intel", tags=["Threat Intel"])`
   - Update `spa_fallback_404_handler`:
     * Ensure `api_prefixes` includes `"/intel"` and `"/threat-intel"`.
     * Add disambiguation for direct React UI navigation to `/threat-intel` vs API requests:
       `is_ui_page = path in ("/threat-intel", "/threat-intel/")`
       `is_api = any(path.startswith(prefix) for prefix in api_prefixes) and not is_ui_page`
       `if not is_api and not has_extension and os.path.isfile(_index_html): return FileResponse(_index_html)`

7. **`tests/test_threat_intel_r1.py`**:
   - Implement comprehensive 30+ test suite covering validation, regex extraction, campaign similarity (~94%), graph linkage, API routes (201, 200, 404, 422), and SPA fallback disambiguation.

8. **Verification & Testing (MANDATORY)**:
   - Run new tests: `./.venv/bin/pytest tests/test_threat_intel_r1.py -v`
   - Run linter: `./.venv/bin/ruff check app tests`
   - Run full regression suite: `./.venv/bin/pytest tests/ -q`
   - Document exact commands and passing outputs in your handoff report.

9. Write complete handoff report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`.
10. Send message to parent upon completion.

## 2026-09-03T10:20:35Z
You are teamwork_preview_worker_m1.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1.
Read your instructions at /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/DISPATCH.md.
Also read:
- /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/handoff.md (and analysis.md)
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_2/handoff.md (and analysis.md)
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_3/handoff.md (and analysis.md)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement:
1. `app/models/threat_intel.py`
2. `ThreatSignalModel` in `app/models/upi_persistence.py`
3. `app/services/graph_service.py`
4. `app/services/threat_intel_service.py`
5. `app/api/intel.py`
6. Router mounting and SPA fallback disambiguation in `app/main.py`
7. Comprehensive test suite in `tests/test_threat_intel_r1.py`

Run test and lint verification:
- `./.venv/bin/pytest tests/test_threat_intel_r1.py -v`
- `./.venv/bin/ruff check app tests`
- `./.venv/bin/pytest tests/ -q`

Write your complete handoff report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`.
Report completion back to parent via send_message.

