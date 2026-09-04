# Dispatch: teamwork_preview_worker_m3_r3

## Mission
Implement Milestone 3 (R3): Mobile App Push Notification System (FCM Integration) & End-to-End Latency Benchmarking for SAMPATI V2.

## Working Directory
`/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m3_r3/`

## Mandatory Reading Before Starting Work
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read request under 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r3/handoff.md`

## Exclusive Write Ownership
- `app/services/notification_service.py` (new)
- `app/api/notifications.py` (new)
- `app/main.py` (mount notifications router)
- `app/services/threat_intel_service.py` (trigger on HIGH/CRITICAL signals)
- `app/api/upi.py` (trigger on BLOCK verdict in `/upi/check`)
- `tests/test_notifications_benchmark.py` (new benchmark and notification test suite)

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Requirements & Implementation Blueprint
Follow the blueprint in `.agents/teamwork_preview_explorer_survey_r3/handoff.md`:
1. `app/services/notification_service.py`:
   - Implement `DeviceRegistrationRequest` (token, platform, device_id, user_id, vpa, app_version) and `DeviceRegistrationResponse`.
   - Implement `NotificationPayload` (risk_score, verdict, top_reason, target_vpa, title, body, data, dispatched_at).
   - Implement `DispatchResult` (success, dispatched_count, payload, latency_ms, mode).
   - Implement `FcmProvider` protocol with:
     - `MockFcmProvider` for hermetic testing and offline operation (records token dispatches in thread-safe list, microsecond execution).
     - `HttpV1FcmProvider` for live Google Cloud FCM HTTP v1 API using httpx.
   - Implement `NotificationService` with `register_device()`, `get_registered_tokens(vpa=...)`, `dispatch_threat_alert()`, `clear()`, and singleton `get_notification_service()`.
   - Ensure duplicate token registration updates metadata and returns status `"updated"`, without duplicating records.
2. `app/api/notifications.py` & `app/main.py`:
   - Router endpoints:
     - `POST /notifications/register`: Registers or updates device token.
     - `GET /notifications/tokens`: Returns registered device records.
     - `GET /notifications/history`: Returns recent dispatch history.
   - In `app/main.py`: Mount router at `/notifications` and `/upi/notifications`. Include `/notifications` in SPA fallback whitelist.
3. `app/services/threat_intel_service.py`:
   - In `ingest_signal()`, if `severity.upper() in ("HIGH", "CRITICAL")`:
     - Dispatch threat alert with `risk_score` (95 for CRITICAL, 85 for HIGH), `verdict="BLOCK"`, `top_reason=f"Pre-transaction threat: {top_tag}"`, `target_vpa=upi_id`.
4. `app/api/upi.py`:
   - In `check_upi_txn()`, if `resp.action == "BLOCK"`:
     - Dispatch threat alert with `risk_score=resp.risk_score`, `verdict="BLOCK"`, `top_reason=resp.reasons[0]`, `target_vpa=txn.payer_vpa`.
5. `tests/test_notifications_benchmark.py`:
   - Test device registration and deduplication (`registered` vs `updated`).
   - Test `POST /intel/signals` with HIGH/CRITICAL severity triggers FCM dispatch with risk score, verdict, and top reason.
   - Test `POST /intel/signals` with LOW severity does NOT trigger FCM dispatch.
   - Test `POST /upi/check` with BLOCK verdict triggers FCM dispatch.
   - **Benchmark Test**: Run 50+ iterations of end-to-end ingestion to FCM dispatch via `POST /intel/signals`. Compute average, median (p50), p95, p99, and max latency in ms. Assert that p99 and max latency are strictly under 500ms on the local machine (typically < 25ms).
6. Run all verifications:
   - `./.venv/bin/pytest tests/test_notifications_benchmark.py -v -s`
   - `./.venv/bin/pytest tests/ -q` (all tests pass)
   - `./.venv/bin/ruff check app tests` (0 errors)
   - `cd frontend && npm run lint && npm run build && cd ..` (clean build)

Write your completion report to `handoff.md` and notify the orchestrator with `send_message`.
