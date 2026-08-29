## 2026-08-29T08:03:04Z
You are the Backend Implementation Worker for Milestone M2 of SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/worker_m2_backend/
Please read the user request at: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md.
Also read the project architecture at: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_2/PROJECT.md and the backend technical design report at: /home/avi/Downloads/Sampati_v2/.agents/survey_backend/handoff.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
1. You own write access to: `app/main.py`, `app/api/upi.py`, `app/services/upi_cases.py`, `app/models/upi_persistence.py`, `app/models/upi_models.py`.
2. Implement Milestone M2 (R3 requirements):
   - `GET /stats/analytics` & `GET /upi/stats/analytics`: returns time-bucketed verdict counts (hourly/daily), rule trigger frequencies, top flagged accounts, and bank distributions.
   - `GET /health/detailed` & `GET /upi/health/detailed`: returns detection latency percentiles (p50/p90/p99), DB pool status, Redis ping latency, WebSocket active connection count, throughput (batches/min & txns/sec), and process uptime.
   - `PATCH /cases/{case_id}/status` & `PATCH /upi/cases/{case_id}/status`: allows updating case review status (`reviewed`, `escalated`, `dismissed`, `open`), persists updates to DB, triggers DPIP feed publishing & adaptive model feedback on escalation, and broadcasts WebSocket updates.
   - Latency tracking & 60s throughput calculation in `UpiCaseService`.
   - Add SPA fallback handler in `app/main.py` to serve `frontend/dist/index.html` on direct client route navigation.
3. Test your changes locally to ensure the backend starts, imports cleanly, and all endpoints return the exact schema expected.
4. Write your handoff report to `/home/avi/Downloads/Sampati_v2/.agents/worker_m2_backend/handoff.md` and send a message when done.
