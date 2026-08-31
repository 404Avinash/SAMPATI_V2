## 2026-08-31T03:25:56Z
You are a Worker agent implementing Milestone 1 (M1: Core Risk Engine Extensions) for SAMPATI V2 Sprint 2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/
Original user request is authoritative and located at: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
Project architecture and plan is at: /home/avi/Downloads/Sampati_v2/PROJECT.md
Survey architecture handoff is at: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_engine/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Tasks for Milestone 1:
1. `app/models/upi_models.py`:
   - Add `dmv_score: float = Field(default=0.0, description="Dead Money Velocity score (0-100)")` to `UpiEvaluationResponse`.
   - Add `campaign_id: Optional[str] = Field(default=None, description="Active fraud campaign identifier if matched")` to `UpiEvaluationResponse`.
2. `app/engine/dmv.py`:
   - Implement `DmvTracker` and `calculate_dmv_score(...)` (0–100 scale) quantifying account dormancy followed by rapid, near-complete balance dissipation.
3. `app/engine/upi_rules.py`:
   - Implement 3 new scoring rules:
     - `rule_sim_device_mismatch` (`R_SIM_DEVICE_MISMATCH`, 30 pts, HIGH severity): flags when device changes for same SIM or SIM changes for same device for a payer.
     - `rule_impossible_travel` (`R_IMPOSSIBLE_TRAVEL`, 35 pts, CRITICAL severity): Haversine distance and velocity calculation (>500km in <30min / >1000km/h) across coordinates ("lat,lon") and Indian/global city names.
     - `rule_datacenter_ip` (`R_DATACENTER_IP`, 25 pts, HIGH severity): checks IP against AWS, GCP, Azure, DigitalOcean, Tor/VPN CIDR subnets using `ipaddress`.
   - Add rule codes and metadata to `RULE_METADATA` in `app/services/upi_cases.py`.
4. `app/engine/campaign.py`:
   - Implement `CampaignSignatureStore` and `rule_campaign_match` (`R_CAMPAIGN_MATCH`, 30 pts, CRITICAL severity).
   - Ingest transaction behavioral vector on BLOCK or CONFIRMED_FRAUD verdicts.
   - Compare incoming transaction similarity (threshold >= 0.82) and attach matched `campaign_id`.
5. `app/engine/upi_scorer.py` and `app/services/upi_cases.py`:
   - Wire DMV score calculation, new rules, and campaign matching into `UpiRiskScorer.evaluate()` and `UpiCaseService.evaluate()`.
   - Ensure `dmv_score` and `campaign_id` are populated on `UpiEvaluationResponse`.
6. Verification & Quality Gates:
   - Run `./.venv/bin/pytest tests/ -v` (must pass 559+ tests with 0 regressions).
   - Run `./.venv/bin/ruff check app tests` (must pass with 0 errors).
   - Add unit tests for M1 in `tests/test_engine_sprint2.py`.

Write your completion report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`.
Send a message when completed with test and build verification commands and results.
