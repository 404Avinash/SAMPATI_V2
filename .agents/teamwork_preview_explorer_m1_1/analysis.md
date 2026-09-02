# SAMPATI V2 Encyclopedia Knowledge Base: Mathematical Formulas, Algorithmic Definitions, and Detection Rationales

## Executive Summary
This document provides an exhaustive mathematical dictionary, algorithmic specification, and plain-English explanation template library extracted from `ENCYCLOPEDIA.md` and verified against the SAMPATI V2 core codebase. It serves as the definitive reference for implementing the Knowledge Base layer (`app/engine/encyclopedia_kb.py`) and deep context injection for the Gemini Assistant.

---

## 1. Knowledge Base Architecture & Interfaces

### 1.1 Role in Gemini Assistant
The Knowledge Base layer indexes mathematical formulas, deterministic rules, statistical anomaly bounds, and plain-English detection rationales. When a case is inspected or queried via `/cases/{case_id}/ai-briefing` or `/cases/{case_id}/ai-chat`, the knowledge base translates raw evaluated rule hits and mathematical metrics into transparent, legally defensible, plain-English explanations.

### 1.2 Target Interface Contracts (`app/engine/encyclopedia_kb.py`)
```python
def get_rule_explanation(rule_code: str, metric_value: float = None, context: dict = None) -> dict:
    """Returns {
        "rule_code": str,
        "name": str,
        "mathematical_definition": str,
        "anomaly_threshold": str,
        "plain_english_explanation": str
    }"""

def build_case_encyclopedia_context(evaluated_rules: list[dict], metrics: dict = None) -> str:
    """Returns formatted markdown string explaining all fired and evaluated rules for prompt injection."""
```

---

## 2. Mathematical Formula Dictionary & Algorithmic Definitions

### 2.1 Dead Money Velocity (DMV) Engine
**Source Reference:** `app/engine/dmv.py`, `ENCYCLOPEDIA.md` Section 7, 21, 22
**Purpose:** Detects the signature pattern of a mule account — prolonged dormancy (weeks/months) followed by an explosive, near-complete balance dissipation in a narrow time window.

#### Mathematical Formulation

$$\text{DMV Score} \in [0.0, 100.0]$$

1. **Dormancy Index ($D \in [0.0, 1.0]$):**
   - If previous outbound transaction timestamp $t_{prev}$ exists:
     $$\Delta t_{days} = \max\left(0, \frac{t_{now} - t_{prev}}{86400}\right)$$
     $$D = \min\left(1.0, \frac{\Delta t_{days}}{30.0}\right)$$
   - If first observed outbound transaction (using account age $A_{days}$):
     $$D = \begin{cases} \min\left(1.0, \frac{\min(90.0, A_{days})}{30.0}\right) & \text{if } A_{days} \ge 30 \\ \max\left(0.0, \frac{A_{days}}{30.0} \times 0.2\right) & \text{if } A_{days} < 30 \end{cases}$$

2. **Burst Velocity Index ($V \in [0.0, 1.0]$):**
   - Let $O_{1h}$ be total outflow in 1-hour window, $I_{24h}$ be total inflow in 24-hour window, $N_{1h}$ be transaction count in 1-hour window, and $A$ be current transaction amount.
   - **Current Outflow:** $O_{curr} = O_{1h} + A$
   - **Available Inflow Baseline:** $I_{avail} = \max(I_{24h}, A, 1.0)$
   - **Balance Depletion Ratio ($R_{drain}$):**
     $$R_{drain} = \min\left(1.0, \frac{O_{curr}}{I_{avail}}\right)$$
   - **Transaction Rate Factor ($R_{rate}$):**
     $$R_{rate} = \min\left(1.0, \frac{N_{1h} + 1}{4.0}\right)$$
   - **Amount Scale Factor ($A_{factor}$):**
     $$A_{factor} = \min\left(1.0, \frac{A}{30000.0}\right)$$
   - **Composite Burst Velocity ($V$):**
     $$V = 0.50 \cdot R_{drain} + 0.30 \cdot R_{rate} + 0.20 \cdot A_{factor}$$
     $$V = \min(1.0, \max(0.0, V))$$

