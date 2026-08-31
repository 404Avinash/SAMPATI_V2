# Handoff Report: Backend Deployment Fix & Demo Seed Data (Sprint 3 Milestone 1: R1 & R2)

**Author**: Worker 1 (`teamwork_preview_worker_m1`)  
**Target**: Orchestrator / Parent Agent  
**Date**: 2026-08-31T15:48:00Z  

---

## 1. Observation

1. **Static Mount & SPA Fallback (`app/main.py`)**:
   - `app.mount("/static", ...)` was previously absent in `app/main.py`. Requests to `/static/upi_cases/...` were swallowed by the root SPA mount `app.mount("/", StaticFiles(directory=_dist, html=True))` or returned 404 falling back to `index.html`.
   - `spa_fallback_404_handler` `api_prefixes` did not include `"/static"`.

2. **Dependencies (`requirements.txt`)**:
   - `requirements.txt` lacked `reportlab>=4.0.0`, required for containerized environments and SAR PDF generation.

3. **In-Memory State & Demo Seed Data (`app/services/upi_cases.py`, `app/api/upi.py`, `app/main.py`)**:
   - On server startup or after restarts without persisted DB state, initial transaction count was 0, leaving the frontend dashboard with empty charts and unpopulated constellation graphs.
   - Unit tests like `test_analytics_empty_state_resilience` in `tests/test_analytics.py` instantiate `UpiCaseService()` directly and assert `total_evaluated == 0`.

---

## 2. Logic Chain

1. **Static Mount Resolution**:
   - In `app/main.py`, defined `_static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))` and ensured `os.makedirs(os.path.join(_static_dir, "upi_cases"), exist_ok=True)`.
   - Mounted `app.mount("/static", StaticFiles(directory=_static_dir), name="static")` **before** the SPA mount `app.mount("/", ...)`.
   - Added `"/static"` to `api_prefixes` in `spa_fallback_404_handler` so missing static files return standard 404 JSON rather than HTML SPA fallback.

2. **Dependency Resolution**:
   - Added `reportlab>=4.0.0` to `requirements.txt`.

3. **Non-Blocking Background Demo Seed Architecture**:
   - Created `trigger_demo_seed(service, total_txns=150, fraud_ratio=0.25, seed=42)` in `app/services/upi_cases.py`.
   - Used thread-safe double-checked locking (`_demo_seed_lock` and `_demo_seeded` flag).
   - In the background daemon thread (`_seed_worker`), generated stream using `generate_labeled_stream(total_txns=150, fraud_ratio=0.25, seed=42)`, routed each transaction to federation nodes via `svc.federation.route(labeled.txn)` and evaluated via `svc.evaluate(labeled.txn)`, followed by `svc.run_federation(now=stream[-1].txn.timestamp)`.
   - Hooked `trigger_demo_seed()` into:
     - `app/main.py` application `lifespan` startup hook.
     - `app/api/upi.py` `upi_stats()` endpoint handler on first request when `eval_count == 0`.
   - Kept `UpiCaseService.__init__` pure so direct instantiation in isolated unit tests starts with 0 evaluations.

---

## 3. Caveats

- **Thread Completion Time**: The demo seeder runs as an asynchronous daemon thread. On a fresh startup or first `/upi/stats` call, the initial response returns immediately while the background worker takes ~1-2 seconds to evaluate 150 transactions and render the ring PNGs.
- **Direct Instantiation**: Direct `UpiCaseService()` instances in test suites will not auto-seed unless `trigger_demo_seed(service)` or HTTP endpoints are called.

---

## 4. Conclusion

- Requirement R1 (Deployment Fix — Forensic Image Persistence & Static Mount) and Requirement R2 (Demo Seed Data on Load) are fully implemented and verified.
- All 710 existing tests in `./.venv/bin/pytest tests/ -v` pass with 0 failures.
- `ruff check app tests` passes cleanly with 0 violations.
- Direct static file probes verify that `/static/upi_cases/{case_id}_ring.png` serves 200 OK, missing static files return 404 JSON, and auto-seeding populates cases and rings.

---

## 5. Verification Method

1. **Verify Static Mount & Auto-Seed Functionality**:
   ```bash
   ./.venv/bin/python -c "
   import os, time
   from fastapi.testclient import TestClient
   from app.main import app
   from app.services.upi_cases import UpiCaseService, trigger_demo_seed

   # 1. Test pure instantiation
   fresh_service = UpiCaseService(artifact_dir='static/test_probe_fresh')
   assert fresh_service.get_current_stats()['evaluated'] == 0
   assert len(fresh_service.list_cases()) == 0

   # 2. Test static files mount
   os.makedirs('static/upi_cases', exist_ok=True)
   probe_file = 'static/upi_cases/probe_test_case_ring.png'
   with open(probe_file, 'wb') as f:
       f.write(b'\x89PNG\r\n\x1a\nprobe_data')

   client = TestClient(app)
   res_static = client.get('/static/upi_cases/probe_test_case_ring.png')
   assert res_static.status_code == 200
   assert res_static.content == b'\x89PNG\r\n\x1a\nprobe_data'

   # 3. Test static 404 JSON fallback
   res_404 = client.get('/static/upi_cases/non_existent_file.png')
   assert res_404.status_code == 404
   assert res_404.headers['content-type'].startswith('application/json')
   if os.path.exists(probe_file):
       os.remove(probe_file)

   # 4. Test trigger_demo_seed
   test_svc = UpiCaseService(artifact_dir='static/test_probe_seeded')
   assert trigger_demo_seed(test_svc, total_txns=150, fraud_ratio=0.25, seed=42) is True
   time.sleep(2.5)
   stats = test_svc.get_current_stats()
   assert stats['evaluated'] == 150
   assert len(test_svc.list_cases()) > 0
   assert len(test_svc.federation.current_rings()) > 0
   print('Static mount and auto-seed probe passed!')
   "
   ```

2. **Verify Python Linting**:
   ```bash
   ./.venv/bin/ruff check app tests
   ```

3. **Verify Full Pytest Suite**:
   ```bash
   ./.venv/bin/pytest tests/ -v
   ```
   Expected: 710 passed, 0 failures.
