# Handoff Report: Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP) & Frontend Dashboard Integration (R2)

**Agent ID**: `explorer_survey_r2`  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r2`  
**Target Milestone**: R2 — Simulated Institutional Signal Adapters & Frontend Integration  
**Date**: 2026-09-04T01:50:30Z  

---

## 1. Observation

### 1.1 Existing Models and Schemas
- **`app/models/threat_intel.py`**:
  - Defines `ThreatSignalCreateRequest` (lines 158–234) with fields:
    - `source`: `str = Field(default="external", description="Signal origin: mobile_app, psp_feed, user_report, telecom_feed, honeypot")`
    - `phone`: `Optional[str]`
    - `upi_id`: `Optional[str]`
    - `url`: `Optional[str]`
    - `tags`: `List[str] = Field(default_factory=list)`
    - `raw_content`: `Optional[str]`
    - `severity`: `str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")`
    - `confidence`: `float = Field(default=0.85, ge=0.0, le=1.0)`
  - Contains entity extractor `extract_entities(text: Optional[str]) -> ExtractedEntities` (lines 91–139) with regex patterns `PHONE_REGEX`, `UPI_REGEX`, `URL_REGEX`, and `TAG_PATTERNS`.
  - Defines `ThreatSignalResponse` (lines 251–283) containing `signal_id`, `source`, `phone`, `upi_id`, `url`, `tags`, `severity`, `confidence`, `extracted_entities`, `matched_campaign`, `linked_graph_nodes`, and timestamps.
  - Currently lacks an explicit class named `StandardFraudSignal`. `ORIGINAL_REQUEST.md` (lines 397–398) explicitly requires:
    > "Mock PSP Adapter (e.g., 'PhonePe', 'Paytm'): Produces standardized fraud signals (velocity anomaly, suspicious beneficiary) using the existing `StandardFraudSignal` format."

- **`app/models/upi_models.py`**:
  - `UpiEvaluationResponse` (lines 59–79):
    ```python
    class UpiEvaluationResponse(BaseModel):
        txn_id: str
        risk_score: int
        action: str
        reasons: List[str]
        rule_breakdown: List[RuleHit]
        rule_score: int
        adaptive_score: float
        network_score: float
        ml_anomaly_score: float
        execution_latency_ms: float
        evaluated_at: datetime
        case_id: Optional[str]
        dmv_score: float
        campaign_id: Optional[str]
    ```
  - Currently missing fields required by R1 and R2:
    - `supervised_fraud_score: float` (R1)
    - `mock_npci_score: float` (R2: "returns a non-zero mock_npci_score and mock_dpip_threat_level in the verdict response", line 418)
    - `mock_dpip_threat_level: Union[float, int, str]` (R2: "returns a non-zero mock_npci_score and mock_dpip_threat_level in the verdict response", line 418)
    - `contributing_signals: List[Dict[str, Any]]` (R2: "clearly displayed in the dashboard as contributing signal sources with their institution label", line 398)

### 1.2 Honeypot and Mule Account Identification
- **`app/engine/honeypot.py`**:
  - Seeded synthetic honeypot VPAs (lines 18–33):
    `honeypot_trap_01@okaxis`, `honeypot_mule_99@okhdfcbank`, `phish_trap_node@okicici`, `botnet_sink_04@oksbi`, `mule_honeypot_prime@okaxis`, `trap_collect_007@paytm`, `phish_sink_alpha@ibl`, `mule_decoy_99@ybl`, `honeypot_mule_88@okhdfcbank`, `decoy_phish_trap@oksbi`, `honeypot.sink@upi`, `trap_synthetic@upi`, `darkweb_mule_sink@okaxis`, `honeypot_phish_victim@ybl`.
  - Prefix matching (lines 35–47):
    `("honeypot_", "honeypot.", "phish_trap_", "botnet_sink_", "mule_honeypot_", "trap_sink_", "decoy_mule_", "trap_synthetic", "trap_collect", "decoy_phish")`.
  - `HoneypotRegistry.is_honeypot(vpa)` (lines 61–70): Case-insensitive match against `_honeypots` set or `HONEYPOT_PREFIXES`.