3. **Composite Raw DMV Score:**
   $$\text{Raw DMV} = 100.0 \times (0.40 \cdot D + 0.60 \cdot V)$$

4. **Synergistic Escalation Multiplier:**
   - If $D \ge 0.5$ and $V \ge 0.4$:
     $$\text{Multiplier} = 1.0 + 0.5 \cdot (D \times V)$$
     $$\text{Final DMV Score} = \min(100.0, \text{Raw DMV} \times \text{Multiplier})$$
   - Else:
     $$\text{Final DMV Score} = \text{Raw DMV}$$

#### Data Structure & Complexity
- Utilizes thread-safe sliding double-ended queues (`collections.deque`) per VPA tracking `(timestamp, amount, is_outflow)`.
- Eviction window: 720 hours (30 days) with $O(1)$ amortized append and popleft operations.

#### Gauge Color Tiers
| Tier | Score Range | Indication | Analyst Interpretation |
|---|---|---|---|
| **GREEN** | $0.0 \le \text{Score} < 40.0$ | Normal Velocity | Established spending pattern; active transaction cadence. |
| **AMBER** | $40.0 \le \text{Score} \le 70.0$ | Elevated Velocity | Moderate dormancy or accelerating outflow; heightened monitoring. |
| **RED** | $\text{Score} > 70.0$ | Critical Mule Signature | Severe dormancy wake-up with rapid balance liquidation; immediate freeze candidate. |

---

### 2.2 Adaptive EWMA Behavioral Anomaly Model (Layer 2)
**Source Reference:** `app/engine/adaptive.py`, `ENCYCLOPEDIA.md` Section 7, 21, 22
**Purpose:** Real-time, streaming statistical anomaly detection maintaining personalized rolling baselines for each VPA without database latency or batch re-training.

#### Mathematical Formulation

1. **Online Streaming Update Equations ($\alpha = 0.25$):**
   - **Running Mean:**
     $$\mu_t = \alpha \cdot x_t + (1 - \alpha) \cdot \mu_{t-1} = \mu_{t-1} + \alpha \cdot (x_t - \mu_{t-1})$$
   - **Running Variance (Welford-style EWMA):**
     $$\sigma^2_t = (1 - \alpha) \cdot \sigma^2_{t-1} + \alpha \cdot (x_t - \mu_{t-1})^2$$
   - **Inter-arrival Gap Mean:**
     $$\Delta t = \max(0.0, t_{now} - t_{last})$$
     $$\mu_{gap, t} = \alpha \cdot \Delta t + (1 - \alpha) \cdot \mu_{gap, t-1}$$
   - **New Payee Indicator EWMA:**
     $$I_{new} = \begin{cases} 1.0 & \text{if payee is new for payer} \\ 0.0 & \text{otherwise} \end{cases}$$
     $$\mu_{new\_payee, t} = \alpha \cdot I_{new} + (1 - \alpha) \cdot \mu_{new\_payee, t-1}$$

2. **Multi-Component Statistical Anomaly Scoring:**
   - **Amount Z-Score Normalization:**
     $$\sigma_{amt} = \sqrt{\max(\sigma^2_t, 10^{-9})}$$
     $$\text{Denominator} = \max(\sigma_{amt}, 0.15 \cdot \mu_t, 1.0)$$
     $$Z_{amt} = \frac{|x_t - \mu_t|}{\text{Denominator}}$$
     $$C_{amt} = \tanh\left(\frac{Z_{amt}}{3.0}\right)$$
   - **Transaction Speedup Component:**
     $$\text{Speedup } S = \frac{\mu_{gap}}{\max(\Delta t, 1.0)}$$
     $$C_{gap} = \tanh\left(\frac{\max(0.0, S - 1.0)}{20.0}\right)$$
   - **New Payee Component:**
     $$C_{payee} = \min(1.0, 0.5 - 0.2 \cdot \mu_{new\_payee})$$
   - **Composite Raw Anomaly:**
     $$\text{Raw Anomaly} = \frac{\sum C_k}{\max(K, 1)}$$
     $$\text{Adaptive Score} = \min\left(1.0, \max\left(0.0, \text{Raw Anomaly} \times \text{Sensitivity} + \text{Suspicion}\right)\right)$$

