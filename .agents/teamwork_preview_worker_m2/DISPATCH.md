## 2026-08-30T19:35:14Z
You are Worker M2 (Backend Honeypot Network) for SAMPATI V2.
Your working directory is `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2`.
Read `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md`, `/home/avi/Downloads/Sampati_v2/PROJECT.md`, and `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/analysis.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership: You own backend engine/service files:
`app/engine/honeypot.py`, `app/engine/upi_rules.py`, `app/engine/upi_scorer.py`, `app/services/upi_cases.py`, `app/api/upi.py`, `app/api/federation.py`, `tests/test_honeypot.py`.
Do NOT edit frontend files.

Your Task — Milestone 2: VPA Honeypot Network & Hit Tracking:
1. Implement `app/engine/honeypot.py`:
   - Define seeded synthetic honeypot VPAs (e.g. `honeypot_trap_01@okaxis`, `honeypot_mule_99@okhdfcbank`, `phish_trap_node@okicici`, `botnet_sink_04@oksbi`, `mule_honeypot_prime@okaxis`).
   - Implement `HoneypotRegistry` class with thread-safe `record_hit(vpa, txn_id, amount)`, `is_honeypot(vpa) -> bool`, `get_stats() -> Dict[str, Any]`, `get_hits_24h() -> int`, `list_honeypots() -> List[Dict[str, Any]]`.
   - Track hit counts, total amount deflected, and last-hit ISO timestamps per honeypot VPA.
2. Update `app/engine/upi_rules.py` & `app/engine/upi_scorer.py`:
   - Implement detection rule `rule_honeypot_hit` (awarding 100 points, `Severity.CRITICAL`, `reason="Transaction directed to active synthetic honeypot VPA"`, `rule_id="R_HONEYPOT_HIT"`).
   - Ensure that when a transaction's payee VPA is in the honeypot registry:
     - `R_HONEYPOT_HIT` is triggered.
     - `risk_score` is 100 (which exceeds `BLOCK_AT = 70`).
     - Verdict is `BLOCK`.
     - `resp.reasons` contains `"R_HONEYPOT_HIT"`.
3. Update `app/services/upi_cases.py` and `app/api/upi.py`:
   - Integrate `HoneypotRegistry` into `UpiCaseService.evaluate(txn)`.
   - Update `get_current_stats()` to include `honeypot_hits_24h` and `honeypot_hits` in the stats dictionary.
   - Expose in `GET /upi/stats`, WebSocket broadcasts, and add `GET /federation/honeypots` in `app/api/federation.py`.
4. Create test suite in `tests/test_honeypot.py` covering:
   - Seeded VPAs detection, `R_HONEYPOT_HIT` rule, `BLOCK` verdict, reasons list.
   - Hit count incrementing and 24h rolling count aggregation.
   - `/upi/check`, `/upi/stats`, `/federation/honeypots` endpoints.
5. Verification:
   - Run pytest: `.venv/bin/pytest tests/test_honeypot.py -v`.
   - Run full test suite: `.venv/bin/pytest tests/ -v` to ensure 0 regressions.
6. Write your changes and test results to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2/handoff.md`. Notify parent when done.
