## 2026-08-30T21:52:36Z

Scope of investigation: Core Risk Engine, DMV Score, Device Telemetry Rules, and Campaign Fingerprinting.

Please investigate:
1. Examine app/engine/upi_scorer.py, app/engine/upi_rules.py, app/models/upi_models.py, app/services/upi_cases.py, app/engine/honeypot.py, and app/engine/adaptive*.
2. How transactions are evaluated, scored (0-100), and structured in UpiEvaluationResponse and rule_breakdown.
3. How UpiTransaction device/location fields (device_id, sim_id, ip, location, payer_account_age_days) are defined and can be used.
4. Detailed design for:
   - DMV (Dead Money Velocity) Score (0-100) per-VPA in /upi/check: formula, dormant period detection, rapid transfer burst velocity, history tracking.
   - SIM-Device Mismatch Rule (`R_SIM_DEVICE_MISMATCH`): detecting SIM swaps or device changes for a payer history.
   - Impossible Travel Rule (`R_IMPOSSIBLE_TRAVEL`): distance calculation (Haversine/coordinates/locations) vs elapsed time (>500km in <30min).
   - Datacenter/VPN IP Rule (`R_DATACENTER_IP`): IP range verification (cloud/datacenter/Tor/VPN CIDRs/subnets).
   - Campaign DNA Fingerprinting (`R_CAMPAIGN_MATCH`): signature extraction on BLOCK/CONFIRMED_FRAUD, similarity scoring against campaign store, returning `campaign_id` and rule in breakdown.
5. Identify any potential breaking changes to existing tests and how to ensure 100% backward compatibility.

Write a complete, structured report to:
/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_engine/handoff.md
Send a completion message when finished.
