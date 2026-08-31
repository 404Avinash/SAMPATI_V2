## 2026-08-31T15:34:18Z

You are Explorer 1 for SAMPATI V2 Sprint 3.
Your task: Survey the backend codebase for Requirements R1 (Static Mount, Forensic Image Persistence, requirements.txt) and R2 (Demo Seed Data on Load).

Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1
Workspace root: /home/avi/Downloads/Sampati_v2
Read:
- /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (Sprint 3 section)
- /home/avi/Downloads/Sampati_v2/app/main.py
- /home/avi/Downloads/Sampati_v2/app/services/upi_cases.py
- /home/avi/Downloads/Sampati_v2/app/api/upi_routes.py (and any other relevant routes)
- /home/avi/Downloads/Sampati_v2/requirements.txt
- Existing backend tests in tests/

Investigate:
1. Exact static mount in `app/main.py` and where it needs to be placed relative to SPA fallback mount.
2. In `app/services/upi_cases.py` (`UpiCaseService.__init__`), how `artifact_dir` is initialized, where ring PNG images are saved (`static/upi_cases/`), and ensuring `os.makedirs` handles directory creation.
3. In `requirements.txt`, verify reportlab and all packages used by the backend are listed.
4. For R2 Demo Seed Data: investigate how `UpiCaseService` handles transactions/cases, how a background non-blocking simulation (~150 txns, fraud_ratio=0.25) can be triggered on startup or on the first request to `/upi/stats` if `evaluated_txns == 0` without blocking response. Check how stats/simulation work.

Write your findings to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md`.
Use `send_message` to report back to parent when complete with path to handoff.md.