3. **Contribution to 3-Layer Composite Score:**
   $$\text{Adaptive Points} = \lfloor \text{Adaptive Score} \times 25 \rfloor \quad (\text{Max } 25 \text{ pts})$$
   - If $\text{Adaptive Score} \ge 0.60 \implies$ triggers `BEHAVIORAL_ANOMALY` reason tag.

4. **Analyst Feedback Adaptation:**
   - **Confirmed Fraud:**
     $$\text{Suspicion} \leftarrow \min(0.50, \text{Suspicion} + 0.25)$$
     $$\text{Sensitivity} \leftarrow \min(1.50, \text{Sensitivity} + 0.02)$$
   - **False Positive (Dismissed):**
     $$\text{Suspicion} \leftarrow \max(0.0, \text{Suspicion} - 0.15)$$
     $$\text{Sensitivity} \leftarrow \max(0.70, \text{Sensitivity} - 0.02)$$

---

### 2.3 Structuring / Smurfing Detection
**Source Reference:** `app/engine/upi_rules.py`, `app/engine/campaign.py`, `ENCYCLOPEDIA.md` Section 7, 21
**Purpose:** Detects deliberate splitting of high-value funds into smaller micro-transfers to evade regulatory monitoring limits.

#### Mathematical Formulation & Detection Gates

1. **Threshold Limit Skirting (`LIMIT_SKIRTING` - 10 pts):**
   - Monitored Regulatory Caution Thresholds:
     $$\mathcal{T} = \{₹10,000,\ ₹15,000,\ ₹25,000,\ ₹50,000,\ ₹100,000\}$$
   - Trigger Condition: Amount $A$ falls strictly within the upper 2% margin below any threshold $T \in \mathcal{T}$:
     $$0.98 \times T \le A < T$$
   - Example triggers: ₹9,850 – ₹9,999; ₹24,500 – ₹24,999; ₹49,000 – ₹49,999; ₹98,000 – ₹99,999.

2. **Micro-Smurfing Dispersal Signature (`CAMP-SMURF-BURST-02`):**
   - Amount Range: $₹2,000 \le A \le ₹24,999$
   - Pattern: High-frequency fan-out outbound transfers from collector nodes to mule endpoints.
   - Structuring Proximity Booster: If $|A - T| \le ₹50$ for any $T \in \mathcal{T}$, amount similarity is boosted to $\ge 0.90$.

---

### 2.4 Pass-Through Conduits & Mule Rings
**Source Reference:** `app/engine/upi_rules.py`, `app/federation/coordinator.py`, `ENCYCLOPEDIA.md` Section 7, 8
**Purpose:** Identifies transit accounts that hold funds for minimal duration, immediately forwarding them to the next layer in the laundering chain.

#### Mathematical Formulation & Rules

1. **Pass-Through Conduit (`PASS_THROUGH_CONDUIT` - 30 pts):**
   - Account Age constraint: $A_{payer} < 30 \text{ days}$
   - Inflow threshold: Total received in window $I_{win} \ge ₹5,000$
   - Outflow ratio:
     $$\text{Outflow Ratio} = \frac{O_{prev} + A}{I_{win}} \ge 0.90 \quad (90\%)$$
   - Substantial Transfer condition:
     $$A \ge 0.50 \cdot I_{win} \quad (50\% \text{ of window inflow})$$

