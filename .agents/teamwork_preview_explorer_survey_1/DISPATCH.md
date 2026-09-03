# Dispatch for teamwork_preview_explorer_survey_1

- Role: Backend & Threat Intel Explorer
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1
- Parent orchestrator: teamwork_preview_orchestrator_10
- Objective: Survey R1 (Early Warning Intelligence Layer backend infrastructure, FastAPI routes, PostgreSQL models, fraud signal ingestion, fraud graph linkage) and relevant existing backend architecture.

## 2026-09-03T09:35:00Z
Investigate the backend architecture, PRD documents, database models, and existing API routes for Requirement 1: "Early Warning Intelligence Layer (Backend)".
Specifically:
1. Search for any PRD, architecture docs, or specs in the repository (e.g., PRD.md, README.md, ENCYCLOPEDIA.md, docs/, etc.) regarding the "Intelligence Mesh" pivot, pre-transaction threat signals, social engineering tags, and entity extraction.
2. Investigate existing FastAPI routers (app/api/), database connections/models (app/models/, SQLAlchemy/SQL/PostgreSQL or in-memory repositories), and the central Fraud Graph (app/services/graph_service.py, app/engine/, etc.).
3. Determine how standard fraud signal JSON payloads (Phone, UPI ID, URL, tags like "Bank impersonation", "Urgency") should be structured, validated (Pydantic models), stored, and ingested via new FastAPI endpoints (e.g. /intel/signals, /threat-intel/, etc.).
4. Determine how these incoming threat signals will automatically link to the central Fraud Graph and how they can be retrieved or streamed to the frontend.
5. Check existing tests in tests/ to see what test patterns are used, and what new endpoints or fixtures will be needed.

Write your findings and recommendations into /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md.
Use send_message to notify parent when complete with the path to your handoff file.