- **`app/engine/upi_rules.py`**:
  - Rule `rule_honeypot_hit(txn, state)` (lines 243–260) triggers `RuleHit(code="R_HONEYPOT_HIT", points=100, detail="Transaction directed to active synthetic honeypot VPA")` when `reg.is_honeypot(txn.payee_vpa)` is true.
  - Rule `rule_known_fraud_entity(txn, state)` (lines 368–380) checks `state.fraud_memory(vpa) > 0` for payer and payee.

### 1.3 Threat Intelligence & Transaction Ingestion Pipelines
- **`app/api/intel.py`**:
  - `POST /signals` (lines 81–110): Ingests pre-transaction signals via `ThreatIntelService.ingest_signal()`, extracts entities, matches campaign clusters, updates `FraudGraphService`, and broadcasts WebSocket event.
  - `GET /signals` (lines 112–140): Paginated queries with filters (`severity`, `source`, `campaign_id`).
  - `GET /graph` (lines 163–190): Exports multi-entity graph with nodes (`VPA`, `PHONE`, `URL`, `CASE`, `CAMPAIGN`, `SIGNAL`) and edges (`EXTRACTED_FROM`, `ASSOCIATED_WITH`, `MEMBER_OF_CAMPAIGN`).
- **`app/services/upi_cases.py`**:
  - `evaluate(txn)` (lines 1014–1065):
    - Queries federated network score: `network = self.federation.network_score_for_txn(txn)`.
    - Queries DPIP score: `external = self.dpip.external_score_for_pair(txn.payer_vpa, txn.payee_vpa)`.
    - Evaluates composite risk score: `resp = self.scorer.evaluate(txn, network_score=combined_network)`.
    - Opens investigative case if action in `("HOLD", "BLOCK")`.
  - `DpipFeed` loaded from `app.dpip.feed`: Has methods `external_score(vpa) -> float`, `ingest_external_signal(vpa, risk, source)`, `publish_confirmed_ring(...)`, and `stats()`.

### 1.4 Frontend Architecture & Institutional Presentation
- **`frontend/src/components/CaseDrawer.jsx`**:
  - Lines 400–550: Renders Case File Dossier with top summary banner (`VerdictBadge`, `StatusBadge`, `RiskScoreBadge`), DMV Arc Gauge (`DmvArcGauge`), and Rule Breakdown chart (`RuleBreakdownChart`).
  - Currently lacks a dedicated panel for institutional contributing signals (NPCI, DPIP, PSP).
- **`frontend/src/pages/ThreatIntelPage.jsx`**:
  - Lines 650–735: Renders live ingested threat signals with severity badges (`CRITICAL`, `HIGH`, `MEDIUM`) and source string (`signal.source`).
  - Lacks branded institution pill badges (e.g. `[NPCI]`, `[DPIP]`, `[PhonePe]`, `[Paytm]`).
- **`frontend/src/components/LiveFeed.jsx`**:
  - Lines 20–65: Renders flagged transactions with table columns `Time`, `Flow`, `Amount`, `Verdict`, `Score`, `Signals`.
  - The `Signals` column currently truncates `(c.reasons || []).slice(0, 2).join(", ")`.
- **`frontend/src/services/api.js`**:
  - Provides REST wrappers for simulation, federation, cases, and threat intelligence (`getThreatSignals`, `ingestThreatSignal`, `getThreatGraph`).
  - Needs endpoints for direct querying of the institutional adapters.

---

## 2. Logic Chain

### 2.1 Design of Adapter 1: Mock NPCI MuleHunter Adapter
1. **Industry Context**:
   NPCI (National Payments Corporation of India) operates the core UPI payment switch. NPCI MuleHunter is an institutional ML model evaluating account velocity, multi-bank linking, and pass-through aggregation across all Indian banks.
