# Handoff Report: Milestone M1 — Encyclopedia Knowledge Base Exploration

## 1. Observation
- **Scope & Mission:** Milestone M1 requires extracting all mathematical formulas, algorithmic definitions, anomaly thresholds, and plain-English detection rationales from `ENCYCLOPEDIA.md` and the SAMPATI V2 backend to inform the Knowledge Base layer (`app/engine/encyclopedia_kb.py`).
- **Core Files Inspected:**
  1. `ENCYCLOPEDIA.md` (Lines 1–1647): Comprehensive technical architecture, algorithms, and glossary across 32 sections.
  2. `app/engine/dmv.py` (Lines 1–199): Implementation of Dead Money Velocity scoring, sliding deques (720h window), dormancy calculations, and burst velocity indices.
  3. `app/engine/adaptive.py` (Disassembled bytecode): Implementation of streaming online EWMA (`EWMA_ALPHA = 0.25`), Welford running variance, inter-arrival gap speedup, Z-score normalization, and sensitivity adaptation.
  4. `app/engine/upi_rules.py` (Lines 1–431): Deterministic rule definitions (`R_HONEYPOT_HIT`, `R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`, `PASS_THROUGH_CONDUIT`, `FAN_IN_BURST`, `FAN_OUT_DISPERSAL`, `DEVICE_FARM`, `NEW_ACCOUNT_HIGH_VALUE`, `LIMIT_SKIRTING`, `KNOWN_FRAUD_ENTITY`).
  5. `app/engine/campaign.py` (Lines 1–288): Multi-vector Cosine similarity matching (`R_CAMPAIGN_MATCH`, threshold 0.82) with keyword (0.35), amount (0.30), temporal (0.15), and entity (0.20) weightings.
  6. `app/engine/honeypot.py` (Lines 1–192): Synthetic decoy registry containing 14 seeded addresses, prefix pattern matchers, and 100-point instant block logic.
  7. `app/federation/coordinator.py` (Lines 1–403): Privacy-preserving SHA-256 salted pseudonymization, multi-PSP graph consensus, and ring promotion ($\ge 3$ members across $\ge 2$ PSPs).
  8. `app/services/upi_cases.py` (Lines 1–1200): Graph ML topology role categorization (Victim, Collector Hub, Layering Hop, Cash-Out), token economy metrics, and SAR generation.

## 2. Logic Chain
1. **From Observation 1 & 2 (DMV Engine):** Analysis of `app/engine/dmv.py:145-198` and `ENCYCLOPEDIA.md:374-398` reveals that DMV is calculated from a Dormancy Index $D$ and Burst Velocity Index $V$. $D$ measures the gap relative to 30 days. $V$ measures drain ratio ($O_{1h}/I_{24h}$), transaction rate, and amount factor. A synergistic multiplier $1.0 + 0.5(D \cdot V)$ applies when $D \ge 0.5$ and $V \ge 0.4$.
2. **From Observation 3 (Adaptive EWMA):** In `app/engine/adaptive.py`, online streaming statistics update with $\alpha = 0.25$. Running variance is updated as $(1-\alpha)\sigma^2_{t-1} + \alpha(x_t - \mu_{t-1})^2$. Z-score is smoothed via $\tanh(Z/3.0)$ and transaction gap acceleration via $\tanh((S-1)/20.0)$. An adaptive score $\ge 0.60$ flags `BEHAVIORAL_ANOMALY`.
3. **From Observation 4 (Rules & Telemetry):** `app/engine/upi_rules.py` implements explainable rules with specific numeric thresholds:
   - `LIMIT_SKIRTING`: Amount in $[0.98 \times T, T)$ for $T \in \{10k, 15k, 25k, 50k, 100k\}$.
   - `PASS_THROUGH_CONDUIT`: Account age $<30$d, inflow $\ge ₹5,000$, outflow ratio $\ge 90\%$, transfer $\ge 50\%$ of window inflow.
   - `FAN_IN_BURST` & `FAN_OUT_DISPERSAL`: Fresh account with $\ge 5$ distinct counterparties.
   - `R_IMPOSSIBLE_TRAVEL`: Haversine velocity $>1000$ km/h over $>50$ km or $>500$ km in $<30$ min.
   - `R_SIM_DEVICE_MISMATCH`: SIM swap ($D_t = D_{prev}, S_t \ne S_{prev}$) or device switch ($S_t = S_{prev}, D_t \ne D_{prev}$).
4. **From Observation 5 (Campaign DNA):** `app/engine/campaign.py` computes composite similarity $S = 0.35 S_{kw} + 0.30 S_{amt} + 0.15 S_{hour} + 0.20 S_{vpa}$. Trigger threshold is $\ge 0.82$ for `R_CAMPAIGN_MATCH`.
5. **From Observation 6, 7 & 8 (Network & Topology):** In `app/services/upi_cases.py` and `app/federation/coordinator.py`, directed graphs categorize nodes into Source/Victim, Collector Hub, Layering Hop, and Cash-Out. Multi-PSP consensus identifies rings when $\ge 3$ members span $\ge 2$ PSPs.
6. **Synthesis:** All mathematical models, threshold parameters, and plain-English narrative templates have been cataloged in `analysis.md`, providing a direct blueprint for implementing `app/engine/encyclopedia_kb.py`.

## 3. Caveats
- No source code in `app/` or `frontend/` was modified during this investigation, adhering to the read-only explorer constraint.
- The compiled stubs in `.pyc` were disassembled and verified against runtime bytecode to ensure exact numerical parity with production behavior.
- No caveats regarding completeness of formulas or detection rationales.

## 4. Conclusion
The comprehensive formula dictionary and explanation templates have been generated and documented in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/analysis.md`. The knowledge base is fully prepared for implementation in Milestone M1 (`app/engine/encyclopedia_kb.py`) and prompt assembly in Milestone M2.

## 5. Verification Method
- **Inspection:** Inspect `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/analysis.md` to review the complete formula dictionary and plain-English templates.
- **Test Suite Execution:** Verify that existing backend tests continue to pass:
  ```bash
  ./.venv/bin/pytest tests/ -v
  ```
- **Code Parity Check:** Cross-reference formula parameters in `analysis.md` with `app/engine/dmv.py`, `app/engine/upi_rules.py`, and `app/engine/campaign.py`.
