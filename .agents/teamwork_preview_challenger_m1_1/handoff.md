# Handoff Report: Milestone 1 — Adversarial Empirical Verification (Threat Intelligence Layer R1)

**Author**: Empirical Challenger 1 (`teamwork_preview_challenger_m1_1`)  
**Recipient**: Parent Orchestrator (`teamwork_preview_orchestrator_11` / `93ffe563-3fed-400b-b381-966248be98c4`)  
**Milestone**: Milestone 1 (Backend Early Warning Threat Intelligence Layer, R1)  
**Date**: 2026-09-03  
**Verdict**: **REJECT** (4 concrete empirical failures reproduced, including graph entity pollution and service crashes)  
**Handoff Type**: Hard  

---

## 1. Observation

### 1.1 Empirical Test Suite Execution
- **Test File**: `/home/avi/Downloads/Sampati_v2/tests/test_threat_intel_adversarial_challenger.py`
- **Execution Command**:
  ```bash
  ./.venv/bin/python -m pytest tests/test_threat_intel_adversarial_challenger.py -v -s
  ```
- **Output Summary**:
  ```text
  FAILED tests/test_threat_intel_adversarial_challenger.py::TestRegexAdversarialBoundaries::test_dirty_and_obfuscated_urls
  FAILED tests/test_threat_intel_adversarial_challenger.py::TestRegexAdversarialBoundaries::test_email_subdomain_and_tld_boundary_cases
  FAILED tests/test_threat_intel_adversarial_challenger.py::TestFraudGraphServicePressure::test_get_subgraph_none_entity_id_handling
  FAILED tests/test_threat_intel_adversarial_challenger.py::TestCampaignSimilarityEdgeCases::test_non_string_tags_graceful_handling
  ========================= 4 failed, 13 passed in 3.25s =========================
  ```

### 1.2 Verbatim Failure Traces & Concrete Reproductions

#### Failure 1: URL Extraction Captures Trailing Markdown & Parentheses into Malicious Graph Entities
- **File**: `app/models/threat_intel.py`, lines 46–50 (`URL_REGEX`) and line 116 (`extract_entities`).
- **Verbatim Failure**:
  ```text
  AssertionError: True is not false : URL contains trailing markdown parenthesis: https://sbi-kyc-update.com/login)
  ```
- **Direct Reproduction**:
  ```python
  from app.models.threat_intel import extract_entities
  res = extract_entities("Click [here](https://sbi-kyc-update.com/login) to unblock account.")
  print(res.urls)
  # Output: ['https://sbi-kyc-update.com/login)']

  res2 = extract_entities("Visit (https://sbi.co.in/login).")
  print(res2.urls)
  # Output: ['https://sbi.co.in/login)']
  ```
- **Direct Cause**:
  `URL_REGEX` excludes characters `[^\s<>\"'{}|\\^`\[\]]*`, omitting `)` from exclusions. In addition, line 116 only does `u = m.group(1).rstrip(".,;:!?")`, leaving the closing parenthesis attached. When ingested, this injects corrupted node IDs (`URL:https://sbi-kyc-update.com/login)`) into the Central Fraud Graph.

#### Failure 2: Enterprise & Subdomain Emails Truncated into Fake UPI Payment VPAs
- **File**: `app/models/threat_intel.py`, lines 37–40 (`UPI_REGEX`).
- **Verbatim Failure**:
  ```text
  AssertionError: 'user@support' unexpectedly found in ['user@support'] : Subdomain email was falsely extracted as UPI VPA: ['user@support']
  ```
- **Direct Reproduction**:
  ```python
  from app.models.threat_intel import extract_entities
  res = extract_entities("Emails: alex@mail.google.com and support@alerts.hdfcbank.com and user@support.example.com")
  print(res.upi_ids)
  # Output: ['alex@mail', 'support@alerts', 'user@support']
  ```
