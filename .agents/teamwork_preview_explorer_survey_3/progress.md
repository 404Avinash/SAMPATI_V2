# Progress Heartbeat

**Last visited**: 2026-09-03T09:45:00Z
**Status**: Complete

## Tasks Checklist - Survey R3 (ML Layer & Terminology Overhaul)
- [x] Initialize briefing, dispatch, progress files
- [x] Read ORIGINAL_REQUEST.md (2026-09-03T09:32:24Z) and DISPATCH.md
- [x] Investigate ML Layer: `app/engine/upi_scorer.py`, `app/engine/`, `scikit-learn` IsolationForest configuration, feature vectors, `ml_anomaly_score` in [0.0, 1.0], `/upi/check` response schema (`UpiEvaluationResponse`), verdict integration
- [x] Investigate "Dead Money Velocity" / "DMV" occurrences across frontend and backend, rename plan to "Dormant-to-Active Velocity" preserving contract compatibility
- [x] Investigate "Criminal Network" / "Criminal Hierarchy" occurrences, rename plan to "Suspected Mule Cluster" (ensure 0 in frontend)
- [x] Investigate "100% confidence" / "100% traceable" claims and find defensible signal-correlation replacements
- [x] Investigate tagline "Everyone sees a piece. SAMPATI connects the dots." placement (Overview header banner, navigation, masthead)
- [x] Check existing pytest suite (`.venv/bin/pytest tests/ -v`, 833+ tests -> 850 passed in 162.17s) and affected tests
- [x] Synthesize findings into Features Discovered and Edge Cases tables in analysis.md and handoff.md
- [x] Complete handoff.md following 5-component format
- [x] Update BRIEFING.md and notify parent via send_message



