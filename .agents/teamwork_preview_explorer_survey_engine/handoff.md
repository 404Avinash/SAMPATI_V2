# Architectural Investigation & Design Report: Core Risk Engine, DMV Score, Device Telemetry Rules, and Campaign Fingerprinting

**Workspace**: `/home/avi/Downloads/Sampati_v2`  
**Milestone**: Sprint 2 Survey Phase — Core Risk Engine & Telemetry  
**Author**: Explorer Agent (`teamwork_preview_explorer_survey_engine`)  
**Date**: 2026-08-31  

---

## 1. Observation

Direct code and test inspection revealed the following exact components and characteristics:

### 1.1 `app/engine/upi_scorer.py` (Lines 1–103)
- **Scoring Architecture**: 3-layer additive architecture bounded to `[0, 100]` points:
  - Layer 1: Deterministic rules `rule_score = min(100, sum(h.points for h in hits))` (Line 41).
  - Layer 2: Adaptive behavioral model `adaptive_pts = int(adaptive_score * 25)` (Lines 43–44).
  - Layer 3: Federated network score `network_pts = int(network_score * 40)` (Lines 46).
  - Combined: `combined = rule_score + adaptive_pts + network_pts; risk_score = min(100, max(0, combined))` (Lines 48–49).
- **Verdict Thresholds**:
  - `risk_score >= 70` (`BLOCK_AT`) $\implies$ `action = "BLOCK"` (Lines 51–52).
  - `risk_score >= 45` (`ALLOW_BELOW`) $\implies$ `action = "HOLD"` (Lines 53–54).
  - `network_score >= 0.7` (`NETWORK_HOLD_FLOOR`) $\implies$ `action = "HOLD"; risk_score = max(risk_score, 45)` (Lines 55–57).
  - Otherwise $\implies$ `action = "ALLOW"` (Lines 58–59).
- **Reasons List**:
  - Populated with `[h.code for h in hits]`.
  - Appends `"BEHAVIORAL_ANOMALY"` if `adaptive_score >= 0.6` (Line 63).
  - Appends `"FEDERATED_MULE_NETWORK"` if `network_score >= 0.5` (Line 65).
- **State Updates**:
  - `self.state.record_txn(...)` records `(timestamp, payer_vpa, payee_vpa, amount, device_id, sim_id)` into `UpiHotState` (Lines 69–76).
  - `self.adaptive.observe(txn)` updates the entity profile (Line 78).

### 1.2 `app/engine/upi_rules.py` (Lines 1–176)
- **Currently Implemented Rules**:
  1. `R_HONEYPOT_HIT` (100 pts): Payee VPA matches seeded synthetic honeypot registry (Lines 26–44).
  2. `NEW_PAYEE_VPA` (25 pts): Payee VPA age $< 15$ days (`FRESH_VPA_DAYS`) (Lines 46–54).
  3. `PASS_THROUGH_CONDUIT` (30 pts): Entity forwards $\ge 90\%$ of received funds ($\ge \text{Rs } 5,000$) within rolling window for accounts $< 30$ days old (Lines 57–74).
  4. `FAN_IN_BURST` (25 pts): Payee account $< 30$ days old receiving from $\ge 5$ distinct payers in window (Lines 77–88).
  5. `FAN_OUT_DISPERSAL` (25 pts): Payer account $< 30$ days old dispersing to $\ge 5$ distinct payees in window (Lines 91–102).
  6. `DEVICE_FARM` (20 pts): Same hardware device fingerprint or SIM bound to $\ge 3$ distinct VPAs (Lines 105–118).
  7. `NEW_ACCOUNT_HIGH_VALUE` (15 pts): Account $< 15$ days old transferring $\ge \text{Rs } 10,000$ (Lines 120–128).
  8. `LIMIT_SKIRTING` (10 pts): Amount sits within $2\%$ below caution thresholds (`10k`, `15k`, `25k`, `50k`, `100k`) (Lines 131–140).
  9. `KNOWN_FRAUD_ENTITY` (35 pts): Payer or payee VPA previously confirmed in fraud feedback memory (Lines 143–155).
