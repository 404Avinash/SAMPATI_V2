## 2026-08-31T03:22:07Z

You are the Master Project Orchestrator (teamwork_preview_orchestrator_5) for SAMPATI V2 Sprint 2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_5/
Original user request is authoritative and recorded at: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md

Mission & Objectives:
Complete the full PRD (F-04 through F-08) + Autonomous Live Auto-Feed mode for SAMPATI V2:
1. R1. Dead Money Velocity (DMV) Score (0–100) per-VPA in `/upi/check`, CaseDrawer gauge (green/amber/red), "Top VPAs by DMV Score" table in Analytics.
2. R2. Device Telemetry Enrichment (3 New Scoring Rules: `R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`) integrated into risk engine, rule_breakdown, and scored appropriately.
3. R3. Transaction DNA Campaign Fingerprinting (`R_CAMPAIGN_MATCH`, fingerprint store on BLOCK verdicts, campaign identifier).
4. R4. One-Click SAR PDF Export (`GET /cases/{case_id}/sar/pdf` with narrative, ring member list, embedded forensic graph; "Export SAR" button in CaseDrawer).
5. R5. Analyst Workload Heatmap (7x24 grid in Analytics page reflecting case timestamps).
6. R6. Live Auto-Feed Mode (Autonomous background transaction generation at ~5-20 tx/s, full live pipeline scoring, WebSocket `/ws/feed` broadcast, live KPI tile ticking, real-time constellation updates on ring detection, clean toggle start/stop).

Integrity & Quality Gates:
- Maintain 100% pass on all existing backend tests (`./.venv/bin/pytest tests/ -v`) + add thorough tests for all new endpoints, rules, and behaviors.
- Ensure frontend compiles cleanly (`cd frontend && npm run build` and `npm run lint`).
- Ensure no mock-only shortcuts that break live integration — make it defensible for bank engineers and judges.
- Regularly update `progress.md` and `plan.md` in your working directory.
- When all requirements are implemented and verified, deliver your final handoff and message the sentinel.