2. **Architecture**:
   - Create `app/adapters/npci.py` with class `NpciMuleHunterAdapter`.
   - Pydantic response model:
     ```python
     class NpciMuleHunterResponse(BaseModel):
         vpa: str
         mule_probability: float  # [0.0, 1.0]
         risk_rating: str         # "HIGH", "MEDIUM", "LOW", "CLEAN"
         central_switch_flags: List[str]
         switch_velocity_percentile: float
         evaluated_at: str
     ```
3. **Deterministic VPA Mapping**:
   - **Honeypots** (`get_honeypot_registry().is_honeypot(vpa)`):
     - `mule_probability = 0.96`
     - `risk_rating = "HIGH"`
     - `central_switch_flags = ["CENTRAL_SWITCH_HONEYPOT_SINK", "MULE_CLUSTER_CENTRAL_TRAP", "RAPID_INFLOW_SURGE"]`
     - `switch_velocity_percentile = 99.8`
   - **Known-Bad Keywords** (VPA contains `mule`, `scam`, `fraud`, `phish`, `botnet`, `trap`, `darkweb`, `bad`, `conduit`, `cashout`, `drain`):
     - `mule_probability = 0.92`
     - `risk_rating = "HIGH"`
     - `central_switch_flags = ["KNOWN_MULE_SIGNATURE", "MULTI_BANK_BURST_OUTFLOW"]`
     - `switch_velocity_percentile = 98.5`
   - **Moderate Risk Indicators** (VPA contains `temp`, `transfer`, `fast`, `quick`):
     - `mule_probability = 0.55`
     - `risk_rating = "MEDIUM"`
     - `central_switch_flags = ["UNUSUAL_PSP_CONDUIT"]`
     - `switch_velocity_percentile = 72.0`
   - **Clean / Legitimate VPAs** (standard user/merchant accounts, e.g. `user@okhdfcbank`, `merchant@okaxis`):
     - Deterministic hash-based pseudo-random low score:
       `seed = int(hashlib.sha256(vpa.lower().encode()).hexdigest()[:8], 16)`
       `mule_probability = round((seed % 10) / 100.0, 4)` (e.g., 0.00 to 0.09)
       `risk_rating = "LOW"`
       `central_switch_flags = ["NORMAL_SWITCH_CLEARING"]`
       `switch_velocity_percentile = round(15.0 + (seed % 30), 1)`

### 2.2 Design of Adapter 2: Mock DPIP Smart Registry Adapter
1. **Industry Context**:
   DPIP (Digital Payment Intelligence Platform / National Fraud Registry) is India's national fraud and cybercrime registry (integrated with I4C/MHA/RBI). Financial institutions query by VPA hash (SHA-256) for privacy-preserving registry lookup and submit confirmed mule rings.
2. **Architecture**:
   - Create `app/adapters/dpip.py` with class `DpipSmartRegistryAdapter`.
   - Backed by a thread-safe registry cache `_registry: Dict[str, Dict[str, Any]]` pre-populated with:
     - Hashes of all `DEFAULT_HONEYPOTS`
     - Hashes of known-bad test fixtures
     - Dynamic entries added via `update_registry()`
   - Models:
     ```python
     class DpipRegistryRecord(BaseModel):
         vpa_hash: str
         threat_level: str          # "CRITICAL", "HIGH", "MEDIUM", "LOW", "CLEAN"
         threat_score: float        # [0.0, 1.0], e.g. 0.90 for HIGH, 0.0 for CLEAN
         listed: bool
         record_id: Optional[str]   # e.g. "DPIP-REG-2026-9812"
         reporting_agencies: List[str] # ["I4C_PORTAL", "RBI_FRAUD_REGISTRY", "LEAS_FREEZE_NOTICE"]
         last_updated: str

     class DpipRegistryUpdateRequest(BaseModel):
         vpa_or_hash: str
         threat_level: str = "HIGH"
         threat_score: float = 0.90
         reason: str = "Analyst-confirmed mule account"
         agency: str = "SAMPATI_MESH"
     ```