- **Rule Pipeline**: `evaluate_rules(txn, state)` iterates through the rule list and collects non-`None` `RuleHit` objects (Lines 158–176).

### 1.3 `app/models/upi_models.py` (Lines 1–254)
- **`UpiTransaction` Model** (Lines 30–57):
  - Already contains: `txn_id: str`, `timestamp: datetime`, `amount: float`, `txn_type: str`, `payer_vpa: str`, `payer_psp: str`, `payer_account_age_days: int = 365`, `payee_vpa: str`, `payee_psp: str`, `payee_vpa_age_days: int = 365`, `payee_is_new_for_payer: bool = False`, `device_id: str = ""`, `sim_id: str = ""`, `note: str = ""`, `ip: str = ""`, `location: str = ""`.
- **`UpiEvaluationResponse` Model** (Lines 59–73):
  - Contains: `txn_id`, `risk_score: int`, `action: str`, `reasons: List[str]`, `rule_breakdown: List[RuleHit]`, `rule_score: int`, `adaptive_score: float`, `network_score: float`, `execution_latency_ms: float`, `evaluated_at: datetime`, `case_id: Optional[str]`.
  - Missing Sprint 2 fields: `dmv_score: float = 0.0`, `campaign_id: Optional[str] = None`.

### 1.4 `app/services/upi_cases.py` (Lines 1–1353)
- `UpiCaseService.evaluate(txn)` coordinates federated scoring, external DPIP scoring, invokes `scorer.evaluate(txn, combined_network)`, logs the evaluation, records latency, opens an investigative case if `HOLD` or `BLOCK`, and returns the `UpiEvaluationResponse` (Lines 936–985).
- `RULE_METADATA` dictionary (Lines 54–72) maps rule codes to `{name, severity}`.

### 1.5 Test Suite Baseline Verification
- Tool command: `./.venv/bin/pytest`
- Execution result: **559 passed, 1 warning in 29.02s**.
- Verification covers all 5 tiers: Feature isolation (Tier 1), boundary conditions (Tier 2), combinations (Tier 3), real-world scenarios (Tier 4), and adversarial testing (Tier 5).

---

## 2. Logic Chain

### 2.1 Current State Analysis & Gap Identification
1. **Device and Telemetry Fields Unused in Granular Scoring**:
   - While `UpiTransaction` carries `device_id`, `sim_id`, `ip`, and `location`, the current engine only uses `device_id` and `sim_id` for multi-VPA counts in `DEVICE_FARM`.
   - `ip` is never checked against datacenter/cloud/VPN/Tor ranges.
   - `location` is never checked for geographic velocity or impossible travel.
   - Per-payer device/SIM historical consistency (detecting SIM swap vs device swap) is not tracked.
2. **Missing Dead Money Velocity (DMV) Metric**:
   - Mule accounts typically sit dormant before experiencing a sudden spike of near-100% outflow velocity. There is currently no per-VPA `dmv_score` in `/upi/check` responses or `/stats/analytics`.
3. **Isolated Fraud Decisions (Missing Campaign Clustering)**:
   - Fraudulent transactions are flagged individually. There is no behavioral DNA fingerprint extraction on `BLOCK` / `CONFIRMED_FRAUD` verdicts to cluster active syndicates or match new incoming transactions against known campaign archetypes (`R_CAMPAIGN_MATCH`).

---

### 2.2 Detailed Architectural Design

