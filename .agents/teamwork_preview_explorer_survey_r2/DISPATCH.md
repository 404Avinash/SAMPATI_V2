# Dispatch: teamwork_preview_explorer_survey_r2

## Mission
Investigate R2: Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP) & Frontend Dashboard Integration for SAMPATI V2.

## Working Directory
/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r2/

## Mandatory Reading
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read the latest request from 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/DISPATCH.md`

## Objectives
1. Investigate existing honeypot/mule detection, `StandardFraudSignal` in `app/models/`, threat intel ingestion in `app/api/` (e.g. `/intel/signals`), and transaction evaluation in `app/engine/`.
2. Determine how the 3 simulated institutional signal adapters should be designed:
   - Mock NPCI MuleHunter Adapter: returns realistic mule-probability score for VPA/account.
   - Mock DPIP Smart Registry Adapter: query/update national fraud registry by VPA hash, returning threat level.
   - Mock PSP Adapter (e.g. PhonePe, Paytm): produces standard fraud signals using `StandardFraudSignal` format.
3. Determine deterministic rules for VPA characteristics (e.g. honeypot/known-bad VPAs return HIGH from mock NPCI and non-zero `mock_npci_score` & `mock_dpip_threat_level` in verdict response).
4. Determine schema changes in `/upi/check` response (e.g. `mock_npci_score`, `mock_dpip_threat_level`, contributing signals) and how they integrate into scoring.
5. Determine frontend dashboard components that need to display these contributing signal sources with institution labels (e.g. CaseDrawer, Threat Intel tab, Overview, etc.).
6. Write your findings to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r2/handoff.md`.

## 2026-09-04T01:45:37Z
Investigate R2: Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP) & Frontend Dashboard Integration.
Explore the existing codebase:
- Examine app/models/ (StandardFraudSignal, UpiEvaluationResponse, etc.), app/api/ (intel/signals, upi, etc.), and app/engine/.
- Check how honeypots and mule accounts are currently defined and flagged.
- Design the 3 simulated institutional signal adapters:
  1. Mock NPCI MuleHunter Adapter (returns mule-probability score).
  2. Mock DPIP Smart Registry Adapter (queries/updates national fraud registry by VPA hash, returning threat level).
  3. Mock PSP Adapter (PhonePe, Paytm, etc. producing StandardFraudSignal).
- Design deterministic VPA mapping so honeypot/known-bad VPAs return HIGH from mock NPCI and non-zero mock_npci_score and mock_dpip_threat_level in verdict response.
- Explore frontend components (CaseDrawer, Threat Intelligence tab, Overview, etc.) to see how contributing signal sources should be clearly displayed with institution labels.
- Document all findings, file paths, concrete implementation steps, and verification strategies in handoff.md in your working directory.
Communicate completion back with send_message.