- **Direct Cause**:
  In `UPI_REGEX`:
  ```python
  r"\b([a-zA-Z0-9.\-_]{2,64}@(?!(?:gmail|yahoo|outlook|hotmail|proton|icloud|mail)\.com\b)(?![a-zA-Z0-9_\-]+\.(?:com|in|co\.in|org|net|edu|gov)\b)[a-zA-Z][a-zA-Z0-9_\-]{1,32})\b"
  ```
  The negative lookahead asserts that the handle is not followed by `[a-zA-Z0-9_\-]+\.(?:com|in...)`. When an email contains subdomains (e.g. `mail.google.com` or `alerts.hdfcbank.com`), the second segment is not a top-level domain, so the lookahead succeeds. The handle pattern `[a-zA-Z][a-zA-Z0-9_\-]{1,32}` matches up to the first dot, extracting `alex@mail` and `support@alerts` as payment VPAs. Real UPI handles never have subdomain structures.

#### Failure 3: Unhandled `AttributeError` in `FraudGraphService.get_subgraph(None)`
- **File**: `app/services/graph_service.py`, line 75 in `_resolve_node_id`.
- **Verbatim Failure**:
  ```text
  AttributeError: 'NoneType' object has no attribute 'lower'
  at candidate_lower = f"{p}{entity_id.lower().strip()}"
  ```
- **Direct Reproduction**:
  ```python
  from app.services.graph_service import get_fraud_graph
  g = get_fraud_graph()
  g.get_subgraph(None)
  # Raises: AttributeError: 'NoneType' object has no attribute 'lower'
  ```
- **Direct Cause**:
  `_resolve_node_id` lacks a guard for `None` or non-string inputs before calling `entity_id.lower().strip()`.

#### Failure 4: Unhandled `TypeError` in `compute_campaign_similarity` on Non-String Tags
- **File**: `app/services/threat_intel_service.py`, line 80 in `compute_campaign_similarity`.
- **Verbatim Failure**:
  ```text
  TypeError: sequence item 0: expected str instance, NoneType found
  at tag_str = " ".join(tags).lower()
  ```
- **Direct Reproduction**:
  ```python
  from app.services.threat_intel_service import get_threat_intel_service
  svc = get_threat_intel_service()
  svc.compute_campaign_similarity(tags=[None, 123])
  # Raises: TypeError: sequence item 0: expected str instance, NoneType found
  ```
- **Direct Cause**:
  Line 80 executes `" ".join(tags).lower()` without filtering out non-string items or `None` values, causing internal callers (or direct dictionary ingestion) to crash.

### 1.3 High-Robustness Empirical Observations (Passed Benchmarks)
- **High-Frequency Concurrency on `FraudGraphService`**:
  - 8 worker threads executing 400 operations (signals, transactions, subgraph queries, stats) completed in **1.45s** with **0 deadlocks and 0 race conditions**.
  - Stress test with 16 threads executing 1600 operations created **8,001 nodes and 11,200 edges in 16.29s** cleanly.
- **Topological Cycles & Self-Loops**:
  - Self-loops (`VPA:A -> VPA:A`) and 3-node cycles (`VPA:A -> VPA:B -> VPA:C -> VPA:A`) executed with 100% graph integrity; `nx.ego_graph` terminated cleanly without infinite recursion or stack overflows.
- **12-Digit UPI UTRs & Timestamps**:
  - 12-digit numbers starting with 6, 7, 8, or 9 (e.g. `UTR 902182910291`, `876543210987`) were **never** truncated or matched as phone numbers.
  - Timestamps (`202609031234`) produced 0 false phone extractions.
- **Massive Payload Stability**:
  - 100,000-character payload processed in **0.0814s** entity extraction and **0.0069s** campaign similarity calculation with zero ReDoS or memory leakage.

---

## 2. Logic Chain

1. **Entity Extractor Ground Truth (Observation 1.2, Failures 1 & 2)**:
   - The Early Warning Intelligence Mesh relies on `extract_entities` to ingest raw SMS, chat messages, and reports, converting them into nodes in the `FraudGraphService` and records in PostgreSQL.
   - When URLs from markdown links `[link](https://...)` or parentheses are extracted as `https://...login)`, the graph registers corrupt vertices.
   - When corporate/banking email addresses (`support@alerts.hdfcbank.com`) are ingested, the system extracts `support@alerts` as a UPI VPA, polluting the Central Fraud Graph with phantom payment addresses and creating false linkage to innocent financial entities.

2. **Fault Tolerance of Core Graph & Intelligence Services (Observation 1.2, Failures 3 & 4)**:
   - In Python ASGI microservices, components interact both via external REST APIs and internal background tasks/service calls.
   - Calling `FraudGraphService.get_subgraph(None)` and `ThreatIntelService.compute_campaign_similarity(tags=[None])` generates unhandled `AttributeError` and `TypeError`. A resilient mesh service must handle null/corrupted attributes gracefully.