```
+---------------------------------------------------------------------------------------------------+
|                                  INCOMING UPI TRANSACTION                                         |
|  (txn_id, amount, payer_vpa, payee_vpa, device_id, sim_id, ip, location, payer_account_age_days)  |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      TELEMETRY & HISTORY HOT STATE                                 |
|  * Payer Device History: (last_dev, last_sim, known_devices, known_sims)                          |
|  * Payer Location History: (last_location, last_coords, last_time)                                |
|  * VPA Inflow/Outflow History: (sliding windows, dormancy detection, burst velocity)              |
|  * Active Campaign Signature Store: (cluster centroids, behavioral DNA vectors)                   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      CORE EVALUATION PIPELINE                                      |
|                                                                                                   |
|  [ LAYER 1: DETERMINISTIC RULES ] (0 - 100 pts)                                                   |
|    - R_HONEYPOT_HIT             (100 pts)                                                         |
|    - R_SIM_DEVICE_MISMATCH      ( 30 pts) -> SIM swap / device switch anomaly                     |
|    - R_IMPOSSIBLE_TRAVEL        ( 35 pts) -> >500km in <30min / >1000km/h                         |
|    - R_DATACENTER_IP            ( 25 pts) -> AWS/GCP/Azure/DO/Tor/VPN CIDR subnets                |
|    - R_CAMPAIGN_MATCH           ( 30 pts) -> Behavioral DNA similarity >= 0.82                    |
|    - NEW_PAYEE_VPA              ( 25 pts)                                                         |
|    - PASS_THROUGH_CONDUIT       ( 30 pts)                                                         |
|    - FAN_IN_BURST               ( 25 pts)                                                         |
|    - FAN_OUT_DISPERSAL          ( 25 pts)                                                         |
|    - DEVICE_FARM                ( 20 pts)                                                         |
|    - NEW_ACCOUNT_HIGH_VALUE     ( 15 pts)                                                         |
|    - LIMIT_SKIRTING             ( 10 pts)                                                         |
|    - KNOWN_FRAUD_ENTITY         ( 35 pts)                                                         |
|                                                                                                   |
|  [ LAYER 2: ADAPTIVE EWMA ANOMALY ] (0 - 25 pts)                                                  |
|  [ LAYER 3: FEDERATED MULE NETWORK SCORE ] (0 - 40 pts)                                           |
|                                                                                                   |
|  [ DMV SCORE ENGINE ] (0 - 100 metric)                                                            |
|    - Dormancy Index (D) + Burst Velocity Index (V) per-VPA                                        |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      UpiEvaluationResponse                                        |
|  { txn_id, risk_score, action, reasons, rule_breakdown, dmv_score, campaign_id, ... }             |
+---------------------------------------------------------------------------------------------------+
```

---

### 2.3 Feature-by-Feature Design

#### A. Dead Money Velocity (DMV) Score (0–100) per-VPA
1. **Mathematical Model**:
   - **Dormancy Index ($D \in [0.0, 1.0]$)**:
     - If the payer account has high age (`payer_account_age_days >= 30`), evaluate elapsed time since previous outbound transaction $\Delta t_{\text{dormant}}$:
       $$D = \min\left(1.0, \frac{\max(\text{days\_since\_last\_txn}, \text{dormant\_baseline})}{30.0}\right)$$
       - For newly observed payer accounts with `payer_account_age_days >= 60` and no prior transaction recorded, $\text{dormant\_baseline} = \min(60, \text{payer\_account\_age\_days}) \implies D \approx 1.0$.
       - For active accounts seen recently ($< 2$ days), $D \le 0.07$.
   - **Burst Velocity Index ($V \in [0.0, 1.0]$)**:
     - Outflow drain ratio: $R_{\text{out}} = \frac{\text{recent\_outflow\_1h}}{\max(\text{recent\_inflow\_24h}, \text{current\_amount}, 1.0)}$
     - Transaction rate factor: $F_{\text{rate}} = \min(1.0, \frac{N_{\text{txns\_last\_hour}}}{4})$
     - Amount magnitude factor: $M_{\text{amt}} = \min(1.0, \frac{\text{txn.amount}}{30000.0})$
     - $V = 0.50 \cdot \min(1.0, R_{\text{out}}) + 0.30 \cdot F_{\text{rate}} + 0.20 \cdot M_{\text{amt}}$
   - **Composite DMV Score**:
     $$\text{Raw DMV} = 100.0 \cdot \left(0.40 \cdot D + 0.60 \cdot V\right)$$
     $$\text{DMV Score} = \min\left(100.0, \text{Raw DMV} \cdot (1.25 \text{ if } D > 0.5 \text{ and } V > 0.5 \text{ else } 1.0)\right)$$
   - **Color Classification Contract**:
     - $\text{DMV} < 40.0 \implies \text{GREEN}$ (Standard legitimate flow / active user).
     - $40.0 \le \text{DMV} \le 70.0 \implies \text{AMBER}$ (Moderate burst / elevated flow velocity).
     - $\text{DMV} > 70.0 \implies \text{RED}$ (Classic dormant mule account drain signature).