2. **Rapid Fan-In Burst (`FAN_IN_BURST` - 25 pts):**
   - Payee Account Age: $A_{payee} < 30 \text{ days}$
   - Unique Counterparties:
     $$N_{distinct\_payers} + 1 \ge 5$$

3. **Rapid Fan-Out Dispersal (`FAN_OUT_DISPERSAL` - 25 pts):**
   - Payer Account Age: $A_{payer} < 30 \text{ days}$
   - Unique Counterparties:
     $$N_{distinct\_payees} + 1 \ge 5$$

4. **Multi-PSP Federation Consensus & Ring Promotion:**
   - Node Suspicion Feature Score:
     $$S_{node} = \begin{cases} +0.45 & \text{if } I_{tot} > 1000 \text{ and } 0.85 \le \frac{O_{tot}}{I_{tot}} \le 1.15 \\ +0.25 & \text{if fresh account} \\ +0.20 & \text{if } N_{distinct\_in} \ge 4 \\ +0.20 & \text{if } N_{distinct\_out} \ge 4 \\ +0.15 & \text{if device is shared} \end{cases}$$
   - Seed Nodes: $S_{node} \ge 0.50$; Growable Neighbors: $S_{node} \ge 0.20$
   - Ring Promotion Criteria:
     $$\text{Component Size} \ge 3 \quad \text{AND} \quad \text{Distinct PSPs} \ge 2$$
   - Network Boost to Member Nodes:
     $$\text{Network Risk Score} = \min(1.0, 0.70 + 0.05 \times \text{Size})$$

---

### 2.5 Graph ML Node Role Classification
**Source Reference:** `app/services/upi_cases.py`, `ENCYCLOPEDIA.md` Section 7, 21, 22
**Purpose:** Graph-theoretic structural decomposition of detected mule rings using directed graph topology $G = (V, E)$.

#### Structural Role Taxonomy & Identification Matrix

```
[Victim / Source] ──► [Collector Hub] ──► [Layering Hop / Conduit] ──► [Cash-Out / Sink]
```

| Structural Role | Graph In/Out Degree Criteria | Flow Dynamics & Centrality | Real-World Operational Meaning |
|---|---|---|---|
| **Source / Victim** | $\text{In-Degree} = 0$, $\text{Out-Degree} \ge 1$ | High net outflow, zero prior fraud memory, established account age ($>90$d) | Innocent account compromised or targeted by phishing/social engineering. |
| **Collector Hub** | $\text{In-Degree} \ge 4$, $\text{Out-Degree} \le 1$ | Rapid fan-in aggregation; high degree centrality; short retention duration | First-line aggregation node receiving small stolen tranches from multiple victims. |
| **Layering Hop / Conduit** | $\text{In-Degree} \ge 1$, $\text{Out-Degree} \ge 1$ | Balanced flow: $0.85 \le \frac{\text{Outflow}}{\text{Inflow}} \le 1.15$; High betweenness centrality | Obscuration relay node transferring funds across PSP boundaries to break audit trails. |
| **Cash-Out / Sink** | $\text{In-Degree} \ge 1$, $\text{Out-Degree} = 0$ | Terminal node in DAG; high terminal inflow; funds exit via ATM/crypto/P2P cash | Final liquidation endpoint where laundered funds exit the digital payment rail. |

---

### 2.6 Honeypot Decoys & Synthetic Traps
**Source Reference:** `app/engine/honeypot.py`, `app/engine/upi_rules.py`, `ENCYCLOPEDIA.md` Section 9, 21
**Purpose:** Zero-false-positive deterministic trapping of automated crawlers, botnets, and organized syndicates probing synthetic accounts.

