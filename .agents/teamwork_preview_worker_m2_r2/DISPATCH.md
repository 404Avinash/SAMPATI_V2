# Dispatch: teamwork_preview_worker_m2_r2

## Mission
Implement Milestone 2 (R2): Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP) & Frontend Dashboard Integration for SAMPATI V2.

## Working Directory
`/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2_r2/`

## Mandatory Reading Before Starting Work
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read request under 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r2/handoff.md`

## Exclusive Write Ownership
- `app/models/threat_intel.py` (add `StandardFraudSignal`)
- `app/models/upi_models.py` (add `mock_npci_score`, `mock_dpip_threat_level`, `contributing_signals` to `UpiEvaluationResponse`)
- `app/adapters/` (new package: `__init__.py`, `npci.py`, `dpip.py`, `psp.py`, `service.py`)
- `app/services/upi_cases.py` (populate institutional scores in `evaluate()`)
- `app/api/adapters.py` (new router for adapter endpoints)
- `app/main.py` (mount `adapters.router` at `/adapters` and `/upi/adapters`)
- `frontend/src/components/CaseDrawer.jsx` (display institutional contributing signals)
- `frontend/src/pages/ThreatIntelPage.jsx` (institutional badges & presets)
- `frontend/src/components/LiveFeed.jsx` (institutional pill tags)
- `frontend/src/services/api.js` (adapter API wrappers)
- `tests/test_institutional_adapters.py` (new tests)

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Requirements & Implementation Blueprint
Follow the detailed blueprint in `.agents/teamwork_preview_explorer_survey_r2/handoff.md`:
1. `app/models/threat_intel.py`:
   - Define `StandardFraudSignal(ThreatSignalCreateRequest)` with helper constructor/classmethods.
2. `app/adapters/npci.py`:
   - Implement `NpciMuleHunterAdapter`: returns `NpciMuleHunterResponse` with `mule_probability`, `risk_rating`, `central_switch_flags`, etc.
   - Deterministic mapping: Honeypots (`is_honeypot(vpa)`) and known-bad VPAs return `mule_probability = 0.96`, `risk_rating = "HIGH"`. Clean VPAs return hash-based low score (< 0.15), `risk_rating = "LOW"`.
3. `app/adapters/dpip.py`:
   - Implement `DpipSmartRegistryAdapter`: Query by VPA or SHA-256 hash. Returns `DpipRegistryRecord` with `threat_level` ("HIGH", "CLEAN", etc.), `threat_score` (0.90 for bad, 0.0 for clean), `listed` (bool), etc.
   - Support `update_registry(req: DpipRegistryUpdateRequest)` to add/update entries by VPA or hash.
4. `app/adapters/psp.py`:
   - Implement `MockPspAdapter`: generate signals (`velocity_anomaly`, `suspicious_beneficiary`, etc.) as `StandardFraudSignal` for PhonePe, Paytm, GooglePay, BHIM.
   - Support `publish_to_mesh()` via `ThreatIntelService.ingest_signal()`.
5. `app/adapters/service.py`:
   - Implement `InstitutionalAdapterService`: singleton `get_institutional_adapters()`.
   - Method `evaluate_for_transaction(txn: UpiTransaction) -> Dict[str, Any]` returning `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals` (list of signal dicts with `institution`, `score`, `risk_rating`, `summary`).
6. `app/models/upi_models.py`:
   - Add fields to `UpiEvaluationResponse`:
     - `mock_npci_score: float = Field(default=0.0, description="Simulated NPCI MuleHunter mule-probability score in [0.0, 1.0]")`
     - `mock_dpip_threat_level: Union[float, int, str] = Field(default=0.0, description="Simulated DPIP Smart Registry threat level score")`
     - `contributing_signals: List[Dict[str, Any]] = Field(default_factory=list, description="Contributing institutional signal sources with institution labels")`
7. `app/services/upi_cases.py`:
   - In `evaluate(txn)`, call `get_institutional_adapters().evaluate_for_transaction(txn)` and populate `resp.mock_npci_score`, `resp.mock_dpip_threat_level`, and `resp.contributing_signals`.
   - Ensure for honeypot or known-bad payee VPA, `resp.mock_npci_score >= 0.85` and `resp.mock_dpip_threat_level >= 0.85`.
8. `app/api/adapters.py` & `app/main.py`:
   - Expose endpoints: `GET /adapters/npci/mulehunter`, `GET /adapters/dpip/registry`, `POST /adapters/dpip/registry`, `POST /adapters/psp/simulate`, `GET /adapters/signals/contributing`. Mount at `/adapters` and `/upi/adapters`.
9. Frontend Integration:
   - `CaseDrawer.jsx`: Add "Institutional Contributing Signals" card rendering NPCI MuleHunter, DPIP Smart Registry, and PSP tags with institution labels.
   - `ThreatIntelPage.jsx`: Add branded institution badges (`[NPCI]`, `[DPIP]`, `[PhonePe]`, `[Paytm]`) and presets.
   - `LiveFeed.jsx`: Display institutional pill tags (`[NPCI]`, `[DPIP]`) in Signals column when `c.mock_npci_score > 0` or `c.mock_dpip_threat_level > 0`.
   - `frontend/src/services/api.js`: Add API methods for querying/updating adapters.
10. Tests in `tests/test_institutional_adapters.py`:
   - Unit tests for NPCI MuleHunter, DPIP Smart Registry (query by VPA and hash, update registry), and PSP adapter.
   - Test `/upi/check` returns non-zero `mock_npci_score` and `mock_dpip_threat_level` for honeypots / known-bad VPAs, and zero/low for clean VPAs.
   - Verify all 923+ existing tests pass.
   - Verify `ruff check app tests` passes cleanly.
   - Verify `cd frontend && npm run lint && npm run build` passes cleanly.

Write completion report to `handoff.md` and communicate via `send_message`.

## 2026-09-04T03:21:27Z
User Request received for teamwork_preview_worker_m2_r2: Implement Milestone 2 (R2): Simulated Institutional Signal Adapters (Mock NPCI MuleHunter, Mock DPIP Smart Registry, Mock PSP) & Frontend Dashboard Integration.

