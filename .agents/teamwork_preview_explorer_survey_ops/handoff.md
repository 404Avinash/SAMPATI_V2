# Handoff Report: Operations & Encyclopedia Survey Explorer

**Agent:** Explorer 2 (`teamwork_preview_explorer_survey_ops`)  
**Timestamp:** 2026-09-02T17:46:00Z  
**Handoff Type:** Hard (Task Complete)

---

## 1. Observation

1. **`ENCYCLOPEDIA.md` Algorithmic Definitions & Structures:**
   - **Dead Money Velocity (DMV)** (`app/engine/dmv.py`, `ENCYCLOPEDIA.md:374-398, 1153-1156, 1195-1199`):
     - Uses sliding window ratio analysis via `collections.deque` with $O(1)$ eviction. Formula: $f(\text{dormancy\_gap}, \text{velocity}, \text{depletion\_ratio})$.
     - Real-world equivalent: **Token Bucket Algorithm** with time decay.
     - Severity tiers: $<40$ Normal, $40\text{--}70$ Elevated, $>70$ Critical.
   - **Adaptive EWMA Anomaly Model** (`app/engine/adaptive.py`, `ENCYCLOPEDIA.md:347-373, 1101-1104, 1207-1213`):
     - Streaming statistics without database storage. Maintains running mean $\mu$ and variance $\sigma^2$ with exponential decay $\alpha$.
     - Computes $Z$-score $Z = \frac{|x - \mu|}{\sqrt{\sigma^2}}$ and anomaly score $\le 25$ pts.
     - Real-world equivalent: **Exponential Smoothing / Holt-Winters** and streaming state estimation.
   - **Deterministic Structural Rules** (`app/engine/upi_rules.py`, `ENCYCLOPEDIA.md:321-344`):
     - `PASS_THROUGH_CONDUIT` (30 pts, inflow $\ge ₹5000$, forwarding $\ge 90\%$, age $<30$d).
     - `FAN_IN_BURST` (25 pts, $\ge 5$ distinct payers in window to fresh account $<30$d).
     - `FAN_OUT_DISPERSAL` (25 pts, $\ge 5$ distinct payees in window from fresh account $<30$d).
     - `NEW_ACCOUNT_HIGH_VALUE` (15--50 pts, account $<15$d moving $\ge ₹10,000$ to $\ge ₹1,000,000$).
     - `NEW_PAYEE_VPA` (25 pts, payee registered $<15$d).
     - `LIMIT_SKIRTING` (10 pts, smurfing/structuring within 2% below caution thresholds ₹10k, ₹15k, ₹25k, ₹50k, ₹100k).
     - `R_HONEYPOT_HIT` (100 pts, hit against 14 seeded honeypot VPAs in `app/engine/honeypot.py`).
     - `R_SIM_DEVICE_MISMATCH` (30 pts, SIM swap / device handover).
     - `R_IMPOSSIBLE_TRAVEL` (35 pts, Haversine great-circle speed $>1000$ km/h or $>500$ km in $<30$ min).
     - `R_DATACENTER_IP` (25 pts, cloud provider / VPN CIDR match).
     - `R_CAMPAIGN_MATCH` (30 pts, 4D weighted cosine similarity $\ge 0.82$ against known campaign fingerprints in `app/engine/campaign.py`).
   - **Node Role Classification & Graph Theory** (`app/services/upi_cases.py`, `ENCYCLOPEDIA.md:422-438, 1157-1160, 1214-1220`):
     - Directed graph ($\text{DiGraph}$) centrality analysis classifying nodes into **Victim**, **Collector Hub**, **Layering Hop**, and **Cash-Out**.
   - **Privacy-Preserving Federation Mesh** (`app/federation/coordinator.py`, `app/federation/psp_node.py`, `ENCYCLOPEDIA.md:440-496, 1093-1096, 1280-1304`):
     - SHA-256 with shared salt pseudonymization. Sub-5ms in-memory cache lookup. Promotes connected components ($\ge 3$ members across $\ge 2$ PSPs) into confirmed `MuleRing` records.