#### Seeded Traps & Prefix Signatures
- **Pre-Seeded VPAs (14 addresses):** `honeypot_trap_01@okaxis`, `honeypot_mule_99@okhdfcbank`, `phish_trap_node@okicici`, `botnet_sink_04@oksbi`, `mule_honeypot_prime@okaxis`, `trap_collect_007@paytm`, `phish_sink_alpha@ibl`, `mule_decoy_99@ybl`, `honeypot_mule_88@okhdfcbank`, `decoy_phish_trap@oksbi`, `honeypot.sink@upi`, `trap_synthetic@upi`, `darkweb_mule_sink@okaxis`, `honeypot_phish_victim@ybl`.
- **Prefix Matching:** `honeypot_`, `honeypot.`, `phish_trap_`, `botnet_sink_`, `mule_honeypot_`, `trap_sink_`, `decoy_mule_`, `trap_synthetic`, `trap_collect`, `decoy_phish`.

#### Operational Trigger & Side Effects
1. Rule `R_HONEYPOT_HIT` fires with **100 points** $\implies$ Final Risk Score $= 100$, Verdict $=$ **BLOCK**.
2. Records hit timestamp, transaction ID, payer VPA, and cumulative amount deflected.
3. Broadcasts real-time `HONEYPOT_ALERT` event over WebSocket to frontend dashboard.

---

### 2.7 Campaign DNA Similarity Matching
**Source Reference:** `app/engine/campaign.py`, `ENCYCLOPEDIA.md` Section 7, 21, 22
**Purpose:** Fuzzy similarity clustering to match incoming transactions against known or emerging organized crime syndicate signatures.

#### Multi-Vector Similarity Formulation

$$\text{Similarity Score } S \in [0.0, 1.0]$$

$$S = 0.35 \cdot S_{kw} + 0.30 \cdot S_{amt} + 0.15 \cdot S_{hour} + 0.20 \cdot S_{vpa}$$

1. **Keyword Overlap ($S_{kw}$, weight 0.35):**
   - Let $\mathcal{W}_{note}$ be tokenized word set from transaction note and $\mathcal{K}_{camp}$ be campaign keywords:
     $$S_{kw} = \min\left(1.0, \frac{|\mathcal{W}_{note} \cap \mathcal{K}_{camp}|}{1.0}\right)$$
   - If payee VPA handle contains any keyword $k \in \mathcal{K}_{camp} \implies S_{kw} \leftarrow \max(S_{kw}, 0.85)$.

2. **Amount Distribution ($S_{amt}$, weight 0.30):**
   - If $A_{min} \le A \le A_{max} \implies S_{amt} = 1.0$
   - If $A < A_{min} \implies S_{amt} = \max\left(0.0, 1.0 - \frac{A_{min} - A}{\max(1.0, A_{min})}\right)$
   - If $A > A_{max} \implies S_{amt} = \max\left(0.0, 1.0 - \frac{A - A_{max}}{\max(1.0, A_{max})}\right)$
   - Structuring Pattern Boost: If $|A - T| \le ₹50$ for $T \in \{10k, 15k, 25k, 50k, 100k\} \implies S_{amt} \leftarrow \max(S_{amt}, 0.90)$.

3. **Temporal Bucket ($S_{hour}$, weight 0.15):**
   $$S_{hour} = \begin{cases} 1.0 & \text{if } \text{Hour} \in \mathcal{H}_{camp} \text{ or } \mathcal{H}_{camp} \text{ is empty} \\ 0.40 & \text{otherwise} \end{cases}$$

4. **Entity VPA Overlap ($S_{vpa}$, weight 0.20):**
   $$S_{vpa} = \begin{cases} 1.0 & \text{if } \text{Payer VPA or Payee VPA} \in \mathcal{V}_{members} \\ 0.0 & \text{otherwise} \end{cases}$$

5. **Synergy Boosts & Thresholds:**
   - If $S_{kw} \ge 0.85$ and $S_{amt} \ge 0.70 \implies S \leftarrow \max(S, 0.85)$
   - If $S_{vpa} \ge 0.90 \implies S \leftarrow \max(S, 0.90)$
   - **Detection Gate:** If $S \ge 0.82 \implies$ Rule `R_CAMPAIGN_MATCH` fires (+30 pts).
   - **Dynamic Ingestion:** On BLOCK, if $S \ge 0.70 \implies$ merges into existing campaign; if $S < 0.70 \implies$ spawns new `CAMP-AUTO-xxxx`.