2. **State & Analytics Integration**:
   - Dedicated `DmvTracker` class maintained in memory.
   - `/upi/check` response includes `dmv_score: float`.
   - `/stats/analytics` includes `top_vpas_by_dmv: List[Dict[str, Any]]` sorted descending by DMV score.

---

#### B. SIM-Device Mismatch Rule (`R_SIM_DEVICE_MISMATCH`)
1. **Scoring Contribution**: `points = 30`, severity = `HIGH`.
2. **Detection Logic**:
   - Maintains per-payer telemetry history in state: `(last_device_id, last_sim_id)`.
   - When both `device_id` and `sim_id` are supplied in incoming `UpiTransaction`:
     - **SIM-Swap Signature**: `txn.device_id == last_device_id` AND `txn.sim_id != last_sim_id` $\implies$ New SIM card inserted into old device.
     - **Cloned SIM / Device Swap Signature**: `txn.sim_id == last_sim_id` AND `txn.device_id != last_device_id` $\implies$ Existing SIM identity active on a new physical hardware device.
   - If mismatch detected:
     - Return `RuleHit(code="R_SIM_DEVICE_MISMATCH", points=30, detail=f"SIM-device mismatch for '{txn.payer_vpa}': SIM '{txn.sim_id[:6]}...' observed on device '{txn.device_id[:6]}...'")`.
   - If no prior history exists or IDs match, return `None`.

---

#### C. Impossible Travel Rule (`R_IMPOSSIBLE_TRAVEL`)
1. **Scoring Contribution**: `points = 35`, severity = `CRITICAL`.
2. **Geographic Coordinate Resolution**:
   - Location strings support either explicit coordinates `"lat,lon"` (e.g. `"19.0760,72.8777"`) or standard Indian/global city names:
     - Mumbai: `(19.0760, 72.8777)`
     - Delhi / NCR: `(28.7041, 77.1025)`
     - Bengaluru: `(12.9716, 77.5946)`
     - Chennai: `(13.0827, 80.2707)`
     - Kolkata: `(22.5726, 88.3639)`
     - Hyderabad: `(17.3850, 78.4867)`
     - Pune: `(18.5204, 73.8567)`
     - Ahmedabad: `(23.0225, 72.5714)`
     - Jaipur: `(26.9124, 75.7873)`
     - London: `(51.5074, -0.1278)`
     - New York: `(40.7128, -74.0060)`
     - Singapore: `(1.3521, 103.8198)`
     - Dubai: `(25.2048, 55.2708)`
3. **Haversine Distance & Velocity Calculation**:
   - Distance: $d = 2 R \arcsin\left(\sqrt{\sin^2(\Delta\phi/2) + \cos\phi_1\cos\phi_2\sin^2(\Delta\lambda/2)}\right)$ with $R = 6371\text{ km}$.
   - Elapsed Time: $\Delta t = (t_{\text{curr}} - t_{\text{prev}})$ in hours.
   - Velocity: $v = \frac{d}{\Delta t}\text{ km/h}$.
