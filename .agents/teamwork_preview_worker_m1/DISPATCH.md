## 2026-08-31T15:39:26Z
You are Worker 1 for SAMPATI V2 Sprint 3 Milestone 1 (Backend Deployment Fix & Demo Seed Data: R1 & R2).

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1
Workspace root: /home/avi/Downloads/Sampati_v2

You EXCLUSIVELY own and are permitted to modify these files:
- `app/main.py`
- `app/services/upi_cases.py`
- `app/api/upi.py`
- `requirements.txt`

Context & Input:
- Read /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (Sprint 3 section)
- Read /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md for exact line numbers and proposed code changes.

Requirements to implement:
1. R1: Fix Deployment — Forensic Image Persistence & Static Mount:
   - In `app/main.py`:
     - Add `_static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))` and ensure `os.makedirs(os.path.join(_static_dir, "upi_cases"), exist_ok=True)`.
     - Mount `/static` with `app.mount("/static", StaticFiles(directory=_static_dir), name="static")` BEFORE the catch-all root SPA mount `app.mount("/", ...)`.
     - In `spa_fallback_404_handler`, ensure `"/static"` is added to `api_prefixes` so missing static files return 404 JSON instead of falling back to SPA HTML.
   - In `app/services/upi_cases.py`:
     - In `UpiCaseService.__init__`, ensure `os.makedirs(self.artifact_dir, exist_ok=True)` is called and handles directory creation robustly.
   - In `requirements.txt`:
     - Add `reportlab>=4.0.0` to `requirements.txt`.
2. R2: Demo Seed Data on Load:
   - Implement non-blocking background demo seed simulation (~150 transactions, fraud_ratio=0.25) using `generate_labeled_stream(total_txns=150, fraud_ratio=0.25, seed=42)`.
   - Trigger it safely in background (non-blocking daemon thread or background task) on startup in `app/main.py` lifespan and on the first request to `/upi/stats` in `app/api/upi.py` if `evaluated == 0` and not already seeded.
   - Ensure direct instantiation of `UpiCaseService()` in unit tests remains pure (do not auto-seed in `__init__`).

Verification commands:
- Run `./.venv/bin/pytest tests/ -v` (must pass 710+ tests).
- Test `/static/upi_cases/` mount with a test probe.
- Test that `/upi/stats` triggers the non-blocking background seed cleanly.

Write your completion report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`.
Use `send_message` to notify parent when complete.