3. **Deterministic VPA Mapping**:
   - Input normalization: Accepts either plain VPA (e.g. `honeypot_trap_01@okaxis`) or hex SHA-256 hash. If plain VPA is provided, automatically computes `vpa_hash = hashlib.sha256(vpa.strip().lower().encode()).hexdigest()`.
   - **Honeypots & Seeded Bad Hashes**:
     - `threat_level = "HIGH"`
     - `threat_score = 0.90` (non-zero float)
     - `listed = True`
     - `reporting_agencies = ["NATIONAL_CYBER_CRIME_PORTAL", "DPIP_HOTLIST"]`
   - **Known-Bad Keywords** in unhashed VPA:
     - `threat_level = "HIGH"`
     - `threat_score = 0.85` (non-zero float)
     - `listed = True`
     - `reporting_agencies = ["MULE_NETWORK_COORDINATION", "I4C"]`
   - **Clean VPAs**:
     - `threat_level = "CLEAN"`
     - `threat_score = 0.0` (zero)
     - `listed = False`
     - `reporting_agencies = []`
   - Query & Update API:
     - `query_vpa(vpa: str) -> DpipRegistryRecord`
     - `query_hash(vpa_hash: str) -> DpipRegistryRecord`
     - `update_registry(req: DpipRegistryUpdateRequest) -> DpipRegistryRecord`

### 2.3 Design of Adapter 3: Mock PSP Adapter (PhonePe, Paytm, Google Pay, etc.)
1. **Industry Context**:
   Major UPI PSPs (PhonePe, Paytm, Google Pay) execute local client-side and server-side risk checks (e.g. device velocity anomalies, sudden high-value transfer to unvetted beneficiaries). They broadcast standardized fraud signals into the collaborative mesh.
2. **Architecture**:
   - In `app/models/threat_intel.py`:
     ```python
     class StandardFraudSignal(ThreatSignalCreateRequest):
         """Standardized fraud signal format produced by PSP and institutional adapters."""
         pass
     ```
   - In `app/adapters/psp.py`, class `MockPspAdapter`:
     - Method `generate_signal(psp: str, vpa: str, anomaly_type: str = "velocity_anomaly", ...) -> StandardFraudSignal`:
       - Supported PSPs: `"PhonePe"`, `"Paytm"`, `"GooglePay"`, `"BHIM"`.
       - Supported anomaly types:
         1. `"velocity_anomaly"`: Rapid multi-beneficiary outbound burst.
         2. `"suspicious_beneficiary"`: Transfer to beneficiary flagged for social engineering.
         3. `"device_binding_churn"`: Multiple accounts bound to single hardware device.
       - Generates `StandardFraudSignal` with:
         - `source = f"psp_{psp.lower().replace(' ', '')}"` (e.g. `"psp_phonepe"`, `"psp_paytm"`)
         - `upi_id = vpa`
         - `severity = "HIGH" if is_bad else "MEDIUM"`
         - `confidence = 0.88`
         - `tags = [f"PSP:{psp}", anomaly_type.replace('_', ' ').title(), "Pre-transaction alert"]`
         - `raw_content = f"[{psp} Fraud Engine] Flagged {anomaly_type.replace('_', ' ')} for VPA {vpa}."`
     - Method `publish_to_mesh(signal: StandardFraudSignal) -> ThreatSignalResponse`:
       - Posts directly through `ThreatIntelService.ingest_signal()`, automatically updating the Central Fraud Graph and broadcasting via WebSocket.