---

### 2.8 Impossible Travel & Device Telemetry Anomalies
**Source Reference:** `app/engine/upi_rules.py`, `ENCYCLOPEDIA.md` Section 7, 21
**Purpose:** Detects geographic velocity violations, account takeovers, SIM-swap attacks, and proxy/cloud IP routing.

#### Mathematical Formulations

1. **Great-Circle Haversine Distance ($d$ in km, Earth Radius $R = 6,371 \text{ km}$):**
   $$\Delta \phi = \text{radians}(\text{lat}_2 - \text{lat}_1), \quad \Delta \lambda = \text{radians}(\text{lon}_2 - \text{lon}_1)$$
   $$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\text{radians}(\text{lat}_1)) \cdot \cos(\text{radians}(\text{lat}_2)) \cdot \sin^2\left(\frac{\Delta \lambda}{2}\right)$$
   $$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
   $$d = R \cdot c$$

2. **Impossible Travel Velocity Gates (`R_IMPOSSIBLE_TRAVEL` - 35 pts):**
   - Let $\Delta t_{min} = \frac{t_{now} - t_{prev}}{60}$ and $\text{Speed}_{km/h} = \frac{d}{\Delta t_{hours}}$.
   - **Trigger Condition 1:** $d > 500 \text{ km}$ in $\Delta t_{min} < 30 \text{ min}$ ($\text{Speed} > 1000 \text{ km/h}$)
   - **Trigger Condition 2:** $d > 100 \text{ km}$ in $\Delta t_{min} < 3 \text{ min}$ ($\text{Speed} > 2000 \text{ km/h}$)
   - **Trigger Condition 3:** $\text{Speed} > 1000 \text{ km/h}$ and $d > 50 \text{ km}$

3. **SIM / Device Mismatch (`R_SIM_DEVICE_MISMATCH` - 30 pts):**
   - **SIM Swap Attack:** Same Device Hardware ID ($D_t = D_{prev}$) but Different SIM IMSI ($S_t \ne S_{prev}$).
   - **Account Takeover / Device Swap:** Same SIM IMSI ($S_t = S_{prev}$) active on New Device Hardware ($D_t \ne D_{prev}$).

4. **Hardware Device Farm (`DEVICE_FARM` - 20 pts):**
   - Single Hardware Device ID or SIM ID bound to $\ge 3$ distinct VPAs in the sliding window.

5. **Datacenter / VPN IP Origin (`R_DATACENTER_IP` - 25 pts):**
   - Transaction IP belongs to compiled CIDR subnets of AWS, GCP, Azure, DigitalOcean, Tor Exit Nodes, or commercial proxy VPNs.

---

### 2.9 3-Layer Composite Risk Scoring Engine
**Source Reference:** `app/engine/upi_scorer.py`, `ENCYCLOPEDIA.md` Section 6, 18

$$\text{Combined Score} = \min\left(100, \text{Rule Score} + \text{Adaptive Pts} + \text{Network Pts}\right)$$

Where:
- $\text{Rule Score} = \min(100, \sum \text{Rule Points})$
- $\text{Adaptive Pts} = \lfloor \text{Adaptive Score} \times 25 \rfloor \quad [0, 25]$
- $\text{Network Pts} = \lfloor \text{Network Score} \times 40 \rfloor \quad [0, 40]$

#### Decision Boundaries & Actions
$$\text{Verdict} = \begin{cases} \text{BLOCK} & \text{if } \text{Combined Score} \ge 70 \\ \text{HOLD} & \text{if } 45 \le \text{Combined Score} < 70 \quad \text{OR} \quad \text{Network Score} \ge 0.70 \\ \text{ALLOW} & \text{if } \text{Combined Score} < 45 \text{ and } \text{Network Score} < 0.70 \end{cases}$$

