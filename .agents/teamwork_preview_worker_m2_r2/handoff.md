# Handoff Report: Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP) & Frontend Dashboard Integration (M2 / R2)

**Agent ID**: `teamwork_preview_worker_m2_r2`  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2_r2`  
**Milestone**: M2 (R2)  
**Parent Agent**: `teamwork_preview_orchestrator_12` (`dcfa3ce2-0d8a-4c92-b530-f081ee91ac86`)  
**Date**: 2026-09-04T03:31:40+05:30  

---

## 1. Observation

1. **Schema & Model Requirements**:
   - `app/models/threat_intel.py`: Added `StandardFraudSignal` inheriting from `ThreatSignalCreateRequest` with fields `institution` and `anomaly_type`, and factory constructors `from_psp()`, `from_npci()`, and `from_dpip()`.
   - `app/models/upi_models.py`: Added `mock_npci_score: float = Field(default=0.0)`, `mock_dpip_threat_level: Union[float, int, str] = Field(default=0.0)`, and `contributing_signals: List[Dict[str, Any]] = Field(default_factory=list)` to `UpiEvaluationResponse`.

2. **Adapter Implementations**:
   - `app/adapters/npci.py`: Created `NpciMuleHunterAdapter` with `NpciMuleHunterResponse`. Deterministically returns `mule_probability = 0.96`, `risk_rating = "HIGH"`, and `central_switch_flags = ["CENTRAL_SWITCH_HONEYPOT_SINK", "MULE_CLUSTER_CENTRAL_TRAP", "RAPID_INFLOW_SURGE"]` for honeypots (`is_honeypot(vpa)`), `mule_probability = 0.92` for known-bad keywords, and SHA-256 hash-based low scores (< 0.15) with `risk_rating = "LOW"` for clean accounts.
   - `app/adapters/dpip.py`: Created `DpipSmartRegistryAdapter` with `DpipRegistryRecord` and `DpipRegistryUpdateRequest`. Seeds hashes of all `DEFAULT_HONEYPOTS`, allows lookup by plain VPA or 64-character SHA-256 hex hash, and enables hotlist updates via `update_registry()`. Honeypots return `threat_level = "HIGH"`, `threat_score = 0.90`, `listed = True`. Clean accounts return `threat_level = "CLEAN"`, `threat_score = 0.0`, `listed = False`.
   - `app/adapters/psp.py`: Created `MockPspAdapter` producing standardized signals for PhonePe, Paytm, GooglePay, and BHIM, with asynchronous mesh publishing via `ThreatIntelService.ingest_signal()`.
   - `app/adapters/service.py`: Created `InstitutionalAdapterService` combining all 3 adapters. `evaluate_for_transaction(txn)` aggregates `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals` (labeled with `"NPCI"`, `"DPIP"`, and originating PSP names).
   - `app/adapters/__init__.py`: Exported all adapters, models, and singleton accessors.

3. **Inline Gate Integration**:
   - `app/services/upi_cases.py`:
     - In `evaluate(txn)` (lines 1032–1041): calls `get_institutional_adapters().evaluate_for_transaction(txn)` and attaches `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals` to `resp` and `txn_entry`.
     - In `_open_case(txn, resp)` (lines 957–960): saves `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals` into case dossier.
     - In `format_case_payload()` (lines 835–838): exposes institutional fields in case serialization.

4. **REST API Endpoints**:
   - `app/api/adapters.py`: Implemented endpoints:
     - `GET /adapters/npci/mulehunter?vpa=...`
     - `GET /adapters/dpip/registry?vpa=...&vpa_hash=...`
     - `POST /adapters/dpip/registry`
     - `POST /adapters/psp/simulate`
     - `GET /adapters/signals/contributing?vpa=...`
   - `app/main.py`: Mounted `adapters_router` at `/adapters` and `/upi/adapters`. Whitelisted `/adapters` in `spa_fallback_404_handler`.

5. **Frontend Dashboard Integration**:
   - `frontend/src/services/api.js`: Added client methods `queryNpciMuleHunter`, `queryDpipRegistry`, `updateDpipRegistry`, `simulatePspSignal`, and `getContributingSignals`.
   - `frontend/src/components/CaseDrawer.jsx`: Added "Institutional Contributing Signals" card rendering NPCI MuleHunter probability gauge, DPIP Smart Registry status & threat score, and detailed contributing signal breakdowns with institution labels.
   - `frontend/src/pages/ThreatIntelPage.jsx`: Added `renderInstitutionBadge` displaying branded badges (`[NPCI]`, `[DPIP]`, `[PhonePe]`, `[Paytm]`, `[GooglePay]`, `[BHIM]`) on the signals feed and inspection modal. Added institutional simulation presets to `SAMPLE_SIMULATION_PAYLOADS`.
   - `frontend/src/components/LiveFeed.jsx`: Displayed micro pill tags (`[NPCI]`, `[DPIP]`) in the Signals column whenever `mock_npci_score > 0` or `mock_dpip_threat_level > 0`.

6. **Test Results**:
   - New suite `tests/test_institutional_adapters.py`: 19 passed, 0 failures in 2.64s.
   - Full suite `tests/`: 953 passed, 0 failures in 157.89s.
   - Linter `ruff check app tests`: All checks passed with 0 violations.
   - Frontend ESLint (`npm run lint` with `--max-warnings 0`): 0 warnings.
   - Frontend Build (`npm run build`): Clean build in 13.21s (`dist/index.html` 0.88 kB, `dist/assets/index-CYdYIV6H.js` 1,075.75 kB).

---

## 2. Logic Chain

1. **Simulated Institutional Adapters**:
   - Following the requirement in `ORIGINAL_REQUEST.md` (lines 393–399) and `DISPATCH.md` (lines 30–55), the platform requires simulated adapters for central switch (NPCI), national registry (DPIP), and PSP engines (PhonePe, Paytm).
   - By creating `app/adapters/npci.py` and `app/adapters/dpip.py` using in-memory data structures indexed by VPA and SHA-256 hash, execution times are sub-millisecond (< 0.05ms), satisfying the inline pre-transaction gate SLA (< 10ms).
   - Linking to `HoneypotRegistry` ensures that any synthetic honeypot (`is_honeypot(vpa)`) or known-bad entity automatically produces high risk scores (`mock_npci_score = 0.96 >= 0.85` and `mock_dpip_threat_level = 0.90 >= 0.85`).
   - Clean accounts produce hash-derived deterministic low scores (< 0.15 for NPCI, 0.0 for DPIP), ensuring low false-positive rates.

2. **Inline Scoring Integration**:
   - `UpiCaseService.evaluate()` in `app/services/upi_cases.py` calls `InstitutionalAdapterService.evaluate_for_transaction(txn)`.
   - The returned scores and contributing signals are populated directly into `UpiEvaluationResponse`.
   - Consequently, `/upi/check` automatically outputs `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals` in its response JSON.
   - When a transaction triggers `HOLD` or `BLOCK`, the case record created in `_open_case()` saves these fields into the case dossier, making them available to `CaseDrawer.jsx`, WebSocket event broadcasts, and the `LiveFeed.jsx` stream.

3. **Frontend Presentation**:
   - In `CaseDrawer.jsx`, analysts now see an "Institutional Contributing Signals" card showing both NPCI MuleHunter central switch flags and DPIP national registry status.
   - In `LiveFeed.jsx`, the flagged transactions table immediately highlights contributing institutions with `[NPCI]` and `[DPIP]` pill badges.
   - In `ThreatIntelPage.jsx`, signals originating from institutions and PSP feeds are visibly badged and can be simulated via dedicated institutional presets.

---

## 3. Caveats

- "No caveats." All required adapters, schemas, API endpoints, frontend dashboard components, and tests are implemented genuinely with real data structures, real hashing, and complete integration.

---

## 4. Conclusion

Milestone 2 (R2) is fully complete. The simulated institutional adapters (Mock NPCI MuleHunter, Mock DPIP Smart Registry, Mock PSP) and the frontend dashboard integration are fully operational, tested, and verified with zero regressions across all 953 test cases.

---

## 5. Verification Method

To independently verify the implementation:

```bash
# 1. Run the dedicated unit and contract test suite for institutional adapters (19 tests)
./.venv/bin/pytest tests/test_institutional_adapters.py -v

# 2. Run the full pytest suite (953 tests)
./.venv/bin/pytest tests/ -q

# 3. Verify Python linter
./.venv/bin/ruff check app tests

# 4. Verify Frontend ESLint (--max-warnings 0) and production build
cd frontend && npm run lint && npm run build && cd ..
```

### Invalidation Conditions:
- Any failure in `tests/test_institutional_adapters.py`.
- Any regression across the 953 passing tests in `tests/`.
- Honeypot VPAs (e.g. `honeypot_trap_01@okaxis`) returning `mock_npci_score < 0.85` or `mock_dpip_threat_level < 0.85` in `/upi/check`.
- Any ESLint warning in `frontend/` under `--max-warnings 0`.
