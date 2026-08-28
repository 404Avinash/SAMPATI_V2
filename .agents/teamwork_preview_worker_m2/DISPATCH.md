## 2026-08-28T19:18:47Z
You are Worker 2 for Milestone M2 (Backend Real-Time WebSocket Push Hub).

Your working directory is:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_worker_m2\

Project workspace:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2

Original User Request:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\ORIGINAL_REQUEST.md

Project Specification:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\PROJECT.md

Survey Blueprint from Explorer 2:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_2\survey_websocket_realtime.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive Write Files:
- `app/api/websocket.py`
- `app/api/upi.py`
- `app/services/upi_cases.py`

Your Task:
Implement Milestone M2 (Backend Real-Time WebSocket Push Hub):
1. Implement thread-safe `ConnectionManager` in `app/api/websocket.py` with `active_connections`, `connect()`, `disconnect()`, and `broadcast()` with dead connection pruning and exception safety.
2. Expose WebSocket routes on `@router.websocket("/ws")`, `@router.websocket("/ws/")`, and `@router.websocket("/ws/feed")` supporting ping/pong heartbeats.
3. Wire broadcasting into `UpiCaseService.create_case` and `UpiCaseService.save_case` to emit `new_case` payload format specified in PROJECT.md.
4. Wire broadcasting into `app/api/upi.py` (`simulate` endpoint and federation endpoint) to emit `new_case` and `stats_update` events in real time with < 2s latency.
5. Verify with automated tests (`python tests/test_e2e_suite.py --feature F5 --feature F6` and WebSocket integration tests).
6. Write `handoff.md` in your working directory and notify parent.