---

## 3. Plain-English Explanation Templates (Rule Rationale Library)

The table below provides the authoritative dictionary of rule codes, formal definitions, anomaly thresholds, and plain-English narrative templates for direct use in `encyclopedia_kb.py` and LLM system prompts.

| Rule Code | Formal Name | Points | Mathematical Trigger / Anomaly Threshold | Plain-English Detection Rationale Template |
|---|---|---|---|---|
| `R_HONEYPOT_HIT` | Synthetic Honeypot Trap Hit | 100 | Payee VPA matches seeded decoy registry or honeypot prefix | "The payee Virtual Payment Address '{payee_vpa}' is an active synthetic honeypot decoy deployed to trap automated crawlers. No legitimate customer can reach this address; transaction blocked with 100% confidence." |
| `R_SIM_DEVICE_MISMATCH` | SIM / Device Telemetry Mismatch | 30 | Device ID same but SIM changed, OR SIM same but Device changed | "Hardware telemetry detected an identity mismatch for payer '{payer_vpa}'. A new SIM card was inserted into a known device (or existing SIM operated on new hardware), matching the signature of a SIM-swap attack or account takeover." |
| `R_IMPOSSIBLE_TRAVEL` | Impossible Geographic Velocity | 35 | Velocity $>1000$ km/h over $>50$ km between consecutive payments | "Payer '{payer_vpa}' recorded consecutive transactions from '{prev_location}' and '{curr_location}' ({distance_km:.0f} km apart) within {delta_mins:.1f} minutes. This requires a velocity of {speed_kmh:.0f} km/h, which is physically impossible and indicates shared credentials or remote session hijacking." |
| `R_DATACENTER_IP` | Datacenter / Cloud / VPN IP Origin | 25 | Client IP falls within AWS, GCP, Azure, DigitalOcean, or Tor CIDR | "Transaction originated from IP address '{ip}', which resolves to a commercial cloud datacenter, VPN provider, or Tor exit node rather than a residential mobile telecom gateway." |
| `R_CAMPAIGN_MATCH` | Fraud Campaign DNA Signature Match | 30 | Multi-vector Cosine similarity $S \ge 0.82$ against active campaign | "Transaction exhibits an {similarity_pct:.0f}% behavioral DNA match with known fraud syndicate '{campaign_id}' ({campaign_name}), matching suspicious payment note keywords, amount structuring brackets, and temporal attack vectors." |
| `PASS_THROUGH_CONDUIT` | Rapid Conduit Pass-Through | 30 | Fresh account ($<30$d), inflow $\ge ₹5,000$, outflow $\ge 90\%$, txn $\ge 50\%$ inflow | "Payer account '{payer_vpa}' is a fresh account ({age_days}d old) acting as a rapid transit conduit, immediately forwarding {outflow_ratio:.0%} of the ₹{received_amount:,.0f} received in the current sliding window with minimal dwell time." |
| `FAN_IN_BURST` | Rapid Multi-Payer Fan-In Burst | 25 | Fresh account ($<30$d) collecting from $\ge 5$ distinct payers | "Payee account '{payee_vpa}' (registered {age_days}d ago) suddenly received funds from {distinct_payers} distinct payers within the sliding window, matching the collector hub pattern of a mule network." |
| `FAN_OUT_DISPERSAL` | Rapid Multi-Payee Fan-Out Dispersal | 25 | Fresh account ($<30$d) dispersing to $\ge 5$ distinct payees | "Payer account '{payer_vpa}' (registered {age_days}d ago) rapidly dispersed funds to {distinct_payees} distinct payee accounts within the sliding window, matching a mule ring cash-out or smurfing dispersal phase." |
| `DEVICE_FARM` | Multi-VPA Hardware Device Farm | 20 | Single Device Hardware ID or SIM ID bound to $\ge 3$ VPAs | "Hardware telemetry reveals that the payer's device/SIM fingerprint is linked to {vpa_count} distinct Virtual Payment Addresses, indicating an organized device farm or mule laundering center." |
| `NEW_ACCOUNT_HIGH_VALUE` | High-Value Fresh Account Outflow | 15–50 | Payer account $<15$d old moving $\ge ₹10,000$ (Tiered up to ₹1,000,000) | "Payer account is brand new ({age_days} days old) but is attempting to transfer a high-value amount of ₹{amount:,.0f} without having established a historical transaction reputation." |
| `LIMIT_SKIRTING` | Regulatory Limit Skirting / Structuring | 10 | Amount sits in $[0.98 \times T, T)$ for $T \in \{10k, 15k, 25k, 50k, 100k\}$ | "The transaction amount of ₹{amount:,.2f} sits suspiciously within 2% below the ₹{threshold:,.0f} regulatory monitoring threshold, indicating intentional smurfing/structuring to avoid compliance alarms." |
| `NEW_PAYEE_VPA` | Fresh Payee VPA Registration | 25 | Payee VPA registered $<15$ days ago | "Payee Virtual Payment Address '{payee_vpa}' was created only {age_days} days ago (<15 days threshold), representing a fresh and unverified counterparty." |
| `KNOWN_FRAUD_ENTITY` | Confirmed Fraud Entity Memory | 35 | Payer or Payee flagged in prior analyst-confirmed fraud | "Party '{vpa}' has previously appeared in {confirmed_count} analyst-confirmed fraud case(s) and has been retained in high-risk memory." |
| `BEHAVIORAL_ANOMALY` | Adaptive EWMA Behavioral Anomaly | 0–25 | Adaptive EWMA statistical score $\ge 0.60$ ($Z_{amt} \ge 3.0$) | "Payer transaction amount of ₹{amount:,.0f} significantly deviates from their historical EWMA baseline (mean: ₹{mean_amount:,.0f}, variance: {variance:.1f}), representing an extreme statistical anomaly ({z_score:.1f} standard deviations)." |
| `FEDERATED_MULE_NETWORK` | Cross-PSP Federated Ring Intelligence | 0–40 | Federated risk score $\ge 0.50$ from multi-bank mesh | "Cross-PSP federated intelligence mesh identified participating entities as part of confirmed mule ring '{ring_hash}' spanning {psp_count} banking institutions." |
| `DEAD_MONEY_VELOCITY` | Dead Money Velocity Surge | Metric | DMV Score $\ge 70.0$ (High Dormancy Gap + High Outflow Velocity) | "The payer account was dormant for {dormancy_days:.1f} days before suddenly draining {drain_ratio:.0%} of its available balance across {txn_count_1h} transactions in a 1-hour window (DMV Score: {dmv_score}/100)." |

---

## 4. Token Economy & Vision Multimodal Compression Reference
**Source Reference:** `app/forensics/sar_pdf.py`, `app/forensics/token_economy.pyc`, `app/forensics/upi_sar.pyc`

### Token Calculation & Cost Model
- **Vision Tile Calculation ($1200 \times 900$ default topology):**
  $$\text{Tiles}_X = \max(1, \lceil \text{width} / 768 \rceil), \quad \text{Tiles}_Y = \max(1, \lceil \text{height} / 768 \rceil)$$
  $$\text{Vision Tokens} = 258 \text{ tokens (for } \le 1200\times 900) \quad \text{or} \quad \text{Tiles}_X \times \text{Tiles}_Y \times 258$$
  $$\text{Total Multimodal Tokens} = \text{Vision Tokens} + 75 \text{ (prompt overhead)} = 333 \text{ tokens}$$
- **Raw Text Comparison:**
  - Raw JSON serialization of 200+ case transactions $\approx 3,500 – 12,000 \text{ tokens}$.
  - Multimodal Vision compression ratio: $10.5\times – 36.0\times$ token reduction.
  - Cost savings percentage: $90.5\% – 97.2\%$.

