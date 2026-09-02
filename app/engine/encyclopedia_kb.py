"""Encyclopedia Algorithmic Knowledge Base for SAMPATI V2.

Indexes mathematical formulas, algorithmic definitions, and plain-English detection
rationales extracted directly from ENCYCLOPEDIA.md. Provides rule code normalization,
rich forensic explanations, dynamic metric interpolation, prompt injection context
formatting, and fast in-memory keyword search.

Zero external network/DB dependencies, sub-millisecond execution, thread-safe.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# ── 1. Canonical Rule Definitions Registry ────────────────────────────────────

RULE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "DMV_RAPID_DRAIN": {
        "canonical_code": "DMV_RAPID_DRAIN",
        "name": "Dead Money Velocity (DMV) Burst",
        "aliases": [
            "RULE_DMV_VELOCITY", "DMV_VELOCITY", "DMV_SCORE", "DMV",
            "DEAD_MONEY_VELOCITY", "DMV_BURST", "DEAD_MONEY", "RAPID_DRAIN",
            "DORMANT_DRAIN"
        ],
        "layer": 1,
        "severity": "CRITICAL",
        "points": 35,
        "default_points": 35,
        "category": "VELOCITY",
        "mathematical_definition": (
            "Dormancy Index D = min(1.0, elapsed_dormancy_days / 30.0)\n"
            "Drain Ratio R = min(1.0, current_outflow_1h / max(inflow_24h, amount, 1.0))\n"
            "Burst Velocity V = (0.50 * R) + (0.30 * min(1.0, (count_1h + 1) / 4.0)) + (0.20 * min(1.0, amount / 30000.0))\n"
            "Raw DMV = 100.0 * (0.40 * D + 0.60 * V)\n"
            "Final DMV = min(100.0, Raw DMV * (1.0 + 0.5 * D * V)) if (D >= 0.5 and V >= 0.4) else Raw DMV"
        ),
        "plain_english_explanation": (
            "Quantifies the signature pattern of a mule account: an extended period of dormancy (weeks or months) "
            "followed by a sudden, near-complete balance dissipation in a narrow time window. Legitimate operational "
            "accounts maintain a steady transactional cadence, whereas disposable mule accounts lay dormant until "
            "illicit funds are deposited and immediately routed out to cash-out endpoints."
        ),
        "detection_mechanism": "Sliding window ratio analysis using in-memory deque with O(1) eviction.",
        "typical_threshold": "DMV Score >= 70.0 indicates CRITICAL risk; 40.0 - 69.9 indicates ELEVATED risk.",
        "recommended_action": "Place immediate temporary debit freeze on payee entity and request source bank verification.",
        "regulatory_typology": "Layered Mule Laundering / Rapid Pass-Through Account Draining (RBI Master Direction on Digital Payment Security Controls)",
        "keywords": ["dmv", "velocity", "dead money", "dormancy", "burst", "drain", "depletion", "sliding window", "sleeper"]
    },
    "R_HONEYPOT_HIT": {
        "canonical_code": "R_HONEYPOT_HIT",
        "name": "Synthetic Honeypot Trap Hit",
        "aliases": [
            "HONEYPOT_HIT", "HONEYPOT", "R_HONEYPOT", "HONEYPOT_TRAP",
            "SYNTHETIC_HONEYPOT", "HONEYPOT_PROBE", "SYNTHETIC_TRAP", "R_HONEYPOT_HIT"
        ],
        "layer": 1,
        "severity": "CRITICAL",
        "points": 100,
        "default_points": 100,
        "category": "HONEYPOT",
        "mathematical_definition": (
            "Hit = 1 if (payee_vpa in SEEDED_HONEYPOTS or any(payee_vpa.startswith(p) for p in HONEYPOT_PREFIXES)) else 0\n"
            "Risk Points = 100 (Immediate deterministic BLOCK verdict regardless of other layers)"
        ),
        "plain_english_explanation": (
            "The transaction was deliberately sent to a synthetic decoy VPA registered in underground fraud lists "
            "and darknet databases. Because these addresses have zero legitimate commercial utility, any inbound transfer "
            "is mathematically guaranteed to originate from an automated bot probe or a compromised mule operator."
        ),
        "detection_mechanism": "Exact and prefix-based O(1) registry set lookup in memory.",
        "typical_threshold": "Exact match (Binary 0 or 1). Guarantees immediate BLOCK verdict.",
        "recommended_action": "Immediately BLOCK transaction, blacklist originating device/IP, and broadcast threat hash.",
        "regulatory_typology": "Synthetic Identity Probing / Darknet Mule Recruitment (National Cyber Crime Reporting Portal - 1930)",
        "keywords": ["honeypot", "trap", "decoy", "botnet", "probe", "synthetic", "darknet", "blacklist"]
    },
    "R_SIM_DEVICE_MISMATCH": {
        "canonical_code": "R_SIM_DEVICE_MISMATCH",
        "name": "SIM / Device Telemetry Mismatch",
        "aliases": [
            "SIM_DEVICE_MISMATCH", "SIM_SWAP", "DEVICE_MISMATCH",
            "DEVICE_SWAP", "SIM_MISMATCH", "TELEMETRY_MISMATCH", "R_SIM_DEVICE_MISMATCH"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 30,
        "default_points": 30,
        "category": "IDENTITY",
        "mathematical_definition": (
            "Mismatch = (device_id == last_device and sim_id != last_sim) [SIM Swap]\n"
            "         or (sim_id == last_sim and device_id != last_device) [Device Takeover]"
        ),
        "plain_english_explanation": (
            "Detects hardware IMEI or SIM IMSI identity anomalies for a known payer account. A new SIM card inserted "
            "into a known device indicates SIM-swap fraud, while an existing SIM operating from new hardware indicates "
            "physical device swapping or credential account takeover."
        ),
        "detection_mechanism": "In-memory telemetry state tracking with thread-safe lock.",
        "typical_threshold": "State transition detected between consecutive transactions for the same VPA.",
        "recommended_action": "Trigger out-of-band biometric verification and place a 24-hour cooling hold on outgoing transfers.",
        "regulatory_typology": "Account Takeover / SIM-Swap Fraud (Cyber Crime Prevention Protocol)",
        "keywords": ["sim", "device", "mismatch", "swap", "takeover", "hardware", "imsi", "imei", "telemetry"]
    },
    "R_IMPOSSIBLE_TRAVEL": {
        "canonical_code": "R_IMPOSSIBLE_TRAVEL",
        "name": "Impossible Geographic Travel Velocity",
        "aliases": [
            "IMPOSSIBLE_TRAVEL", "TRAVEL_VELOCITY", "GEO_VELOCITY",
            "IMPOSSIBLE_SPEED", "GEO_JUMP", "PHYSICAL_TRAVEL", "TRAVEL_SPEED", "R_IMPOSSIBLE_TRAVEL"
        ],
        "layer": 1,
        "severity": "CRITICAL",
        "points": 35,
        "default_points": 35,
        "category": "IDENTITY",
        "mathematical_definition": (
            "Distance d = 2 * R * arcsin(sqrt(sin^2(d_lat/2) + cos(lat1)*cos(lat2)*sin^2(d_lon/2))) [Haversine, R=6371km]\n"
            "Velocity v = Distance / delta_time_hours\n"
            "Triggered if (d > 500km and delta_mins < 30) or (d > 100km and delta_mins < 3) or (v > 1000 km/h and d > 50km)"
        ),
        "plain_english_explanation": (
            "The physical geographic location of the payer account altered faster than commercial airline speeds "
            "between consecutive transactions (e.g., a payment in Mumbai followed by a payment in Delhi 4 minutes later). "
            "This proves concurrent credential sharing, proxy spoofing, or automated account hijacking."
        ),
        "detection_mechanism": "Haversine great-circle distance computation over geographic coordinates and timestamps.",
        "typical_threshold": "Calculated travel velocity > 1,000 km/h over distances exceeding 50 km.",
        "recommended_action": "Invalidate current session tokens, force re-authentication, and hold pending transfers.",
        "regulatory_typology": "Concurrent Session Spoofing / Credential Stuffing (RBI IT Framework for Banks)",
        "keywords": ["travel", "impossible", "geographic", "location", "speed", "velocity", "haversine", "distance", "spoofing"]
    },
    "R_DATACENTER_IP": {
        "canonical_code": "R_DATACENTER_IP",
        "name": "Datacenter / Cloud / VPN IP Origin",
        "aliases": [
            "DATACENTER_IP", "VPN_IP", "TOR_IP", "CLOUD_IP",
            "HOSTING_IP", "DATACENTER_ORIGIN", "PROXY_IP", "TOR_EXIT", "DATACENTER", "R_DATACENTER_IP"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 25,
        "default_points": 25,
        "category": "NETWORK",
        "mathematical_definition": (
            "Match = 1 if ip_address in compiled_datacenter_networks (AWS, GCP, Azure, DigitalOcean, Tor, Public VPNs) else 0"
        ),
        "plain_english_explanation": (
            "The transaction was initiated from an IP address belonging to a commercial cloud provider (AWS, GCP, Azure, "
            "DigitalOcean) or an anonymizing VPN/Tor exit node rather than a residential or mobile ISP (Jio, Airtel, Vi). "
            "Legitimate UPI payments originate from consumer mobile devices; datacenter traffic signifies automated fraud scripts."
        ),
        "detection_mechanism": "Radix-tree/subnet CIDR containment matching using Python ipaddress.",
        "typical_threshold": "Payer IP falls within compiled datacenter/VPN CIDR subnets.",
        "recommended_action": "Require step-up CAPTCHA / device binding verification and restrict API access.",
        "regulatory_typology": "Automated Botnet Origin / Anonymized Proxy Routing (CERT-In Advisory)",
        "keywords": ["datacenter", "cloud", "vpn", "tor", "proxy", "ip", "aws", "gcp", "azure", "hosting"]
    },
    "R_CAMPAIGN_MATCH": {
        "canonical_code": "R_CAMPAIGN_MATCH",
        "name": "Fraud Campaign DNA Match",
        "aliases": [
            "CAMPAIGN_MATCH", "CAMPAIGN_DNA", "FRAUD_CAMPAIGN",
            "CAMPAIGN_FINGERPRINT", "SYNDICATE_MATCH", "DNA_MATCH", "CAMPAIGN", "R_CAMPAIGN_MATCH"
        ],
        "layer": 1,
        "severity": "CRITICAL",
        "points": 30,
        "default_points": 30,
        "category": "CAMPAIGN",
        "mathematical_definition": (
            "Similarity = (0.35 * KeywordSim) + (0.30 * AmountSim) + (0.15 * HourSim) + (0.20 * VpaMembershipSim)\n"
            "Triggered if max(Similarity over all stored campaign signatures) >= 0.82 (82%)"
        ),
        "plain_english_explanation": (
            "The multi-attribute behavioral DNA fingerprint of the transaction (payment note keywords, structured amount, "
            "time of day, payee handle) exhibits an 82%+ cosine-like similarity to known active fraud syndicate profiles, "
            "such as KYC phishing campaigns, micro-smurfing dispersal rings, or Telegram task/investment scams."
        ),
        "detection_mechanism": "Weighted multi-feature similarity scoring against active CampaignSignatureStore.",
        "typical_threshold": "Composite similarity score >= 0.82 against stored campaign fingerprints.",
        "recommended_action": "Cluster linked accounts into campaign dossier and escalate to FIU-IND cybercrime cell.",
        "regulatory_typology": "Organized Cybercrime Syndicate / Phishing Campaign Cluster (FIU-IND Red Flag)",
        "keywords": ["campaign", "dna", "fingerprint", "syndicate", "phishing", "smurfing", "task", "similarity", "cluster"]
    },
    "PASS_THROUGH_CONDUIT": {
        "canonical_code": "PASS_THROUGH_CONDUIT",
        "name": "Rapid Conduit Pass-Through",
        "aliases": [
            "CONDUIT", "PASS_THROUGH", "R05_HIGH_RISK_HOPS", "HIGH_RISK_HOPS",
            "RAPID_CONDUIT", "CONDUIT_RELAY", "LAYERING_HOP", "RAPID_FORWARD", "PASS_THROUGH_CONDUIT"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 30,
        "default_points": 30,
        "category": "FLOW",
        "mathematical_definition": (
            "Triggered if payer_account_age < 30 days\n"
            "  and inbound_sum_1h >= Rs 5,000\n"
            "  and (outbound_sum_1h + amount) / inbound_sum_1h >= 0.90 (90%)\n"
            "  and amount >= 0.50 * inbound_sum_1h"
        ),
        "plain_english_explanation": (
            "The account rapidly forwards 90%+ of all incoming funds within a narrow sliding window. This near-total "
            "depletion without balance accumulation or merchant utility is the definitive signature of a pass-through "
            "layering node in a multi-hop money laundering chain."
        ),
        "detection_mechanism": "Sliding window inflow/outflow ratio evaluation in UpiHotState.",
        "typical_threshold": "Outflow/Inflow ratio >= 90% with inflow >= Rs 5,000 on accounts under 30 days old.",
        "recommended_action": "Freeze outbound settlement and trace downstream recipient accounts for ring containment.",
        "regulatory_typology": "Pass-Through Layering Conduit (FIU-IND Red Flag Indicator)",
        "keywords": ["conduit", "pass-through", "layering", "flow", "relay", "inflow", "outflow", "ratio", "hop"]
    },
    "FAN_IN_BURST": {
        "canonical_code": "FAN_IN_BURST",
        "name": "Rapid Multi-Payer Fan-In",
        "aliases": [
            "FAN_IN", "RAPID_FAN_IN", "HIGH_VELOCITY_FAN_IN",
            "BURST_FAN_IN", "COLLECTOR_HUB", "FAN_IN_BURST_COLLECTOR",
            "BURST_COLLECTION", "FAN_IN_BURST"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 25,
        "default_points": 25,
        "category": "FLOW",
        "mathematical_definition": (
            "Triggered if payee_vpa_age < 30 days and (distinct_payers_in_window + 1) >= 5"
        ),
        "plain_english_explanation": (
            "A newly created account received payments from 5 or more distinct payers in a short sliding window. "
            "In fraud operations, this identifies a 'Collector Hub' aggregating stolen money from multiple victims "
            "before consolidating the balance for rapid dispersal."
        ),
        "detection_mechanism": "Distinct counterparty set tracking in UpiHotState sliding window.",
        "typical_threshold": ">= 5 distinct payers funneling into a fresh account (<30 days old).",
        "recommended_action": "Mark node as Collector Hub in graph topology and flag all inbound payer accounts.",
        "regulatory_typology": "Mule Collection Hub / Aggregation Point (RBI Master Direction)",
        "keywords": ["fan-in", "collector", "hub", "aggregation", "distinct", "payers", "victims", "burst"]
    },
    "FAN_OUT_DISPERSAL": {
        "canonical_code": "FAN_OUT_DISPERSAL",
        "name": "Rapid Multi-Payee Fan-Out",
        "aliases": [
            "FAN_OUT", "RAPID_FAN_OUT", "R01_RAPID_FAN_OUT",
            "BURST_FAN_OUT", "CASHOUT_DISPERSAL", "DISPERSAL_NODE",
            "DISPERSAL", "SMURF_DISPERSAL", "FAN_OUT_DISPERSAL"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 25,
        "default_points": 25,
        "category": "FLOW",
        "mathematical_definition": (
            "Triggered if payer_account_age < 30 days and (distinct_payees_in_window + 1) >= 5"
        ),
        "plain_english_explanation": (
            "A newly created account rapidly dispersed funds to 5 or more distinct payees in a short time window. "
            "This pattern indicates smurfing / cash-out dispersal designed to split aggregated stolen funds into "
            "smaller chunks across secondary mule accounts to evade detection."
        ),
        "detection_mechanism": "Distinct counterparty set tracking in UpiHotState sliding window.",
        "typical_threshold": ">= 5 distinct payees dispersing from a fresh account (<30 days old).",
        "recommended_action": "Place immediate hold on outgoing batches and submit federated signals for recipient VPAs.",
        "regulatory_typology": "Smurfing Dispersal / Cash-Out Fragmentation (PMLA Section 12 Compliance)",
        "keywords": ["fan-out", "dispersal", "cash-out", "smurfing", "distinct", "payees", "split", "burst"]
    },
    "DEVICE_FARM": {
        "canonical_code": "DEVICE_FARM",
        "name": "Multi-VPA Hardware Device Farm",
        "aliases": [
            "DEVICE_CLUSTERING", "DEVICE_SWITCH_BURST", "R03_DEVICE_SWITCH_BURST",
            "MULE_FARM", "FARM_CLUSTERING", "DEVICE_FARM_DETECTED",
            "FARM", "SIM_FARM", "DEVICE_FARM"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 20,
        "default_points": 20,
        "category": "IDENTITY",
        "mathematical_definition": (
            "Triggered if count(distinct VPAs bound to device_id) >= 3 or count(distinct VPAs bound to sim_id) >= 3"
        ),
        "plain_english_explanation": (
            "The payer's physical device hardware fingerprint or SIM IMSI is actively associated with 3 or more distinct "
            "UPI VPAs. This hardware clustering strongly indicates an organized mule farm operating phone racks or automated "
            "device emulators to manage multiple compromised accounts."
        ),
        "detection_mechanism": "In-memory device-to-VPA bipartite mapping in UpiHotState.",
        "typical_threshold": ">= 3 distinct VPAs bound to the same hardware device or SIM card.",
        "recommended_action": "Flag hardware identifier for global quarantine across all associated banking VPAs.",
        "regulatory_typology": "Automated Mule Farm / Hardware Rack Syndicate (Cybercrime Cell Typology)",
        "keywords": ["device", "farm", "clustering", "hardware", "sim", "emulator", "multiple vpas", "rack"]
    },
    "NEW_ACCOUNT_HIGH_VALUE": {
        "canonical_code": "NEW_ACCOUNT_HIGH_VALUE",
        "name": "High-Value New Account Outflow",
        "aliases": [
            "HIGH_VALUE_NEW_ACCOUNT", "NEW_ACC_HIGH_VAL", "NEW_ACCOUNT_LARGE_TRANSFER",
            "FRESH_ACCOUNT_HIGH_VALUE", "HIGH_VALUE_OUTFLOW", "HIGH_VALUE_NEW_ACC",
            "NEW_ACC_HV", "NEW_ACCOUNT_HIGH_VALUE"
        ],
        "layer": 1,
        "severity": "HIGH",
        "points": 25,
        "default_points": 25,
        "category": "BEHAVIORAL",
        "mathematical_definition": (
            "Triggered if payer_account_age < 15 days and amount >= Rs 10,000\n"
            "Points Tier: >= Rs 1M -> 50 pts; >= Rs 100k -> 45 pts; >= Rs 50k -> 25 pts; >= Rs 10k -> 15 pts"
        ),
        "plain_english_explanation": (
            "A newly registered account (fewer than 15 days old) initiated a large outbound payment. Legitimate bank accounts "
            "establish transaction history with smaller values; immediate high-value outflows indicate an account opened or "
            "purchased specifically for a one-off laundering burst."
        ),
        "detection_mechanism": "Account age and amount threshold conditional evaluation.",
        "typical_threshold": "Amount >= Rs 10,000 on accounts < 15 days old.",
        "recommended_action": "Hold transaction pending voice/biometric confirmation from account holder.",
        "regulatory_typology": "Unseasoned High-Velocity Outflow (RBI Master Direction on KYC/AML)",
        "keywords": ["new account", "high value", "large transfer", "fresh", "age", "outflow", "threshold"]
    },
    "LIMIT_SKIRTING": {
        "canonical_code": "LIMIT_SKIRTING",
        "name": "Threshold Limit Skirting / Structuring",
        "aliases": [
            "STRUCTURING", "SMURFING", "STRUCTURING_BURST", "R02_STRUCTURING_BURST",
            "THRESHOLD_SKIRTING", "LIMIT_AVOIDANCE", "CAUTION_THRESHOLD", "LIMIT_SKIRTING"
        ],
        "layer": 1,
        "severity": "LOW",
        "points": 10,
        "default_points": 10,
        "category": "STRUCTURING",
        "mathematical_definition": (
            "Triggered if any(threshold * 0.98 <= amount < threshold for threshold in [10000, 15000, 25000, 50000, 100000])"
        ),
        "plain_english_explanation": (
            "The transaction amount sits suspiciously within 2% below standard regulatory reporting thresholds or KYC friction "
            "limits (e.g., Rs 49,999, Rs 24,990, or Rs 9,999). Known as structuring or smurfing, this technique is intentionally "
            "used by criminals to evade automatic currency transaction reporting."
        ),
        "detection_mechanism": "Interval containment test against regulatory caution thresholds.",
        "typical_threshold": "Amount within [0.98 * Limit, Limit) for limits 10k, 15k, 25k, 50k, 100k.",
        "recommended_action": "Aggregate rolling 24-hour total for entity to check cumulative threshold breaches.",
        "regulatory_typology": "Currency Transaction Structuring / Smurfing (FIU-IND Anti-Structuring Rule)",
        "keywords": ["limit", "skirting", "structuring", "smurfing", "threshold", "kyc", "evasion", "reporting"]
    },
    "NEW_PAYEE_VPA": {
        "canonical_code": "NEW_PAYEE_VPA",
        "name": "Fresh Payee VPA (<15d)",
        "aliases": [
            "FRESH_PAYEE_VPA", "FRESH_VPA", "NEW_PAYEE", "NEW_PAYEE_HANDLE",
            "FRESH_PAYEE", "NEW_PAYEE_VPA"
        ],
        "layer": 1,
        "severity": "MEDIUM",
        "points": 25,
        "default_points": 25,
        "category": "IDENTITY",
        "mathematical_definition": (
            "Triggered if payee_vpa_age_days < 15 days"
        ),
        "plain_english_explanation": (
            "The recipient Virtual Payment Address was registered fewer than 15 days ago. High-frequency mule syndicates "
            "continuously register and discard fresh VPAs to bypass static blacklists."
        ),
        "detection_mechanism": "Entity metadata age check against FRESH_VPA_DAYS constant.",
        "typical_threshold": "Payee VPA age < 15 days.",
        "recommended_action": "Check counterparty bank reputation and historical dispute rate on the issuing PSP.",
        "regulatory_typology": "Ephemeral Mule Account Cycling (NPCI Risk Assessment Guideline)",
        "keywords": ["new payee", "fresh vpa", "age", "handle", "disposable", "cycling"]
    },
    "KNOWN_FRAUD_ENTITY": {
        "canonical_code": "KNOWN_FRAUD_ENTITY",
        "name": "Confirmed Fraud Entity Memory",
        "aliases": [
            "FRAUD_MEMORY", "HISTORICAL_FRAUD", "REPEAT_FRAUDSTER", "KNOWN_FRAUD",
            "REPEAT_OFFENDER", "BLACKLISTED_VPA", "KNOWN_FRAUD_ENTITY"
        ],
        "layer": 1,
        "severity": "CRITICAL",
        "points": 35,
        "default_points": 35,
        "category": "REPUTATION",
        "mathematical_definition": (
            "Triggered if state.fraud_memory(payer_vpa) > 0 or state.fraud_memory(payee_vpa) > 0"
        ),
        "plain_english_explanation": (
            "Either the payer or payee VPA has been previously confirmed as fraudulent in analyst-reviewed case investigations. "
            "Provides institutional memory so confirmed bad actors are instantly penalized on repeat attempts."
        ),
        "detection_mechanism": "In-memory fraud memory counter lookup in UpiHotState.",
        "typical_threshold": "Confirmed fraud count >= 1.",
        "recommended_action": "Immediately BLOCK transaction and notify FIU-IND of repeat syndicate activity.",
        "regulatory_typology": "Repeat Financial Offender / Persistent Bad Actor List (FIU-IND Section 12)",
        "keywords": ["known fraud", "confirmed", "memory", "repeat", "analyst", "escalated", "blacklist"]
    },
    "BEHAVIORAL_ANOMALY": {
        "canonical_code": "BEHAVIORAL_ANOMALY",
        "name": "Adaptive EWMA Behavioral Anomaly",
        "aliases": [
            "ADAPTIVE_ANOMALY", "EWMA_ANOMALY", "LAYER2_ADAPTIVE",
            "BEHAVIOR_ANOMALY", "STREAMING_ANOMALY", "ADAPTIVE_EWMA",
            "EWMA", "ANOMALY_Z", "BEHAVIORAL_ANOMALY"
        ],
        "layer": 2,
        "severity": "HIGH",
        "points": 25,
        "default_points": 25,
        "category": "BEHAVIORAL",
        "mathematical_definition": (
            "new_mean = alpha * amount + (1 - alpha) * old_mean\n"
            "new_variance = alpha * (amount - new_mean)^2 + (1 - alpha) * old_variance\n"
            "Z-Score = |amount - new_mean| / sqrt(new_variance)\n"
            "Adaptive Score = min(1.0, Z-Score / 4.0)\n"
            "Layer 2 Points = int(Adaptive Score * 25)"
        ),
        "plain_english_explanation": (
            "The transaction amount deviates significantly from the account's historical spending profile maintained via "
            "Exponentially Weighted Moving Average (EWMA). By learning personal baselines in streaming real-time, the system "
            "catches unusual volume spikes without requiring massive historical database queries."
        ),
        "detection_mechanism": "Streaming online statistics (EWMA mean and variance) with decay factor alpha.",
        "typical_threshold": "Z-Score >= 2.5 (Adaptive Score >= 0.60 contributes 15-25 points).",
        "recommended_action": "Compare against historical peer-group spending norms and review device consistency.",
        "regulatory_typology": "Unusual Transaction Volume / Behavioral Outlier (RBI Fair Practices Code)",
        "keywords": ["adaptive", "ewma", "anomaly", "z-score", "mean", "variance", "streaming", "layer 2"]
    },
    "FEDERATED_MULE_NETWORK": {
        "canonical_code": "FEDERATED_MULE_NETWORK",
        "name": "Federated Mule Network Risk",
        "aliases": [
            "FEDERATION_RISK", "CROSS_PSP_MULE_RING", "R07_CROSS_PSP_MULE_RING",
            "FED_MESH", "FEDERATED_NETWORK_SCORE", "FEDERATION_MULE",
            "MULE_RING", "MULE", "FEDERATION_SIGNAL", "FEDERATED_MULE_NETWORK"
        ],
        "layer": 3,
        "severity": "CRITICAL",
        "points": 40,
        "default_points": 40,
        "category": "NETWORK",
        "mathematical_definition": (
            "vpa_hash = SHA256(salt + ':' + vpa.lower())\n"
            "Network Score = max(query_federation(payer_hash), query_federation(payee_hash))\n"
            "Layer 3 Points = int(Network Score * 40)\n"
            "Enforces mandatory HOLD if Network Score >= 0.70"
        ),
        "plain_english_explanation": (
            "Cross-institution threat intelligence signals shared by peer banks (HDFC, SBI, Paytm, Axis, ICICI) converge on "
            "the entity's pseudonymized VPA hash. Detects multi-bank mule rings spanning institutional boundaries while "
            "preserving 100% data privacy under financial banking secrecy laws."
        ),
        "detection_mechanism": "Sub-5ms in-memory query against FederatedCoordinator signal cache.",
        "typical_threshold": "Federated risk score >= 0.50 contributes points; score >= 0.70 mandates HOLD.",
        "recommended_action": "Initiate automated multi-bank federation consensus round and freeze cross-PSP corridors.",
        "regulatory_typology": "Cross-Border / Multi-PSP Syndicate Mule Laundering Mesh (NPCI Federated Defense)",
        "keywords": ["federation", "network", "cross-psp", "mesh", "sha256", "privacy", "salt", "layer 3", "ring", "mule"]
    },
    "DPIP_BLACKLIST": {
        "canonical_code": "DPIP_BLACKLIST",
        "name": "DPIP Intelligence Blacklist",
        "aliases": [
            "R06_DPIP_BLACKLIST", "DPIP_INTELLIGENCE", "DPIP_FEED_FLAG", "DPIP_FEED", "DPIP", "DPIP_BLACKLIST"
        ],
        "layer": 3,
        "severity": "CRITICAL",
        "points": 40,
        "default_points": 40,
        "category": "REPUTATION",
        "mathematical_definition": (
            "External Risk = 1.0 if vpa in DPIP_BLACKLIST_REGISTRY else 0.0\n"
            "Layer 3 Points = int(External Risk * 40)"
        ),
        "plain_english_explanation": (
            "The VPA is actively listed on the national Digital Payments Intelligence Platform (DPIP) blacklist as a "
            "confirmed cybercrime mule account or syndicate relay node."
        ),
        "detection_mechanism": "DpipFeed external signal cache lookup.",
        "typical_threshold": "External risk score = 1.0.",
        "recommended_action": "Mandatory BLOCK and transmit real-time telemetry to DPIP centralized rail.",
        "regulatory_typology": "National Cybercrime Blacklist Match (DPIP Central Gateway)",
        "keywords": ["dpip", "blacklist", "intelligence", "national", "cybercrime", "external signal"]
    },
    "GINI_INEQUALITY": {
        "canonical_code": "GINI_INEQUALITY",
        "name": "Gini Transfer Dispersion Inequality",
        "aliases": [
            "GINI", "GINI_INEQUALITY", "GINI_COEFFICIENT", "GINI_DISPERSION",
            "AMOUNT_GINI", "GINI_SCORE"
        ],
        "layer": 4,
        "severity": "MEDIUM",
        "points": 0,
        "default_points": 0,
        "category": "ANALYTICS",
        "mathematical_definition": (
            "G = sum(sum(|x_i - x_j| for j in 1..n) for i in 1..n) / (2 * n * sum(x_i for i in 1..n))\n"
            "Interpretation: G in [0.0, 1.0]. G < 0.15 indicates uniform structuring; G > 0.70 indicates concentrated funnel."
        ),
        "plain_english_explanation": (
            "Measures the statistical inequality of transfer amounts across the mule ring graph. A near-zero Gini coefficient "
            "proves uniform structuring (splitting stolen amounts into identical smaller sums), whereas a high Gini coefficient "
            "identifies asymmetric funneling into central cash-out aggregators."
        ),
        "detection_mechanism": "Graph edge weight distribution calculation over NetworkX DiGraph.",
        "typical_threshold": "Gini < 0.15 (Structured Smurfing) or Gini > 0.70 (Asymmetric Collector Funnel).",
        "recommended_action": "Use Gini metric to distinguish automated smurf scripts from manual peer transactions.",
        "regulatory_typology": "Graph Topology Dispersal Inequality (Graph Analytics / Anti-Structuring)",
        "keywords": ["gini", "inequality", "dispersion", "distribution", "structuring", "graph", "analytics"]
    },
    "GRAPH_ML_ROLE": {
        "canonical_code": "GRAPH_ML_ROLE",
        "name": "Graph ML Node Role Classification",
        "aliases": [
            "NODE_ROLE_CLASSIFICATION", "TOPOLOGY_ROLE", "NETWORKX_ROLES",
            "MULE_ROLE", "GRAPH_ROLES", "NODE_ROLE", "GRAPH_ML",
            "GRAPH_ROLE_CLASSIFICATION", "GRAPH_ML_ROLE"
        ],
        "layer": 4,
        "severity": "HIGH",
        "points": 0,
        "default_points": 0,
        "category": "ANALYTICS",
        "mathematical_definition": (
            "Victim: In-Degree = 0, Out-Degree >= 1, PriorFraud = 0\n"
            "Collector Hub: In-Degree >= 5, Out-Degree <= 2 (High aggregation)\n"
            "Layering Hop: In-Degree >= 1, Out-Degree >= 1, Outflow / Inflow ~= 1.0 (Pass-Through)\n"
            "Cash-Out Endpoint: In-Degree >= 1, Out-Degree = 0 (Terminal sink)"
        ),
        "plain_english_explanation": (
            "Applies graph theory centrality and flow conservation metrics to classify each node in the fraud network into "
            "its structural role: Victim (original source), Collector Hub (first-hop aggregator), Layering Hop (pass-through "
            "conduit), or Cash-Out Node (terminal ATM / crypto dissipation exit)."
        ),
        "detection_mechanism": "NetworkX directed graph in-degree, out-degree, and flow conservation analysis.",
        "typical_threshold": "Topological connectivity pattern matching across confirmed ring graph.",
        "recommended_action": "Prioritize freezing on Cash-Out nodes to intercept fund dissipation before ATM withdrawal.",
        "regulatory_typology": "Graph ML Structural Decomposition (Network Centrality & Role Clustering)",
        "keywords": ["graph", "role", "victim", "collector", "layering", "cash-out", "networkx", "topology", "centrality"]
    },
}

# ── 2. Fast Alias Lookup Index Construction ──────────────────────────────────

_ALIAS_TO_CANONICAL: Dict[str, str] = {}


def _normalize_key(s: str) -> str:
    """Normalize string for robust, case/punctuation-insensitive dictionary lookup."""
    if not s or not isinstance(s, str):
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", s).upper()


def _initialize_alias_index() -> None:
    """Populate fast lookup mapping from canonical codes, aliases, and stripped variants."""
    for canonical_code, definition in RULE_DEFINITIONS.items():
        # Map canonical code
        _ALIAS_TO_CANONICAL[canonical_code] = canonical_code
        _ALIAS_TO_CANONICAL[_normalize_key(canonical_code)] = canonical_code
        _ALIAS_TO_CANONICAL[canonical_code.lower()] = canonical_code

        # Map all registered aliases
        for alias in definition.get("aliases", []):
            _ALIAS_TO_CANONICAL[alias] = canonical_code
            _ALIAS_TO_CANONICAL[_normalize_key(alias)] = canonical_code
            _ALIAS_TO_CANONICAL[alias.lower()] = canonical_code

        # Map human name
        name = definition.get("name", "")
        if name:
            _ALIAS_TO_CANONICAL[_normalize_key(name)] = canonical_code
            _ALIAS_TO_CANONICAL[name.lower()] = canonical_code


_initialize_alias_index()


# ── 3. Public API Functions ───────────────────────────────────────────────────

def normalize_rule_code(rule_code: Any) -> str:
    """Normalizes any incoming rule code or alias to its canonical knowledge base identifier.
    
    Examples:
        'RULE_DMV_VELOCITY' -> 'DMV_RAPID_DRAIN'
        'dmv'               -> 'DMV_RAPID_DRAIN'
        'R_HONEYPOT_HIT'    -> 'R_HONEYPOT_HIT'
        'sim_swap'          -> 'R_SIM_DEVICE_MISMATCH'
        'structuring'       -> 'LIMIT_SKIRTING'
        'gini'              -> 'GINI_INEQUALITY'
        'UNKNOWN_RULE_XYZ'  -> 'UNKNOWN_RULE_XYZ'
    """
    if not rule_code:
        return "UNKNOWN_RULE"
    if not isinstance(rule_code, str):
        raw = str(rule_code).strip()
    else:
        raw = rule_code.strip()

    if not raw:
        return "UNKNOWN_RULE"

    if raw in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[raw]

    norm = _normalize_key(raw)
    if norm in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[norm]

    # Handle common prefixes e.g. RULE_, R_, HIT_, CHECK_
    for prefix in ("RULE_", "R_", "HIT_", "CHECK_"):
        if raw.upper().startswith(prefix):
            sub = raw[len(prefix):]
            sub_norm = _normalize_key(sub)
            if sub_norm in _ALIAS_TO_CANONICAL:
                return _ALIAS_TO_CANONICAL[sub_norm]

    return raw.upper()


def get_all_rule_definitions() -> List[Dict[str, Any]]:
    """Returns a list of all indexed canonical rule definitions in the knowledge base."""
    return list(RULE_DEFINITIONS.values())


def get_all_rule_codes() -> List[str]:
    """Returns a list of all canonical rule codes in the knowledge base."""
    return list(RULE_DEFINITIONS.keys())


def _safe_float(val: Any) -> Optional[float]:
    """Safely convert numeric value or numeric string to float, filtering NaN and Inf."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def get_rule_explanation(
    rule_code: Any,
    value: Optional[Union[float, int, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    metric_value: Optional[Union[float, int, str]] = None,
) -> Dict[str, Any]:
    """Retrieves full mathematical and plain-English explanation for a given rule code.
    
    Supports dynamic metric interpolation using either scalar value/metric_value
    or rich metadata/context dictionaries.

    Args:
        rule_code: Canonical rule code or alias (e.g. 'RULE_DMV_VELOCITY', 'PASS_THROUGH_CONDUIT').
        value: Optional metric value (e.g. dmv_score=85.0, amount=75000.0, z_score=3.2).
        metadata: Optional dictionary with rule details, points, payer/payee context.
        context: Alias for metadata (supports both calling conventions).
        metric_value: Alias for value (supports both calling conventions).

    Returns:
        Dictionary containing canonical code, name, formulas, plain-English explanation,
        and dynamic contextual narrative.
    """
    raw_input = "" if rule_code is None else str(rule_code)
    canonical = normalize_rule_code(rule_code)
    
    # Merge context / metadata dictionaries
    ctx: Dict[str, Any] = {}
    if metadata and isinstance(metadata, dict):
        ctx.update(metadata)
    if context and isinstance(context, dict):
        ctx.update(context)

    # Resolve metric value from either parameter or context dict
    val_candidate = metric_value if metric_value is not None else value
    definition = RULE_DEFINITIONS.get(canonical)

    if definition is None:
        # Graceful fallback for custom or unindexed rule codes
        clean_name = raw_input.replace("_", " ").title() if raw_input else "Unknown Heuristic Rule"
        pts = ctx.get("points") or ctx.get("default_points") or 10
        severity = ctx.get("severity") or "INFO"
        return {
            "rule_code": canonical,
            "raw_code": raw_input,
            "name": clean_name,
            "layer": ctx.get("layer", 1),
            "severity": severity,
            "points": pts,
            "default_points": pts,
            "category": "CUSTOM",
            "mathematical_definition": "Deterministic custom heuristic condition evaluated to TRUE.",
            "plain_english_explanation": ctx.get("detail") or f"Detection condition '{clean_name}' was triggered during transaction evaluation.",
            "contextual_narrative": ctx.get("detail") or f"Rule '{canonical}' fired on the evaluated case.",
            "recommended_action": "Review account transaction history and assess counterparty relationship.",
            "regulatory_typology": "Custom Heuristic Anomaly (Internal Compliance Policy)",
            "detection_mechanism": "Custom heuristic evaluation rule.",
            "typical_threshold": "Rule condition threshold met.",
        }

    # Base plain-English explanation from definition
    base_explanation = definition["plain_english_explanation"]
    narrative_parts: List[str] = [base_explanation]

    # Dynamic Metric Interpolation
    f_val = _safe_float(val_candidate)
    
    if canonical == "DMV_RAPID_DRAIN":
        score = f_val if f_val is not None else _safe_float(ctx.get("dmv_score"))
        if score is not None:
            severity_label = "CRITICAL" if score >= 70.0 else ("ELEVATED" if score >= 40.0 else "NORMAL")
            narrative_parts.append(
                f"Evaluated Metric: DMV Score = {score:.1f}/100 ({severity_label} velocity drain)."
            )
    elif canonical == "BEHAVIORAL_ANOMALY":
        score = f_val if f_val is not None else _safe_float(ctx.get("adaptive_score"))
        if score is not None:
            z_score = ctx.get("z_score")
            z_str = f" (Z-score: {z_score}σ above baseline)" if z_score is not None else ""
            narrative_parts.append(f"Evaluated Metric: Anomaly Score = {score:.2f}/1.00{z_str}.")
    elif canonical == "LIMIT_SKIRTING":
        amt = f_val if f_val is not None else _safe_float(ctx.get("amount"))
        threshold = _safe_float(ctx.get("threshold")) or 50000.0
        if amt is not None:
            narrative_parts.append(
                f"Evaluated Metric: Amount ₹{amt:,.2f} sits just under the ₹{threshold:,.0f} regulatory caution threshold."
            )
    elif canonical == "NEW_ACCOUNT_HIGH_VALUE":
        amt = f_val if f_val is not None else _safe_float(ctx.get("amount"))
        age = ctx.get("age_days") or ctx.get("payer_account_age_days")
        age_str = f"on a fresh {age}-day-old account" if age is not None else "on a new account"
        if amt is not None:
            narrative_parts.append(f"Evaluated Metric: Outbound transfer of ₹{amt:,.2f} {age_str}.")
    elif canonical == "PASS_THROUGH_CONDUIT":
        ratio = _safe_float(ctx.get("ratio"))
        inflow = _safe_float(ctx.get("inflow"))
        outflow = _safe_float(ctx.get("outflow"))
        if ratio is not None or (inflow and outflow):
            r_val = ratio if ratio is not None else (outflow / inflow if inflow else 0.9)
            r_pct = f"{r_val * 100:.1f}%" if r_val <= 1.0 else f"{r_val:.1f}%"
            win = ctx.get("window_minutes") or 60
            in_str = f"of ₹{inflow:,.0f} incoming funds" if inflow else "of incoming funds"
            narrative_parts.append(f"Evaluated Metric: Forwarded {r_pct} {in_str} within {win} minutes.")
    elif canonical == "R_IMPOSSIBLE_TRAVEL":
        speed = _safe_float(ctx.get("speed_kmh"))
        dist = _safe_float(ctx.get("distance_km"))
        mins = _safe_float(ctx.get("time_minutes")) or _safe_float(ctx.get("delta_mins"))
        from_c = ctx.get("from_city")
        to_c = ctx.get("to_city")
        loc_str = f" between '{from_c}' and '{to_c}'" if (from_c and to_c) else ""
        if speed is not None:
            dist_str = f" over {dist:,.0f} km" if dist is not None else ""
            mins_str = f" in {mins:.1f} min" if mins is not None else ""
            narrative_parts.append(
                f"Evaluated Metric: Travel speed: {speed:,.1f} km/h{dist_str}{mins_str}{loc_str} (exceeds physical limit)."
            )
    elif canonical == "R_HONEYPOT_HIT":
        trap = val_candidate if isinstance(val_candidate, str) else ctx.get("payee_vpa")
        if trap:
            narrative_parts.append(f"Evaluated Metric: Transaction directed to seeded honeypot decoy '{trap}'.")
    elif canonical == "R_SIM_DEVICE_MISMATCH":
        dev = ctx.get("device_id") or ctx.get("device")
        sim = ctx.get("sim_id") or ctx.get("sim")
        if dev or sim:
            narrative_parts.append(f"Evaluated Metric: Hardware mismatch (Device: {dev or 'N/A'}, SIM: {sim or 'N/A'}).")
    elif val_candidate is not None and not (isinstance(val_candidate, float) and (math.isnan(val_candidate) or math.isinf(val_candidate))):
        narrative_parts.append(f"Evaluated Metric: {val_candidate}.")

    detail = ctx.get("detail")
    if detail:
        narrative_parts.append(f"Case Observation: {detail}")

    payer = ctx.get("payer_vpa")
    payee = ctx.get("payee_vpa")
    if payer and payee:
        narrative_parts.append(f"Entities: Payer '{payer}' ➔ Payee '{payee}'.")

    contextual_narrative = " ".join(narrative_parts)

    points_val = ctx.get("points")
    if points_val is None:
        points_val = definition["points"]

    return {
        "rule_code": canonical,
        "raw_code": raw_input,
        "name": definition["name"],
        "layer": definition["layer"],
        "severity": definition["severity"],
        "points": points_val,
        "default_points": definition["default_points"],
        "category": definition["category"],
        "mathematical_definition": definition["mathematical_definition"],
        "plain_english_explanation": contextual_narrative,
        "contextual_narrative": contextual_narrative,
        "recommended_action": definition["recommended_action"],
        "regulatory_typology": definition["regulatory_typology"],
        "detection_mechanism": definition["detection_mechanism"],
        "typical_threshold": definition["typical_threshold"],
    }


def build_case_encyclopedia_context(
    evaluated_rules: Optional[List[Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """Builds formatted markdown knowledge base context for system prompt injection.
    
    Generates a high-density Tier-1 summary table followed by numbered Tier-2
    algorithmic breakdowns detailing formulas, evaluated metrics, forensic typologies,
    and recommended compliance actions.

    Args:
        evaluated_rules: List of rule codes (str), dicts ({'code': '...', 'points': ...}),
                         or RuleHit objects.
        metrics: Optional dictionary containing runtime evaluation metrics
                 (e.g. {'dmv_score': 82.5, 'adaptive_score': 0.92, 'amount': 75000, ...}).

    Returns:
        Structured Markdown context block suitable for direct injection into Gemini Assistant prompt.
    """
    evaluated_rules = evaluated_rules or []
    metrics = metrics or {}

    lines: List[str] = [
        "### 📚 SAMPATI ENCYCLOPEDIA ALGORITHMIC KNOWLEDGE BASE",
        "The following algorithmic detection rules, mathematical thresholds, and forensic typologies were evaluated for this case:\n"
    ]

    # Process and deduplicate evaluated rules
    seen_canonical: Set[str] = set()
    table_rows: List[str] = []
    deep_sections: List[str] = []
    rule_idx = 1

    for item in evaluated_rules:
        if not item:
            continue

        raw_code = ""
        points = None
        detail = ""
        val = None
        item_ctx: Dict[str, Any] = {}

        if isinstance(item, str):
            raw_code = item
        elif isinstance(item, dict):
            raw_code = item.get("code") or item.get("rule_name") or item.get("rule_id") or ""
            points = item.get("points")
            detail = item.get("detail", "")
            val = item.get("value") or item.get("metric_value")
            item_ctx.update(item)
        elif hasattr(item, "code"):
            raw_code = getattr(item, "code", "")
            points = getattr(item, "points", None)
            detail = getattr(item, "detail", "")
            if hasattr(item, "__dict__"):
                item_ctx.update(item.__dict__)

        if not raw_code:
            continue

        canonical = normalize_rule_code(raw_code)
        if canonical in seen_canonical:
            continue
        seen_canonical.add(canonical)

        # Merge case metrics
        merged_ctx = {**metrics, **item_ctx}
        if detail:
            merged_ctx["detail"] = detail
        if points is not None:
            merged_ctx["points"] = points

        # Resolve metric value from metrics dict if not already passed
        if val is None:
            if canonical == "DMV_RAPID_DRAIN":
                val = metrics.get("dmv_score")
            elif canonical == "BEHAVIORAL_ANOMALY":
                val = metrics.get("adaptive_score")
            elif canonical == "FEDERATED_MULE_NETWORK":
                val = metrics.get("network_score")
            elif canonical == "LIMIT_SKIRTING":
                val = metrics.get("amount")
            elif canonical == "NEW_ACCOUNT_HIGH_VALUE":
                val = metrics.get("amount")

        exp = get_rule_explanation(
            rule_code=raw_code,
            value=val,
            metadata=merged_ctx,
            context=merged_ctx,
        )

        # Build Tier-1 summary row
        metric_summary = ""
        if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            if canonical == "DMV_RAPID_DRAIN":
                metric_summary = f"`{val:.1f}/100`"
            elif canonical == "BEHAVIORAL_ANOMALY":
                metric_summary = f"`{val:.2f}/1.00`"
            elif canonical in ("LIMIT_SKIRTING", "NEW_ACCOUNT_HIGH_VALUE"):
                metric_summary = f"₹{float(val):,.2f}"
            else:
                metric_summary = f"`{val}`"
        elif detail:
            metric_summary = detail[:40] + ("..." if len(detail) > 40 else "")
        else:
            metric_summary = "Threshold Met"

        pts_str = f" ({exp['points']} pts)" if exp.get("points") else ""
        sev_str = f"{exp['severity']}{pts_str}"
        summary_blurb = exp["plain_english_explanation"].split(".")[0]

        table_rows.append(
            f"| `{exp['rule_code']}` | {exp['name']} | {metric_summary} | {sev_str} | {summary_blurb} |"
        )

        # Build Tier-2 deep section
        section = (
            f"#### {rule_idx}. `{exp['rule_code']}` — {exp['name']}\n"
            f"- **Mathematical Formula**: \n```\n{exp['mathematical_definition']}\n```\n"
            f"- **Forensic Rationale**: {exp['plain_english_explanation']}\n"
            f"- **Regulatory Typology**: {exp['regulatory_typology']}\n"
            f"- **Recommended Compliance Action**: {exp['recommended_action']}"
        )
        deep_sections.append(section)
        rule_idx += 1

    # Check if DMV is in metrics and not already rendered
    dmv_score = metrics.get("dmv_score")
    if dmv_score is not None and "DMV_RAPID_DRAIN" not in seen_canonical:
        f_dmv = _safe_float(dmv_score)
        if f_dmv is not None:
            exp_dmv = get_rule_explanation("DMV_RAPID_DRAIN", value=f_dmv, metadata=metrics)
            sev_label = "CRITICAL (35 pts)" if f_dmv >= 70 else ("HIGH (20 pts)" if f_dmv >= 40 else "NORMAL (0 pts)")
            table_rows.append(
                f"| `DMV_RAPID_DRAIN` | Dead Money Velocity | `{f_dmv:.1f}/100` | {sev_label} | Post-dormancy balance acceleration metric |"
            )
            section = (
                f"#### {rule_idx}. `DMV_RAPID_DRAIN` — Dead Money Velocity (DMV) Analysis\n"
                f"- **Evaluated Score**: **{f_dmv:.1f}/100** ({'CRITICAL' if f_dmv >= 70 else ('ELEVATED' if f_dmv >= 40 else 'NORMAL')})\n"
                f"- **Mathematical Formula**: \n```\n{exp_dmv['mathematical_definition']}\n```\n"
                f"- **Forensic Rationale**: {exp_dmv['plain_english_explanation']}\n"
                f"- **Regulatory Typology**: {exp_dmv['regulatory_typology']}\n"
                f"- **Recommended Compliance Action**: {exp_dmv['recommended_action']}"
            )
            deep_sections.append(section)
            seen_canonical.add("DMV_RAPID_DRAIN")
            rule_idx += 1

    if not table_rows:
        lines.append(
            "- No specific high-risk deterministic rules triggered. "
            "Transaction evaluated within baseline parameters across standard velocity, device, and network checks."
        )
        return "\n\n".join(lines)

    # Output Tier 1 Table
    lines.append("| Rule Code | Rule Name | Evaluated Metric | Severity | Detection Summary |")
    lines.append("|---|---|---|---|---|")
    lines.extend(table_rows)
    lines.append("\n---")
    lines.extend(deep_sections)

    return "\n\n".join(lines)


def search_encyclopedia(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Searches the knowledge base for rules and algorithmic concepts matching a free-text query.
    
    Ranks results based on relevance scoring:
    - Exact canonical code or alias match: 100 points
    - Name match: 50 points
    - Keyword match: 30 points
    - Category match: 20 points
    - Description/formula text match: 10 points

    Args:
        query: Search string (e.g. 'dead money', 'sim swap', 'gini', 'pass through').
        limit: Maximum number of ranked results to return.

    Returns:
        List of matching canonical rule definitions sorted descending by relevance score.
    """
    if not query or not isinstance(query, str):
        return []

    q_clean = query.lower().strip()
    q_tokens = set(re.findall(r"\b[a-z0-9_]+\b", q_clean))
    if not q_tokens:
        return []

    scored_results: List[Tuple[float, Dict[str, Any]]] = []

    for defn in RULE_DEFINITIONS.values():
        score = 0.0
        code_clean = defn["canonical_code"].lower()
        name_clean = defn["name"].lower()
        category_clean = defn["category"].lower()
        keywords = set(k.lower() for k in defn.get("keywords", []))
        desc_clean = (
            defn["plain_english_explanation"] + " " +
            defn["mathematical_definition"] + " " +
            defn["recommended_action"] + " " +
            defn.get("regulatory_typology", "")
        ).lower()

        # 1. Exact canonical or alias match
        if q_clean == code_clean or any(q_clean == a.lower() for a in defn.get("aliases", [])):
            score += 100.0

        # 2. Token overlap
        for t in q_tokens:
            if t == code_clean or t in code_clean:
                score += 40.0
            if t in name_clean:
                score += 30.0
            if t in keywords:
                score += 25.0
            if t in category_clean:
                score += 20.0
            if t in desc_clean:
                score += 10.0

        if score > 0.0:
            scored_results.append((score, defn))

    # Sort descending by relevance score
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_results[:limit]]
