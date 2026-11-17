# Handoff Report: ML & AI Engine Architecture Survey for SAMPATI V2

**Agent**: ML & AI Engine Architecture Explorer  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ml`  
**Recipient**: Parent Orchestrator (`d7ee2688-0be6-4bc5-b9ec-8b4f7ccf2e64`)  
**Type**: Hard Handoff (Task Complete)  
**Deliverable**: Comprehensive Technical Report at `report.md`  

---

## 1. Observation

Direct investigation of the codebase and test suite revealed the following architectural implementations:

1. **Layer 1: Deterministic Rules & Heuristic State Engines**:
   - `app/engine/upi_rules.py`: Contains 13 deterministic rule functions (`rule_honeypot_hit` [100 pts], `rule_impossible_travel` [35 pts], `rule_sim_device_mismatch` [30 pts], `rule_datacenter_ip` [25 pts], `rule_campaign_match` [30 pts], `rule_new_payee_vpa` [25 pts], `rule_pass_through_conduit` [30 pts], `rule_fan_in_burst` [25 pts], `rule_fan_out_dispersal` [25 pts], `rule_device_farm` [20 pts], `rule_new_account_high_value` [15-50 pts], `rule_limit_skirting` [10 pts], `rule_known_fraud_entity` [35 pts]).
   - `app/engine/dmv.py`: Implements the `DmvTracker` class computing Dead Money Velocity from sliding-window dormancy $D = \min(1.0, \Delta t / 30.0)$ and burst drain ratio $R = \min(1.0, \text{outflow}_{1h} / \text{inflow}_{24h})$, with a non-linear escalation multiplier ($1.0 + 0.5 \cdot D \cdot V$) for $D \ge 0.5, V \ge 0.4$.
   - `app/engine/campaign.py`: Implements `CampaignSignatureStore` using cosine-like multi-attribute similarity matching (keywords, amount ranges, temporal buckets, and member VPAs) with dynamic fingerprint ingestion on `BLOCK` verdicts.
   - `app/engine/honeypot.py`: Implements `HoneypotRegistry` tracking 14 seeded decoy VPAs and prefix matching.

2. **Layer 2: Unsupervised Anomaly Detection (Isolation Forest)**:
   - `app/engine/isolation_forest.py`: Canonical Liu, Ting, Zhou (2008) mathematical formulation implemented in pure Python/NumPy (`PureNumpyIsolationForest`) and optional `SklearnIsolationForestAdapter`.
   - Uses $c(n) = 2(\ln(n - 1) + 0.5772156649) - \frac{2(n - 1)}{n}$ and raw anomaly score $s(x, n) = 2^{-\mathbb{E}(h(x))/c(n)}$.
   - Ensemble parameters: 50 iTrees, subsample size 128 (height limit 7).
   - Trained on legitimate retail UPI baseline (~600 samples) with a 3.5% contamination rate.
   - Normalization function maps $s \le 0.50 \to s \times 0.96 \le 0.48 < 0.50$ (Zero-regression invariant, 0 risk points) and scales $s > 0.50$ monotonically into $[0.50, 1.0]$.
   - Extracts 13 standardized numerical features (`FEATURE_NAMES` lines 298-312).

3. **Layer 3: Supervised Classification (Random Forest)**:
   - `app/engine/supervised_classifier.py`: Custom `PureNumpyStandardScaler`, `PureNumpyDecisionTree` (Gini impurity split $I_G = 2p(1 - p)$, percentile split candidates), and `PureNumpySupervisedClassifier` (30 bagged trees, max depth 6, class-weight balanced bootstrap sampling $w = \frac{N}{2N_c}$).
   - `app/engine/train_supervised.py`: End-to-end training and evaluation pipeline on PaySim benchmark data, achieving Precision $0.9793$, Recall $0.9467$, F1-score $0.9627$, and an 83.33% relative False Negative reduction over the Isolation Forest baseline.
   - Calibrates probabilities into risk tiers with `SUPERVISED_FRAUD_DETECTED` at $\ge 0.70$ and `HOLD` floor at $\ge 0.85$. Serializes model artifact to `app/engine/artifacts/supervised_fraud_model.pkl`.

4. **Ensemble Scoring & Decision Gating**:
   - `app/engine/upi_scorer.py`: Evaluates transactions in sub-1.5ms:
     $$\text{Combined} = S_{\text{rule}} (0-100) + P_{\text{adaptive}} (0-25) + P_{\text{network}} (0-40) + P_{\text{ml}} (0-25)$$
     Decision thresholds: $\ge 70 \implies \text{BLOCK}$, $\ge 45 \implies \text{HOLD}$, else $\implies \text{ALLOW}$.
     Override floors: If $S_{\text{network}} \ge 0.70$ or $S_{\text{ml}} \ge 0.85$ or $S_{\text{supervised}} \ge 0.85 \implies \text{HOLD}$ floor enforced.

5. **Layer 4: Generative AI & Google Gemini Integration**:
   - `app/services/gemini_service.py`: Direct REST client (`v1beta`) targeting `gemini-1.5-flash` with fallbacks (`1.5-flash-8b`, `2.0-flash`, `1.5-pro`).
   - Deep context injection via `build_case_dossier_text` combining telemetry, raw transaction ledger, graph topology, and mathematical rule formulas from `app/engine/encyclopedia_kb.py`.
   - Autonomous Function Calling declarations (`block_vpa_or_transaction`, `trigger_federation_round`, `export_sar_pdf`, `simulate_transactions`).
   - Deterministic Offline Intent Router (`_match_intent`) using regex pattern matching when API key is missing or offline.
   - Multimodal token economy compression: 258 vision tiles + 75 prompt tokens = 333 tokens vs 15,000 text ledger tokens (45x compression ratio, >97% LLM cost reduction).
   - Regulatory SAR PDF pipeline in `app/forensics/sar_pdf.py` compiling 2-page FIU-IND Form 17B documents with embedded graph diagrams.

---

## 2. Logic Chain

1. Modern real-time payment systems cannot afford synchronous external network calls during inline evaluation ($<5\text{ms}$ SLA).
2. SAMPATI V2 satisfies this constraint by executing Layers 1, 2, 3, and the Ensemble Scorer purely locally in CPU memory via vectorized NumPy routines, completing the entire inline scoring pass in $1.2\text{ms} - 1.5\text{ms}$.
3. Layer 1 alone cannot catch zero-day attacks or subtle structurings; therefore, Layer 2 (unsupervised Isolation Forest) isolates multivariate behavioral anomalies, while Layer 3 (supervised Random Forest) eliminates false negatives on subtle dormant-account drain schemes.
4. To prevent conflicting verdicts, the Ensemble Scorer enforces hierarchical gating and safety floors: an extreme score from any advanced model ($S_{\text{ml}} \ge 0.85$ or $S_{\text{supervised}} \ge 0.85$) immediately triggers a `HOLD` floor regardless of other channels.
5. Once a case is flagged (`HOLD` or `BLOCK`), asynchronous post-transaction intelligence takes over: Layer 4 (Google Gemini) receives the case dossier enriched with exact mathematical formulas from the Encyclopedia Knowledge Base, generating plain-English executive briefings and legal Form 17B SAR reports for FIU-IND compliance.
6. In offline or rate-limited conditions, deterministic intent routers and heuristic fallback generators maintain 100% operational uptime without throwing unhandled exceptions.

---

## 3. Caveats

1. **Simulated Institutional Adapters**: `mock_npci_score` and `mock_dpip_threat_level` are currently driven by deterministic simulation adapters (`app/adapters/service.py`) rather than live NPCI/DPIP production VPN sockets.
2. **PostgreSQL / Redis Connection Fallback**: When external PostgreSQL or Redis services are not running locally, the system automatically falls back to thread-safe in-memory stores (`InMemoryStore`, `UpiHotState`), allowing full local testing and zero service degradation.
3. **External Gemini API Key**: In production, `GEMINI_API_KEY` must be set in the environment for live Google Gemini calls; otherwise, the system transparently utilizes the deterministic offline intent router and Encyclopedia KB fallbacks.

---

## 4. Conclusion

The Machine Learning and Generative AI subsystems of SAMPATI V2 provide an enterprise-grade, defense-in-depth architecture. The platform achieves $<1.5\text{ms}$ inline inference, catches both known fraud syndicates and zero-day multivariate anomalies, provides F1-scores $>0.96$ on benchmark distributions, and integrates autonomous LLM reasoning with multimodal token compression and regulatory compliance automation.

All findings, mathematical formulas, feature lists, prompt schemas, and interaction matrices have been compiled into the exhaustive technical report at:
`/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ml/report.md`

---

## 5. Verification Method

To independently verify all findings and test suites:

```bash
# 1. Run the Isolation Forest test suite
./.venv/bin/pytest tests/test_isolation_forest.py -v

# 2. Run the Supervised Model test suite
./.venv/bin/pytest tests/test_supervised_model.py -v

# 3. Run the Gemini Copilot and Assistant test suites
./.venv/bin/pytest tests/test_gemini_copilot.py tests/test_gemini_assistant_agentic.py -v

# 4. Run the Full End-to-End Suite
./.venv/bin/pytest tests/test_e2e_suite.py -v

# 5. Run Python linter
./.venv/bin/ruff check app tests
```