3. **Synthesis & Blast Radius**:
   - While the basic test suite (`tests/test_threat_intel_r1.py`) passes 30/30 on canonical inputs, the boundary collisions and dirty input vulnerabilities in `extract_entities` directly corrupt the central data model that Milestone 2 (Frontend Dashboard) will visualize.
   - Therefore, Milestone 1 cannot be approved in its current state.

---

## 3. Caveats

- **Zero-Width Spaces in Scam Text**:
  - Inserting zero-width spaces (`U\u200brgent`, `K\u200bY\u200bC`) bypasses keyword matching. This is noted as an evasion vector, but is treated as Low/Medium since full Unicode normalization is not strictly mandated by R1.
- **International Numbers**:
  - US numbers like `+1 650 123 4567` are extracted as `+916501234567` because the Indian phone regex does not inspect if a foreign `+` prefix precedes the space. This is noted as a Medium finding.
- **No Implementation Code Modified**:
  - In strict compliance with the Challenger role, no code in `app/` was altered. Only the test harness `tests/test_threat_intel_adversarial_challenger.py` was created to empirically verify behaviors.

---

## 4. Conclusion

### **VERDICT: REJECT**

Milestone 1 has solid architectural foundations (NetworkX `RLock` graph concurrency, clean schema structure, robust 12-digit UTR rejection, fast campaign similarity), but contains **4 concrete defects** that must be remediated:

### Required Remediations for Implementer

1. **Fix URL Trailing Parenthesis (`app/models/threat_intel.py`)**:
   - In `extract_entities`:
     ```python
     u = m.group(1).rstrip(".,;:!?)>\"'")
     ```
   - In `URL_REGEX`: Add `\(\)` to the character exclusions:
     ```python
     [^\s<>\"'{}|\\^`\[\]\(\)]*
     ```

2. **Fix Subdomain Email Collision in UPI Regex (`app/models/threat_intel.py`)**:
   - Real Indian UPI handles do not contain dots after `@` (e.g. `@oksbi`, `@okhdfcbank`, `@paytm`, `@ybl`).
   - In `UPI_REGEX`: Reject any handle that contains a dot or is followed by another domain segment:
     ```python
     UPI_REGEX = re.compile(
         r"\b([a-zA-Z0-9.\-_]{2,64}@(?!(?:gmail|yahoo|outlook|hotmail|proton|icloud|mail)\.com\b)(?![a-zA-Z0-9_\-]+\.[a-zA-Z0-9.\-]+\b)(?![a-zA-Z0-9_\-]+\.(?:com|in|co\.in|org|net|edu|gov)\b)[a-zA-Z][a-zA-Z0-9_\-]{1,32})\b",
         re.IGNORECASE,
     )
     ```
     Or ensure `(?![a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)` ensures that no trailing domain labels exist after the handle.

3. **Add Null-Safety Guard to `_resolve_node_id` (`app/services/graph_service.py`)**:
   - At the beginning of `_resolve_node_id`:
     ```python
     if not entity_id or not isinstance(entity_id, str):
         return None
     ```

4. **Add Type-Coercion Guard to `compute_campaign_similarity` (`app/services/threat_intel_service.py`)**:
   - At line 80:
     ```python
     tag_str = " ".join(str(t) for t in tags if t and isinstance(t, (str, int))).lower()
     ```

---

## 5. Verification Method

To reproduce the 4 failures independently:

```bash
# Run the adversarial challenge suite (currently reproduces the 4 failures)
./.venv/bin/python -m pytest tests/test_threat_intel_adversarial_challenger.py -v

# Run the baseline suite to confirm zero regressions
./.venv/bin/python -m pytest tests/test_threat_intel_r1.py -v

# Run linter
./.venv/bin/ruff check app tests
```

### Invalidation Conditions
This `REJECT` verdict is invalidated and will convert to **APPROVE** once:
1. All 4 failing tests in `tests/test_threat_intel_adversarial_challenger.py` pass cleanly (17 passed).
2. The 30 existing tests in `tests/test_threat_intel_r1.py` continue to pass.
3. `ruff check app tests` returns zero errors.
