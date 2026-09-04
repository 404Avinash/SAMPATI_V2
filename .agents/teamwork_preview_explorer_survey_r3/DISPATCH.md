# Dispatch: teamwork_preview_explorer_survey_r3

## Mission
Investigate R3: Mobile App Push Notification System (FCM Integration) & End-to-End Latency Benchmarking for SAMPATI V2.

## Working Directory
/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r3/

## Mandatory Reading
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read the latest request from 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/DISPATCH.md`

## Objectives
1. Investigate how Firebase Cloud Messaging (FCM) can be cleanly integrated into the FastAPI backend (e.g. `firebase-admin` or lightweight HTTP v1 FCM API client with mockable fallback for environments without external cloud credentials).
2. Design the device token registration endpoint: `POST /notifications/register` (payload schema, in-memory or database storage, duplicate token handling).
3. Investigate the trigger points for push notifications:
   - High-risk threats where transaction verdict is BLOCK
   - High-risk pre-transaction signal arriving via `POST /intel/signals`
   - Notification payload structure: risk score, verdict, top reason.
4. Design the latency benchmark test:
   - Must demonstrate end-to-end latency from signal ingestion (`POST /intel/signals` or `/upi/check`) to notification dispatch is under 500ms on local machine.
5. Check existing test suite (902 tests) and CI/CD/linting constraints (ruff, pytest, frontend ESLint/build).
6. Write your findings to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r3/handoff.md`.

## 2026-09-03T20:15:37Z
Investigate R3: Mobile App Push Notification System (FCM Integration) & End-to-End Latency Benchmarking.
Explore the existing codebase:
- Examine how push notifications should integrate with FastAPI (e.g. firebase-admin or custom FCM v1 client with mock fallback for testing without live Firebase keys).
- Design POST /notifications/register endpoint (schema, token store).
- Identify trigger points: BLOCK verdict in /upi/check or /cases evaluation, and high-risk pre-transaction signal arriving via POST /intel/signals.
- Define notification payload: risk score, verdict, top reason.
- Design benchmark test demonstrating end-to-end latency from signal ingestion to notification dispatch is under 500ms on local machine.
- Check pytest test structure (tests/ folder, test runners, fixtures) and ensure compatibility with existing 902+ tests.
- Document all findings, file paths, concrete implementation steps, and verification strategies in handoff.md in your working directory.
Communicate completion back with send_message.
