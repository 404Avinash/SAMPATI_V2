## 2026-08-31T05:52:47Z
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/worker_backend_sprint2

Read the following reference files:
1. /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
2. /home/avi/Downloads/Sampati_v2/PROJECT.md
3. /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_backend/handoff.md
4. /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_engine/handoff.md

You are the Backend Sprint 2 Implementer. You exclusively own backend files:
- `app/models/upi_models.py`
- `app/engine/upi_rules.py`
- `app/forensics/sar_pdf.py` (or SAR PDF generation modules)
- `app/services/autofeed.py`
- `app/services/upi_cases.py`
- `app/api/upi.py`
- `app/main.py`

Tasks to implement:
1. Area 1 — SAR PDF Export:
   Implement `GET /cases/{case_id}/sar/pdf` (in `app/main.py`) AND `GET /upi/cases/{case_id}/sar/pdf` (in `app/api/upi.py`) returning HTTP 200 with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="SAR_{case_id}.pdf"`.
   Use reportlab or pure-python/matplotlib PDF generation (ensuring valid %PDF-1.4 binary stream, narrative text, ring members table, case summary). Return HTTP 404 with {"detail": f"UPI case '{case_id}' not found"} for unknown case IDs.
2. Area 2 — Workload Heatmap:
   Add `workload_heatmap` to `/upi/stats/analytics` and `/stats/analytics` (in `AnalyticsResponse` and `UpiCaseService.get_analytics()`). Must be a 7x24 grid (day_of_week 0..6 x hour 0..23) counting flagged case volume from the last 30 days from in-memory case data (`_cases`).
   Also ensure `top_dmv_vpas` or top VPAs by DMV are returned as expected.
3. Area 3 — Live Auto-Feed Engine:
   Implement endpoints in `app/api/upi.py` (and generator in `app/services/autofeed.py`):
   - `POST /upi/autofeed/start` (accepts rate_tps: float, fraud_ratio: float, bursty: bool; returns {"status": "started"|"already_running", "active": True, "rate_tps": float})
   - `GET /upi/autofeed/status` (returns {"active": bool, "rate_tps": float, "txns_generated": int, ...})
   - `POST /upi/autofeed/stop` (stops loop, returns {"status": "stopped"|"not_running", "active": False})
   The background async loop must call the live `UpiCaseService.evaluate()` pipeline and broadcast events via WebSocket `broadcast_event()`. Must be idempotent and cleanly stoppable. Max allowed TPS is 50.
4. Area 4 — Scoring Fix:
   In `app/engine/upi_rules.py`, fix `NEW_ACCOUNT_HIGH_VALUE` (or add escalating risk points for very large amounts on new accounts) so that a transaction with `amount=10_000_000` and `payer_account_age_days=1` triggers HOLD or BLOCK (risk score >= 45/70).

Verification requirements:
- Run `./.venv/bin/pytest tests/test_sprint2_e2e_suite.py -v` -> make all 110 tests pass!
- Run `./.venv/bin/pytest tests/ --ignore=tests/test_sprint2_e2e_suite.py -q` -> must be 559 passed, 0 failures!
- Run `./.venv/bin/ruff check app tests` -> 0 lint errors!
