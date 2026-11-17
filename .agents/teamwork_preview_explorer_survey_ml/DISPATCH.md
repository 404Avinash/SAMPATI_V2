## 2026-09-04T22:07:09Z

You are an ML & AI Engine Architecture Explorer for SAMPATI V2.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ml.
Project root: /home/avi/Downloads/Sampati_v2.
Original request file: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md.

Task:
Perform an exhaustive architectural survey of the Machine Learning and Generative AI subsystems of SAMPATI V2 in /home/avi/Downloads/Sampati_v2/app (check app/ml, app/rules, app/services, etc.).

Investigate and document in full detail:
1. Multi-Layer Defense Architecture Overview:
   - Why a layered approach is used (defense-in-depth, latency vs accuracy trade-offs, zero-day vs known patterns).
2. Layer 1: Deterministic Rules Engine:
   - Heuristic rules implemented (geo-velocity impossibility, dead money velocity, sudden volume spikes, structuring/smurfing, etc.).
   - Rule implementation details, thresholds, classes, rule execution flow.
3. Layer 2: Unsupervised Anomaly Detection (Isolation Forest):
   - Model architecture, training baseline (normal traffic), contamination rate.
   - Features used, anomaly score calculation, zero-day fraud pattern detection.
4. Layer 3: Supervised Classification (Random Forest):
   - Model architecture, implementation details (is it pure NumPy, scikit-learn, or custom?).
   - Feature engineering pipeline: exactly what 13 standardized features are extracted, normalization, missing value handling.
   - Evaluation metrics: F1-score, False Positive Rate (FPR), handling of extreme financial class imbalance.
5. Ensemble Scoring Logic:
   - How Layer 1, 2, and 3 scores are combined into a final risk score (weights, formulas, gating, decision thresholds).
   - Verdict classification (ALLOW, REVIEW, BLOCK / FROZEN, MULE_RING).
6. Layer 4: Generative AI & Google Gemini Integration:
   - Gemini API client setup, model selection (e.g., gemini-1.5-flash, gemini-pro), prompt engineering.
   - Forensic Investigator / Explainability: How raw ML scores, feature vectors, and rule violations are translated into plain-English explanations.
   - SAR (Suspicious Activity Report) Generation: Automated regulatory narrative synthesis, PDF generation pipeline.
   - Threat Intelligence & Syndicate Analysis: Detecting coordinated mule accounts.
   - Reliability & Resilience: Rate limiting, fallback handling, mock/offline mode when API key is missing or API times out.

Output:
Write an exhaustive, high-quality technical report to:
/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ml/report.md
Include exact file paths, line references where appropriate, code snippets, mathematical formulas, feature lists, and prompt templates.
When complete, write handoff.md and notify with send_message.