### 2.4 Integration into Transaction Evaluation (`/upi/check`)
1. **Schema Enhancements** in `app/models/upi_models.py`:
   ```python
   class UpiEvaluationResponse(BaseModel):
       txn_id: str
       risk_score: int
       action: str
       reasons: List[str]
       rule_breakdown: List[RuleHit]
       rule_score: int
       adaptive_score: float
       network_score: float
       ml_anomaly_score: float
       supervised_fraud_score: float = Field(default=0.0, description="Supervised ML fraud probability score in [0.0, 1.0]")
       mock_npci_score: float = Field(default=0.0, description="Simulated NPCI MuleHunter mule-probability score in [0.0, 1.0]")
       mock_dpip_threat_level: Union[float, int, str] = Field(default=0.0, description="Simulated DPIP Smart Registry threat level score")
       contributing_signals: List[Dict[str, Any]] = Field(default_factory=list, description="Contributing institutional signal sources with institution labels")
       execution_latency_ms: float
       evaluated_at: datetime
       case_id: Optional[str]
       dmv_score: float
       campaign_id: Optional[str]
   ```
2. **Evaluation Logic** in `app/services/upi_cases.py` (`evaluate(txn)`):
   ```python
   # Invoke simulated institutional signal adapters
   adapters = get_institutional_adapters()
   inst_signals = adapters.evaluate_for_transaction(txn)
   
   resp.mock_npci_score = inst_signals["mock_npci_score"]
   resp.mock_dpip_threat_level = inst_signals["mock_dpip_threat_level"]
   resp.contributing_signals = inst_signals["contributing_signals"]
   ```
3. **Deterministic Guarantee for Known-Bad VPAs**:
   - For any transaction sent to a known-bad VPA (e.g. `honeypot_trap_01@okaxis` or any VPA matching `is_honeypot` or known-bad patterns):
     - `resp.mock_npci_score >= 0.85` (non-zero float, e.g. 0.96)
     - `resp.mock_dpip_threat_level >= 0.85` (non-zero float, e.g. 0.90)
     - `contributing_signals` contains entries for both `"NPCI"` and `"DPIP"`.
   - For a clean transaction (e.g. `payer@okaxis` to `merchant@okhdfcbank`):
     - `resp.mock_npci_score == 0.0` (or < 0.15)
     - `resp.mock_dpip_threat_level == 0.0` (zero)

### 2.5 REST API Router (`app/api/adapters.py`)
- Mount endpoints under `/adapters` and `/upi/adapters`:
  - `GET /adapters/npci/mulehunter?vpa={vpa}`: Returns `NpciMuleHunterResponse`.
  - `GET /adapters/dpip/registry?vpa={vpa}&vpa_hash={vpa_hash}`: Returns `DpipRegistryRecord`.
  - `POST /adapters/dpip/registry`: Updates registry record from `DpipRegistryUpdateRequest`.
  - `POST /adapters/psp/simulate`: Simulates and publishes a PSP signal.
  - `GET /adapters/signals/contributing?vpa={vpa}`: Returns contributing signals for a VPA.

### 2.6 Frontend Dashboard Integration
1. **`frontend/src/components/CaseDrawer.jsx`**:
   - Add an **"Institutional Contributing Signals"** section in the Forensic Dossier:
     - Render when `caseData.contributing_signals?.length > 0` or when `caseData.mock_npci_score > 0` or `caseData.mock_dpip_threat_level > 0`.
     - Visual Cards:
       - **NPCI MuleHunter**: Badge `[NPCI MuleHunter]`, Mule Probability gauge (e.g. `96%`), Risk rating tag (`HIGH` in red), switch velocity flags.
       - **DPIP Smart Registry**: Badge `[DPIP Smart Registry]`, National Fraud Registry Status (`LISTED - HIGH THREAT` in red/amber), threat level score `0.90`, reporting agencies (`I4C`, `RBI Registry`).
       - **PSP Local Signals**: Badge `[PhonePe]` or `[Paytm]`, with anomaly descriptor (`Velocity Anomaly`).
