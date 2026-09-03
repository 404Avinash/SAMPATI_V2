# Dispatch for teamwork_preview_explorer_survey_3

- Role: ML & Terminology Spec Miner
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3
- Parent orchestrator: teamwork_preview_orchestrator_10
- Objective: Survey R3 (Unsupervised Isolation Forest model in app/engine/upi_scorer.py, ml_anomaly_score in /upi/check, global terminology overhaul removing "Dead Money Velocity" and "Criminal Network", stripping 100% confidence, adding tagline "Everyone sees a piece. SAMPATI connects the dots.").

## 2026-09-03T09:35:33Z
You are teamwork_preview_explorer_survey_3 (teamwork_preview_spec_miner).
Your working directory is `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3`.
You MUST read the authoritative user request at `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (especially the latest section timestamp 2026-09-03T09:32:24Z) and your dispatch at `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/DISPATCH.md`.

Your mission:
Investigate the exact specifications and code locations for Requirement 3 (ML Layer & Terminology Overhaul):
1. Investigate `app/engine/upi_scorer.py`, `app/engine/`, and any existing Isolation Forest files (such as `app/engine/isolation_forest.py` or similar if drafted). Determine:
   - How `scikit-learn` IsolationForest or custom iForest is configured and instantiated.
   - How feature vectors are extracted from transaction and state (e.g. amount, time-of-day, velocity, etc.).
   - How `ml_anomaly_score` in [0.0, 1.0] is computed and incorporated into the `/upi/check` response JSON schema (`UpiEvaluationResponse` in `app/models/upi_models.py` or similar).
   - How it factors into the final verdict (e.g., points or floor).
2. Investigate all occurrences of "Dead Money Velocity" across frontend and backend:
   - Find all files containing "Dead Money Velocity" or "DMV" and identify where it must be renamed to "Dormant-to-Active Velocity" without breaking internal abbreviations where required or keeping contract compatibility.
3. Investigate all occurrences of "Criminal Network" or "Criminal Hierarchy" across frontend and backend:
   - Identify every frontend file to ensure 0 occurrences remain for "Dead Money Velocity" and "Criminal Network".
4. Investigate all "100% confidence" / "100% traceable" claims and find where they need to be replaced with defensible signal-correlation phrasing.
5. Identify where the tagline "Everyone sees a piece. SAMPATI connects the dots." must be added (e.g., Overview header banner, navigation, masthead).
6. Check existing pytest suite (`.venv/bin/pytest tests/ -v`, currently 833+ tests) and see what tests currently touch these areas.

Write your findings and recommendations into `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/handoff.md`.
Use send_message to notify parent when complete with the path to your handoff file.