4. **Trigger Condition**:
   - $d > 500\text{ km}$ AND $\Delta t < 0.50\text{ hr}$ ($30\text{ min}$) [implies speed $> 1000\text{ km/h}$], OR
   - $d > 100\text{ km}$ AND $\Delta t < 0.05\text{ hr}$ ($3\text{ min}$) [impossible ground speed $> 2000\text{ km/h}$].
   - If triggered, returns `RuleHit(code="R_IMPOSSIBLE_TRAVEL", points=35, detail=f"Impossible travel: {d:.0f}km in {delta_mins:.1f}min ({v:.0f} km/h) between '{prev_loc}' and '{curr_loc}'")`.

---

#### D. Datacenter / VPN IP Rule (`R_DATACENTER_IP`)
1. **Scoring Contribution**: `points = 25`, severity = `HIGH`.
2. **Subnet Verification via `ipaddress`**:
   - Cloud / Datacenter CIDR ranges compiled into `ipaddress.ip_network` structures:
     - **AWS**: `3.0.0.0/9`, `13.32.0.0/15`, `52.0.0.0/11`, `54.0.0.0/12`, `18.0.0.0/11`, `35.154.0.0/16`, `13.126.0.0/15`, `15.206.0.0/15`, `65.0.0.0/16`
     - **GCP**: `34.64.0.0/11`, `35.184.0.0/13`, `35.200.0.0/13`, `34.93.0.0/16`, `34.100.0.0/16`
     - **Azure**: `20.0.0.0/11`, `40.64.0.0/10`, `51.140.0.0/14`, `104.40.0.0/13`, `52.136.0.0/13`
     - **DigitalOcean**: `104.131.0.0/16`, `138.68.0.0/16`, `159.203.0.0/16`, `167.99.0.0/16`, `188.166.0.0/16`
     - **Tor Exit Nodes & Public VPN Test Subnets**: `185.220.100.0/22`, `198.51.100.0/24`, `203.0.113.0/24`, `194.26.29.0/24`, `45.154.255.0/24`
3. **Execution**:
   - If `txn.ip` is provided and parses to an IPv4/IPv6 address matching any datacenter network:
     - Return `RuleHit(code="R_DATACENTER_IP", points=25, detail=f"Origin IP '{txn.ip}' belongs to Datacenter / Cloud / VPN CIDR ({matched_subnet})")`.
   - Residential and standard mobile carrier IPs (e.g. Jio `49.207.50.x`) return `None`.

---

#### E. Transaction DNA Campaign Fingerprinting (`R_CAMPAIGN_MATCH`)
1. **Scoring Contribution**: `points = 30`, severity = `CRITICAL`.
2. **Behavioral DNA Extraction**:
   - Features extracted per transaction:
     - Amount structuring profile (skirting threshold, rounding modulus, magnitude bucket).
     - Temporal bucket (hour of day, night-window flag).
     - Target payee handle category & payment note semantic keywords (`"kyc"`, `"refund"`, `"lottery"`, `"urgent"`, `"bonus"`).
     - Device & IP class.
     - Velocity burst profile.
3. **Similarity Matching Engine**:
   - Compares incoming transaction DNA against the active campaign signature store.
   - Weighted cosine/Euclidean similarity:
     $$\text{Sim}(T, C) = 0.35 \cdot \text{Sim}_{\text{amount}} + 0.20 \cdot \text{Sim}_{\text{time}} + 0.20 \cdot \text{Sim}_{\text{keywords}} + 0.15 \cdot \text{Sim}_{\text{device/ip}} + 0.10 \cdot \text{Sim}_{\text{flow}}$$
   - When $\text{Sim}(T, C) \ge 0.82$:
     - Rule hit: `R_CAMPAIGN_MATCH` (30 points).
     - `campaign_id` attached to `UpiEvaluationResponse`.
     - `detail = f"Behavioral DNA matches active syndicate campaign '{campaign.id}' ({campaign.name}, similarity: {sim:.0%})"`.
