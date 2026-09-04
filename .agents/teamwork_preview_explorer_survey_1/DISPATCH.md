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

## 2026-09-04T10:21:18Z
Role: survey_explorer_1
Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1
Parent conversation ID: 633a9079-d863-4bd1-9c75-d637844689ae

MANDATORY INPUT:
Read the authoritative user request at:
/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md
Specifically section ## 2026-09-04T10:20:00Z.

MISSION:
Conduct a comprehensive Survey on Requirement R1 (Kill All Overclaims and AI-Sounding Copy):
1. Audit all visible text across the entire frontend (in /home/avi/Downloads/Sampati_v2/frontend/src):
   - Page titles, subtitles, headers, navigation labels
   - KPI labels, metric cards, stat descriptions
   - Card copy, badge labels
   - Empty state messages (e.g., "No data", "Loading...", "No cases found")
   - Offending terms specified in acceptance criteria:
     - "Zero False-Pos" (target: replace with realistic metric like "< 2% analyst escalation rate")
     - "98% Defensible" (target: replace with grounded, specific analyst metric)
     - "Pillar 1", "Pillar 2" (e.g. "Pillar 1: Multi-Modal Ingestion Pipeline", "Pillar 2: Threat Syndicate Analytics" -> plain, direct headers)
     - "100% confidence"
     - "real-time AI", "advanced ML", "AI slop"
     - "No data available", "TODO", "placeholder"
2. Search and catalogue every single instance in the frontend codebase (exact file path, line numbers, current text, recommended realistic replacement text suited for bank fraud analysts and hackathon judges).
3. Check for any backend strings returned in API responses that might bleed into the frontend with overclaims.

CONSTRAINTS:
- You are a READ-ONLY explorer. Do NOT modify any source code files.
- Deliver your detailed findings in:
  /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/survey_r1_report.md
  and write your handoff in:
  /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md
- When finished, send a message to your parent using send_message with a summary of findings and the path to your report.
