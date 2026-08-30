## 2026-08-30T19:28:23Z
You are Worker M1 for SAMPATI V2.
Your working directory is `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1`.
You must read the user's authoritative request at `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md` and the architecture spec at `/home/avi/Downloads/Sampati_v2/PROJECT.md`.
Also review the findings in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/analysis.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Task — Milestone 1: Federation Signal Exchange API & Dynamic Network Scoring:
1. Implement `app/api/federation.py` with:
   - `POST /federation/signal`: Accepts `{vpa_hash, risk_level, ring_hash}` (e.g. `FederationSignalRequest`), records the signal in `FederatedCoordinator`, returns HTTP 200 with `{"status": "accepted", "vpa_hash": ..., "risk_level": ..., "timestamp": ...}`.
   - `GET /federation/query`: Accepts query parameter `vpa_hash`, retrieves score/signal from `FederatedCoordinator` hot cache in sub-5ms, returns `{"vpa_hash": ..., "federated_risk_score": float, "risk_level": ..., "ring_members": List[str], "reported_by_nodes": List[str], "cached": bool}`.
2. Update `app/federation/coordinator.py`:
   - Add `record_signal(vpa_hash: str, risk_level: str, ring_hash: Optional[str])` method mapping risk levels to scores (e.g., CRITICAL: 1.0, HIGH: 0.85, MEDIUM: 0.5, LOW: 0.2) and updating `_signals` and `_scores`. Support hot Redis caching if redis client is available, with fast in-memory fallback.
   - Add `query_signal(vpa_hash: str)` retrieving cached signals/scores.
   - Ensure `network_score(vpa: str)` and `network_score_for_txn(txn: Dict[str, Any])` check raw VPA, SHA-256 hash, and pseudonym against signals and scores, returning the federated score.
3. Update `app/main.py`:
   - Mount the federation router under `/federation` with tags `["federation"]`.
4. Verify `/upi/check` and `UpiEvaluationResponse`:
   - Ensure when a transaction's payee or payer VPA has a matching federation signal, `/upi/check` returns `network_score > 0` and incorporates it into risk scoring.
5. Verification:
   - Run the test suite: `.venv/bin/pytest tests/ -v` and ensure 0 regressions.
   - Run a test verification of `POST /federation/signal`, `GET /federation/query`, and `/upi/check` with a federated VPA.
6. Write your detailed changes and test results to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`. Notify parent when done.