2. **`frontend/src/pages/ThreatIntelPage.jsx`**:
   - Style signal cards with distinctive institutional badges based on `signal.source`:
     - `psp_phonepe` / `phonepe` -> Purple badge `[PhonePe]`
     - `psp_paytm` / `paytm` -> Cyan/Blue badge `[Paytm]`
     - `npci_mulehunter` / `npci` -> Emerald badge `[NPCI]`
     - `dpip_registry` / `dpip` -> Indigo badge `[DPIP]`
   - Add institutional simulation presets in the simulation dropdown:
     - `[NPCI] High-Probability Mule Switch Alert`
     - `[DPIP] National Fraud Registry Hash Match`
     - `[PhonePe] Cross-PSP Velocity Burst Alert`
     - `[Paytm] Suspicious Beneficiary Pooling`
3. **`frontend/src/components/LiveFeed.jsx`**:
   - In the `Signals` column of the flagged activity table:
     - Display small pill tags for contributing institutions: `[NPCI]` or `[DPIP]` whenever `c.mock_npci_score > 0` or `c.mock_dpip_threat_level > 0`.
4. **`frontend/src/services/api.js`**:
   - Add client methods:
     - `queryNpciMuleHunter(vpa)`
     - `queryDpipRegistry({ vpa, vpa_hash })`
     - `updateDpipRegistry(payload)`
     - `simulatePspSignal({ psp, vpa, anomaly_type })`

---

## 3. Caveats

1. **Bytecode File `app/dpip/feed.pyc`**:
   `app/dpip/feed.pyc` is a compiled Python bytecode module loaded by `app/services/upi_cases.py`. Our new `DpipSmartRegistryAdapter` in `app/adapters/dpip.py` should import and coordinate with `get_dpip()` from `app.dpip.feed` while providing the explicit VPA-hash querying, deterministic threat levels, and REST endpoints requested in R2.
2. **Pydantic V1/V2 Compatibility**:
   The codebase supports dual Pydantic environments (`app/models/threat_intel.py` line 9 `from pydantic import BaseModel, Field, model_validator`). All new adapter models must use standard Pydantic field definitions with default values to ensure backward compatibility.
3. **Zero Latency Impact on Inline Scoring Gate**:
   All 3 adapters must operate purely in-memory with sub-millisecond execution (< 1ms) so the `/upi/check` inline scoring gate stays well below the 10ms benchmark requirement.

---

## 4. Conclusion

The simulated institutional signal adapters (Mock NPCI MuleHunter, Mock DPIP Smart Registry, Mock PSP) provide the missing federated mesh components needed to demonstrate SAMPATI V2 as a collaborative intelligence mesh.

### Concrete Implementation Blueprint:
1. **`app/models/threat_intel.py`**:
   - Add `StandardFraudSignal = ThreatSignalCreateRequest` alias and subclass with helper factory methods.
2. **`app/models/upi_models.py`**:
   - Add `mock_npci_score: float = 0.0`, `mock_dpip_threat_level: Union[float, int, str] = 0.0`, and `contributing_signals: List[Dict[str, Any]] = Field(default_factory=list)` to `UpiEvaluationResponse`.
3. **`app/adapters/` Package**:
   - `app/adapters/npci.py`: Implements `NpciMuleHunterAdapter` with deterministic mule probability (0.96 HIGH for honeypots/known-bad, hash-based low for clean).
   - `app/adapters/dpip.py`: Implements `DpipSmartRegistryAdapter` querying/updating national fraud registry by VPA hash (returns threat level HIGH / 0.90 for bad, CLEAN / 0.0 for clean).
   - `app/adapters/psp.py`: Implements `MockPspAdapter` producing `StandardFraudSignal` payloads for PhonePe, Paytm, etc., with publishing to the central mesh graph.
   - `app/adapters/service.py`: Singleton `InstitutionalAdapterService` combining the adapters.
4. **`app/services/upi_cases.py`**:
   - In `evaluate(txn)`, invoke `get_institutional_adapters().evaluate_for_transaction(txn)` and populate `resp.mock_npci_score`, `resp.mock_dpip_threat_level`, and `resp.contributing_signals`.