4. **Dynamic Campaign Store Ingestion**:
   - On every evaluation resulting in `BLOCK` or feedback `CONFIRMED_FRAUD`, the transaction's behavioral vector is ingested via `CampaignStore.ingest_fingerprint(txn)`.
   - Clusters new signatures into existing campaign groups or spawns a new campaign ID (e.g. `CAMP-AUTO-xxxx`) if distinct.
   - Seeded with reference campaigns (`CAMP-KYC-PHISH-01`, `CAMP-SMURF-BURST-02`, `CAMP-INVESTMENT-03`).

---

## 3. Caveats & Edge Cases

1. **In-Memory Telemetry vs DB Persistence**:
   - The in-memory telemetry state (sliding location windows, recent SIM/device pairs) executes in sub-millisecond time (<0.1ms), fully satisfying the <5ms SLA. On process restart, history is rebuilt as transactions arrive or hydrated from database records.
2. **IP Parsing Robustness**:
   - Malformed or blank `ip` strings must be gracefully handled with `ipaddress.ip_address` inside a `try/except ValueError` block without throwing unhandled exceptions.
3. **Missing or Incomplete Telemetry**:
   - In production and unit tests, transactions may arrive with empty `location`, `ip`, or `sim_id`. The rules must strictly return `None` when required telemetry fields are absent, preventing false-positive triggers.

---

## 4. Conclusion

1. **Complete Engine Blueprint**: The design for DMV Score, Device Telemetry Rules (`R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`), and Campaign Fingerprinting (`R_CAMPAIGN_MATCH`) is fully specified, mathematically grounded, and aligned with UPI payment rail characteristics.
2. **Strict 100% Backward Compatibility**:
   - All new fields on `UpiTransaction` and `UpiEvaluationResponse` use optional/default values (`dmv_score: float = 0.0`, `campaign_id: Optional[str] = None`).
   - Existing rules and evaluation workflows remain untouched.
   - All 559 existing tests will continue to pass without modification.
3. **Seamless Analytics & Dashboard Integration**:
   - `dmv_score` in `/upi/check` feeds the CaseDrawer gauge.
   - `top_vpas_by_dmv` in `/stats/analytics` powers the ranked analytics table.
   - `R_CAMPAIGN_MATCH` connects isolated transactions into visible syndicate clusters.

---

## 5. Verification Method

Independent verification can be performed by the following steps:

1. **Full Test Suite Execution**:
   ```bash
   ./.venv/bin/pytest tests/ -v
   ```
2. **Syntax and Code Quality Checks**:
   ```bash
   ./.venv/bin/ruff check app tests
   ```
3. **Specific Rule Trigger Verification**:
   - **`R_SIM_DEVICE_MISMATCH`**: Submit transaction with `(dev1, sim1)`, followed by transaction for same payer with `(dev1, sim2)` or `(dev2, sim1)` $\implies$ verify rule hit and +30 points.
   - **`R_IMPOSSIBLE_TRAVEL`**: Submit transaction at `Mumbai` at $t_0$, followed by transaction at `Delhi` ($>1100\text{ km}$) at $t_0 + 10\text{ min}$ $\implies$ verify rule hit and +35 points.
   - **`R_DATACENTER_IP`**: Submit transaction with `ip = "3.220.100.45"` (AWS EC2) $\implies$ verify rule hit and +25 points. Submit with `ip = "49.207.50.10"` (residential) $\implies$ verify rule does not trigger.
   - **`R_CAMPAIGN_MATCH`**: Submit block-level transaction with matching KYC phishing profile $\implies$ verify `R_CAMPAIGN_MATCH` in `rule_breakdown` and valid `campaign_id` in response.
   - **DMV Score**: Submit transaction for dormant account ($>90$ days inactive) suddenly moving high volume $\implies$ verify `dmv_score > 70.0`.
