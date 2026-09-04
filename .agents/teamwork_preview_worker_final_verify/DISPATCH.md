# Dispatch: teamwork_preview_worker_final_verify

## Mission
Final Milestone: Execute comprehensive end-to-end regression validation, linter verification, and frontend production build for SAMPATI V2.

## Working Directory
`/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_final_verify/`

## Mandatory Reading
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read request under 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md`

## Verification Scope & Instructions
1. Run and verify the training script output:
   `./.venv/bin/python app/engine/train_supervised.py`
   - Verify Precision, Recall, F1 score, and False Negative reduction summary are printed.
2. Run the full pytest suite:
   `./.venv/bin/pytest tests/ -v`
   - Verify that all 969+ tests pass with 0 failures and 0 regressions.
3. Run the latency benchmark suite:
   `./.venv/bin/pytest tests/test_notifications_benchmark.py -v -s`
   - Verify that p99 latency from signal ingestion to FCM dispatch is under 500ms.
4. Run python linter:
   `./.venv/bin/ruff check app tests`
   - Verify 0 errors.
5. Run frontend lint and build:
   `cd frontend && npm run lint && npm run build && cd ..`
   - Verify 0 ESLint warnings (`--max-warnings 0`) and clean Vite production build.
6. Verify Acceptance Criteria:
   - `/upi/check` response includes both `ml_anomaly_score` and `supervised_fraud_score`.
   - Transaction to known-bad VPA returns non-zero `mock_npci_score` and `mock_dpip_threat_level`.
   - `POST /notifications/register` registers tokens and updates deduplicated tokens.
   - High-risk payload to `POST /intel/signals` triggers FCM push within 500ms.

Document full command outputs and verification evidence in `handoff.md` and communicate via `send_message`.

## 2026-09-03T22:11:00Z
<USER_REQUEST>
You are teamwork_preview_worker_final_verify.
Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_final_verify/
Workspace root: /home/avi/Downloads/Sampati_v2
Read /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md, /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md, and your dispatch file at /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_final_verify/DISPATCH.md.

Execute final end-to-end regression validation, linter check, and frontend build:
1. Run `./.venv/bin/python app/engine/train_supervised.py` and capture printed summary.
2. Run `./.venv/bin/pytest tests/ -v` and verify 0 failures.
3. Run `./.venv/bin/pytest tests/test_notifications_benchmark.py -v -s` and verify latency < 500ms.
4. Run `./.venv/bin/ruff check app tests` and verify 0 errors.
5. Run `cd frontend && npm run lint && npm run build && cd ..` and verify clean build.
6. Verify all acceptance criteria explicitly.
Document full verification results in handoff.md and send_message when done.
</USER_REQUEST>
