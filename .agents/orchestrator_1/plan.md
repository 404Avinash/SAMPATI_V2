# Plan — Sprint 2 Continuation Orchestration

## Objective
Deliver and verify all requirements of Sprint 2 Continuation:
1. SAR PDF Export (reportlab): `GET /cases/{case_id}/sar/pdf` & `GET /upi/cases/{case_id}/sar/pdf`
2. Workload Heatmap in Analytics: 7x24 grid in `/upi/stats/analytics` and `/stats/analytics`
3. Live Auto-Feed Engine: `POST /upi/autofeed/start`, `GET /upi/autofeed/status`, `POST /upi/autofeed/stop`
4. Scoring Fix: escalating risk points for very large transfers on new accounts
5. Frontend Dashboard Updates: CaseDrawer DMV gauge, Analytics Top VPAs by DMV table, Analytics 7x24 heatmap, Overview/ControlBar Live Auto-Feed toggle, CaseDrawer Export SAR PDF button.
6. Verification & Commit:
   - pytest tests/test_sprint2_e2e_suite.py -> 110 passed
   - pytest tests/ --ignore=tests/test_sprint2_e2e_suite.py -> 559 passed
   - cd frontend && npm run build -> clean build
   - commit changes

## Decomposition & Execution Strategy
- Track 1 (Backend Services & Engine):
  - Worker to implement SAR PDF generator with reportlab (`app/forensics/sar_pdf.py` or `app/services/upi_cases.py`), 7x24 Heatmap in analytics, Auto-Feed Engine (`app/services/autofeed.py` & `/upi/autofeed/*` endpoints), and scoring fix for mega-transfers on new accounts in `app/engine/upi_rules.py`.
- Track 2 (Frontend Integration):
  - Worker to update CaseDrawer (DMV gauge, Export SAR button), AnalyticsPage (7x24 Workload Heatmap, Top VPAs by DMV table), and ControlBar / AppStateContext (Auto-Feed controls & state).
- Track 3 (Review & Verification):
  - Reviewers and Challengers to verify correctness, test passing (110 sprint2 tests, 559 original tests), and frontend build.
- Track 4 (Forensic Audit & Commit):
  - Forensic Auditor to check genuine implementation and absence of hardcoded hacks.
  - Final safe commit and push sequence according to repository guidelines.