2. **Existing Backend Implementation for Target Operations:**
   - **Operation A (Block/Hold Entity)**:
     - `UpiCaseService.update_case_status(case_id, new_status, ...)` (`app/services/upi_cases.py:637-783`).
     - Marks confirmed fraud in memory: `self.scorer.state.mark_confirmed_fraud(member_vpas)`.
     - Ingests DPIP external signal: `self.dpip.ingest_external_signal(v, risk=1.0, source="...")`.
     - Feeds adaptive model: `self.adaptive.feedback(member_vpas, confirmed_fraud=True)`.
     - Asynchronous PostgreSQL persistence via `_schedule_db_save_case` and `_schedule_db_save_feedback`.
     - WebSocket broadcast of `CASE_STATUS_UPDATED` and `stats_update`.
   - **Operation B (Trigger Federation Round)**:
     - `UpiCaseService.run_federation()` (`app/services/upi_cases.py:1125-1132`) and `FederatedCoordinator.run_federation_round()` (`app/federation/coordinator.py:269-375`).
     - Collects distributed shares, merges features, discovers multi-PSP rings, attaches SARs to open cases, renders ring graphs, schedules DB saves, and broadcasts `FEDERATION_ROUND` and `stats_update`.
   - **Operation C (Export SAR to PDF)**:
     - `UpiCaseService.generate_sar_pdf(case_id)` (`app/services/upi_cases.py:1201-1208`) and `build_sar_pdf(case_data)` (`app/forensics/sar_pdf.py:29-238`).
     - Renders 2-page publication-grade PDF using `matplotlib` (non-interactive `Agg` backend) containing executive summary, trigger transaction DNA, explainable rule breakdown, participating ring topology, embedded ring graph image, and formal FIU-IND narrative.
     - Endpoint `GET /cases/{case_id}/sar/pdf` returns binary streaming `Response(content=pdf_bytes, media_type="application/pdf")`.
   - **Operation D (Simulate Transaction Batch)**:
     - `generate_labeled_stream(total_txns, fraud_ratio, seed)` (`app/synthetic/upi_generator.py`) and `POST /upi/simulate` (`app/api/upi.py:520-590`).
     - Evaluates transactions through inline gate (`svc.evaluate(txn)`), triggers optional federation consensus, persists opened cases and rings, and broadcasts `UPI_EVALUATED`, `new_case`, `UPI_CASE_OPENED`, and `SIMULATION_COMPLETE`.

3. **Current Gemini Copilot Service Architecture:**
   - `GeminiCopilotService` in `app/services/gemini_service.py` provides:
     - `generate_case_briefing(case_data, force_refresh)`
     - `chat_with_case_copilot(case_data, question, conversation_history)`
     - `generate_sar_report(case_data)` and `generate_sar_narrative(case_data)`
   - Full test suite in `tests/test_gemini_copilot.py` (27 passed in 1.86s). Total repository test suite: 737 tests passing.

---

## 2. Logic Chain

1. **Context Injection Logic**:
   - The user requests that the Assistant explain *exactly* why a rule fired in plain English (e.g. why DMV score spiked).
   - `ENCYCLOPEDIA.md` contains exact mathematical principles, parameter thresholds, and regulatory justifications for each rule and ML layer (Observation 1).
   - By structuring these definitions into an in-memory knowledge index (`app/engine/encyclopedia_kb.py`) and dynamically extracting matching rule definitions for a specific case, the Assistant's system prompt receives deep, precise context without token bloat or hallucination risk.

2. **Agentic Function Calling Routing Logic**:
   - The platform must support both production deployments (with valid `GEMINI_API_KEY`) and CI/CD / offline testing environments.
   - For Gemini API calls, we declare standard OpenAPI/JSON-Schema `functionDeclarations` for `trigger_federation_round`, `simulate_transactions`, `block_or_hold_entity`, and `export_sar_pdf`.
   - For offline/fallback execution, we implement a deterministic regex/semantic intent router in `gemini_service.py` that intercepts user instructions like *"Trigger a federation round"* or *"Simulate 50 transactions"*.
   - Both modes route into the same Python backend execution handlers (`svc.run_federation()`, `svc.simulate()`, `svc.update_case_status()`, `svc.generate_sar_pdf()`) (Observation 2).

3. **Structured Response & UI Integration Logic**:
   - Returning structured `tool_executions` alongside natural language `answer` in `/cases/{case_id}/ai-chat` allows the React frontend (`CaseAiCopilotView.jsx` -> `CaseAiAssistantView.jsx`) to display interactive visual cards and download buttons for executed actions.

---

## 3. Caveats

- **External Gemini Network Isolation in Sandbox/CI**: External HTTP calls to `https://generativelanguage.googleapis.com` are mocked or run in fallback mode during local testing. The agentic loop must guarantee that the fallback intent router handles all 4 operations deterministically when no API key is present.
- **Simulation Batch Ceilings**: Batch simulation must remain bounded ($N \le 500$) to prevent memory pressure on constrained EC2 `t3.small` instances.

---

## 4. Conclusion

1. The technical survey of `ENCYCLOPEDIA.md` reveals 12 primary algorithmic models and rule families that should be indexed into `app/engine/encyclopedia_kb.py`.
2. All 4 target operations already have battle-tested backend execution pathways in `UpiCaseService`, `FederatedCoordinator`, `sar_pdf.py`, and `upi_generator.py`.
3. An Agentic Execution Loop with dual-mode dispatch (Gemini API tool declarations + deterministic regex fallback intent routing) will provide 100% testable, zero-friction function calling for the Assistant.
4. The comprehensive analysis has been documented in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ops/analysis.md`.

---

## 5. Verification Method

To verify the findings and existing baseline:
1. **Pytest Suite Verification**:
   ```bash
   ./.venv/bin/pytest tests/test_gemini_copilot.py -v
   ./.venv/bin/pytest tests/ -v
   ```
   *Expected: All 737 tests collect and pass with 0 failures.*
2. **Frontend Quality Verification**:
   ```bash
   cd frontend && npm run lint && npm run build
   ```
   *Expected: ESLint reports 0 errors and 0 warnings (`--max-warnings 0`), Vite build succeeds.*
3. **Artifact Inspection**:
   - Inspect `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ops/analysis.md`
   - Inspect `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_ops/handoff.md`