5. **`app/api/adapters.py` & `app/main.py`**:
   - Create FastAPI router exposing `/adapters/npci/mulehunter`, `/adapters/dpip/registry`, `/adapters/psp/simulate` and mount under `/adapters` and `/upi/adapters`.
6. **Frontend Integration**:
   - Update `CaseDrawer.jsx` to render an "Institutional Contributing Signals" card.
   - Update `ThreatIntelPage.jsx` with institution badges (`[NPCI]`, `[DPIP]`, `[PhonePe]`, `[Paytm]`) and institutional simulation presets.
   - Update `LiveFeed.jsx` with micro-pill badges in the Signals column.
   - Add adapter wrapper methods to `frontend/src/services/api.js`.

---

## 5. Verification Method

### 5.1 Automated Testing Commands
```bash
# 1. Run full existing pytest suite (verify zero regressions, 902+ tests)
./.venv/bin/pytest tests/ -v

# 2. Run new dedicated unit & contract test suite for R2 adapters
./.venv/bin/pytest tests/test_institutional_adapters.py -v

# 3. Verify Ruff Python linter
./.venv/bin/ruff check app tests

# 4. Verify Frontend ESLint and production build
cd frontend && npm run lint && npm run build && cd ..
```

### 5.2 Verification Scenarios & Expected Assertions
1. **Mock NPCI MuleHunter Unit Test**:
   - `adapter.score_account("honeypot_trap_01@okaxis")` -> `risk_rating == "HIGH"`, `mule_probability >= 0.85`
   - `adapter.score_account("clean_user@okhdfcbank")` -> `risk_rating == "LOW"`, `mule_probability < 0.20`
2. **Mock DPIP Smart Registry Unit Test**:
   - `adapter.query_vpa("honeypot_trap_01@okaxis")` -> `threat_level == "HIGH"`, `threat_score > 0`, `listed == True`
   - `adapter.query_hash(sha256("honeypot_trap_01@okaxis"))` -> returns same record
   - `adapter.update_registry(DpipRegistryUpdateRequest(vpa_or_hash="new_mule@ybl", threat_level="HIGH", threat_score=0.95))` -> updates registry
   - Subsequent `adapter.query_vpa("new_mule@ybl")` -> returns `threat_level == "HIGH"`, `threat_score == 0.95`
3. **Mock PSP Adapter Unit Test**:
   - `psp_adapter.generate_signal(psp="PhonePe", vpa="mule@okaxis", anomaly_type="velocity_anomaly")` -> returns `StandardFraudSignal` instance with `source == "psp_phonepe"`, tags including `["PSP:PhonePe", "Velocity Anomaly"]`.
4. **`/upi/check` E2E Contract Test**:
   - POST `/upi/check` with `payee_vpa = "honeypot_trap_01@okaxis"`:
     - `assert res.status_code == 200`
     - `data = res.json()`
     - `assert data["mock_npci_score"] > 0`
     - `assert data["mock_dpip_threat_level"] != 0`
     - `assert data["mock_dpip_threat_level"] > 0`
     - `assert len(data["contributing_signals"]) >= 2`
     - `assert any(s["institution"] == "NPCI" for s in data["contributing_signals"])`
     - `assert any(s["institution"] == "DPIP" for s in data["contributing_signals"])`
5. **Frontend Build & Lint Verification**:
   - `npm run lint` passes with 0 warnings (`--max-warnings 0`).
   - `npm run build` generates clean production assets in `frontend/dist/`.

### 5.3 Invalidation Conditions
- Any regression breaking the 902 passing tests in `tests/`.
- `mock_npci_score` or `mock_dpip_threat_level` returning `0.0` or missing from the `/upi/check` response when evaluated against a honeypot or known-bad VPA.
- Failure of frontend build due to missing imports or ESLint warnings.
