# DISPATCH: teamwork_preview_explorer_m1_3

## Identity
- Role: Explorer 3 for Milestone 1 (FastAPI Endpoints, Router Mounting, SPA Fallback & Test Suite)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_3
- Parent: teamwork_preview_orchestrator_11

## Mission & Inputs
- Read authoritative request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (lines 336–379, R1 Early Warning Intelligence Layer).
- Read project scope & architecture: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`.
- Read previous survey findings: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md`.
- Inspect existing routes and main: `app/main.py`, `app/api/upi.py`, `tests/test_isolation_forest.py`.

## Assignment
1. Investigate and specify FastAPI endpoints in `app/api/intel.py`:
   - `POST /intel/signals` (accepts `ThreatSignalCreateRequest`, returns 201 `ThreatSignalResponse`).
   - `GET /intel/signals` (query params: `limit=50`, `offset=0`, `severity`, `source`, `campaign_id`).
   - `GET /intel/signals/{signal_id}` (returns full signal with graph and campaign metadata, 404 if not found).
   - `GET /intel/graph` (returns `{nodes: [...], edges: [...]}` from FraudGraphService).
   - `GET /intel/campaigns` (returns list of active campaigns with threat signal counts and average similarity).
   - `POST /intel/simulate` (triggers synthetic threat signals generation).
   - Provide route aliases at `/threat-intel/` to guarantee compatibility with frontend calls.
2. Investigate router mounting in `app/main.py`:
   - Import `intel_router` from `app.api.intel`.
   - `app.include_router(intel.router, prefix="/intel", tags=["threat-intel"])`.
   - `app.include_router(intel.router, prefix="/threat-intel", tags=["threat-intel"])`.
   - Update `api_prefixes` tuple in `app/main.py` (around line 423) to include `"/intel"` and `"/threat-intel"` so that SPA static file fallback does not intercept API 404s or endpoints.
3. Design test suite in `tests/test_threat_intel_r1.py`:
   - Test signal creation with explicit fields.
   - Test signal creation with raw unstructured SMS/WhatsApp text and regex entity extraction.
   - Test invalid signal rejection (422).
   - Test campaign similarity calculation (matching KYC phishing keywords -> ~94%).
   - Test FraudGraphService node/edge addition and graph export.
   - Test graph linking between threat signal and existing case/VPA.
   - Test GET /intel/signals, GET /intel/signals/{id}, GET /intel/graph, GET /intel/campaigns, POST /intel/simulate.
   - Test SPA fallback route exclusion.
4. Write your complete findings and implementation plan to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_3/handoff.md`.
5. Report completion back to parent via `send_message`.
