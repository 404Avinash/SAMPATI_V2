# Handoff Report: Backend APIs, SAR PDF Export, Analytics Endpoints & Dependencies Survey

## 1. Observation

### 1.1 Codebase & File Structure Observations
- **FastAPI Main Entry (`app/main.py`)**:
  - `main.py` initializes the FastAPI application (`title="SAMPATI UPI Mule-Network Interception Gateway", version="2.0.0"`).
  - Routes mounted:
    - `/upi` via `upi_router.router` (`app/api/upi.py:157`)
    - `/federation` via `federation_router.router` (`app/api/federation.py:158`)
    - Optional legacy routers (`gateway`, `cases`, `synthetic`, `websocket`) (`app/main.py:159-166`)
    - Root endpoints directly in `main.py`:
      - `GET /health` (`app/main.py:169-188`)
      - `GET /health/detailed` (`app/main.py:191-197`)
      - `GET /stats/analytics` (`app/main.py:200-216`)
      - `PATCH /cases/{case_id}/status` (`app/main.py:219-241`)
      - `GET /api/info` (`app/main.py:243-249`)

- **UPI API Router (`app/api/upi.py`)**:
  - `POST /upi/check` (`app/api/upi.py:112`): Pre-transaction gate evaluating `UpiTransaction`, emits WebSocket `UPI_EVALUATED` and `UPI_CASE_OPENED` / `new_case`.
  - `POST /upi/federation/run` (`app/api/upi.py:153`): Runs federation round, saves detected rings & cases.
  - `GET /upi/rings` (`app/api/upi.py:183`): Returns cross-PSP mule rings.
  - `GET /upi/cases` (`app/api/upi.py:205`): Paginated and filtered case list.
  - `GET /upi/cases/{case_id}` (`app/api/upi.py:258`): Full case details including `sar_markdown` and `token_economy`.
  - `GET /upi/cases/{case_id}/graph.png` (`app/api/upi.py:281`): Returns PNG constellation artifact via `FileResponse(path, media_type="image/png")`.
  - `PATCH /upi/cases/{case_id}/status` (`app/api/upi.py:311`): Updates status (REVIEWED, ESCALATED, DISMISSED, OPEN).
  - `POST /upi/cases/{case_id}/feedback` (`app/api/upi.py:341`): Human analyst feedback loop.
  - `POST /upi/simulate` (`app/api/upi.py:381`): Drives synthetic stream through gate.
  - `GET /upi/stats` (`app/api/upi.py:453`): Real-time system counters.
  - `GET /upi/honeypots` (`app/api/upi.py:529`): Honeypot statistics.
  - `GET /upi/stats/analytics` (`app/api/upi.py:549`): Proxies `service.get_analytics()`.
  - `GET /upi/health/detailed` (`app/api/upi.py:568`): Proxies `service.get_detailed_health()`.

- **Core Case Service (`app/services/upi_cases.py`)**:
  - `UpiCaseService` singleton (`app/services/upi_cases.py:105-1353`).
  - Holds `self.state: UpiHotState`, `self.adaptive: AdaptiveBehaviorModel`, `self.scorer: UpiRiskScorer`, `self.federation: FederatedCoordinator`, `self.dpip: DpipFeed`.
  - `get_analytics()` (`app/services/upi_cases.py:311-570`): Aggregates summary KPIs (`total_evaluated`, `total_flagged`, `total_allowed`, `total_held`, `total_blocked`, `fraud_rate_pct`, `avg_risk_score`, `total_amount_protected`), time-series buckets (`hourly` / `daily`), rule frequencies (`rule_frequencies`), top flagged accounts (`top_flagged_accounts`), and bank distribution (`bank_distribution`).
  - Forensics Integration: Uses `generate_upi_sar`, `render_ring_png`, `build_upi_token_economy` from `app.forensics.upi_sar` (`app/services/upi_cases.py:32-36`).

- **Python Virtual Environment (`.venv`) Package Survey**:
  - Executed `./.venv/bin/pip list`:
    - `reportlab`: **NOT installed**
    - `fpdf` / `fpdf2`: **NOT installed**
    - `weasyprint`: **NOT installed**
    - `matplotlib` (v3.11.1): **INSTALLED** (includes `matplotlib.backends.backend_pdf.PdfPages`)
    - `pillow` (PIL v12.3.0): **INSTALLED**
    - `fonttools` (v4.63.0): **INSTALLED**
    - `fastapi` (v0.141.1), `starlette` (v1.6.0), `pydantic` (v2.13.4), `asyncpg` (v0.31.0), `SQLAlchemy` (v2.0.52), `httpx` (v0.28.1), `pytest` (v9.1.1): **INSTALLED**
  - Offline / Code-only Sandbox constraint: `pip install reportlab` fails due to sandboxed network isolation. PDF generation MUST rely on packages already installed in `.venv` (specifically `matplotlib.backends.backend_pdf` + `PIL`).

- **Test Suite Status (`tests/`)**:
  - Executed `./.venv/bin/pytest`: **559 passed, 0 failures, 1 warning in 30.26s**.
  - Executed `./.venv/bin/ruff check app tests`: **All checks passed (0 errors)**.

---

## 2. Logic Chain

### 2.1 SAR PDF Export Architecture (`GET /cases/{case_id}/sar/pdf`)
1. **Endpoint Routing**:
   - The user specification R4 requires `GET /cases/{case_id}/sar/pdf`.
   - To ensure compatibility across root navigation and API conventions, implement the handler at both:
     - `GET /cases/{case_id}/sar/pdf` in `app/main.py`
     - `GET /cases/{case_id}/sar/pdf` in `app/api/upi.py` (which exposes `/upi/cases/{case_id}/sar/pdf`)
2. **PDF Generation Strategy without External Packages**:
   - Because `reportlab` cannot be installed from PyPI in this offline sandbox, `matplotlib.backends.backend_pdf.PdfPages` combined with `matplotlib.pyplot` and `PIL.Image` provides a robust, built-in PDF generator.
   - Tested empirically: Matplotlib `PdfPages` outputs valid `%PDF-1.4` binary stream in <50ms without file disk churn.
   - Architecture: Create `app/forensics/sar_pdf.py` with `generate_sar_pdf(case_data: Dict[str, Any]) -> bytes`.
3. **PDF Document Layout**:
   - **Header**: High-contrast header banner "SUSPICIOUS ACTIVITY REPORT (SAR) — FIU-IND / RBI DPIP", Case ID, Generation Timestamp, Typology badge (`UPI_MULE_NETWORK_LAYERING`), Verdict (`BLOCK`/`HOLD`), and Risk Score gauge.
   - **Executive Summary & Transaction DNA**: Case details, Trigger transaction (`txn_id`, `amount`, `payer_vpa`, `payee_vpa`, `timestamp`), and reasons.
   - **Ring Members & Topology**: Clean grid/table of participating VPAs, bank names, PSP handles, and flow roles (Fan-in, Pass-through Conduit, Fan-out).
   - **Embedded Forensic Visual Graph**: Embedded PNG rendered via `app.forensics.upi_sar.render_ring_png` or case `visual_path` image loaded via PIL.
   - **Action Plan & Token Economy**: Prescribed FIU-IND filing actions and LLM token compression ratio metrics.
4. **Response Protocol**:
   - Content-Type: `application/pdf`
   - Content-Disposition: `attachment; filename="SAR_{case_id}.pdf"`
   - 404 response if case does not exist: `JSONResponse(status_code=404, content={"detail": f"UPI case '{case_id}' not found"})`.
   - Dynamic on-the-fly SAR generation: If a newly opened case does not have `sar_markdown` or `visual_path` rendered yet, generate them dynamically on request.

### 2.2 Dead Money Velocity (DMV) Score Integration (R1)
1. **DMV Metric Definition**:
   - Score range: `0.0` to `100.0`.
   - Represents the mule dormancy-to-burst signature: dormancy / account age followed by near-instant velocity surge (>90% balance churn).
   - Calculation formula: Combines account dormancy indicator with rapid outflow ratio and burst frequency.
2. **Evaluation Response Enrichment**:
   - Add `dmv_score: float = Field(default=0.0, description="Dead Money Velocity score 0-100")` to `UpiEvaluationResponse` in `app/models/upi_models.py`.
   - Computed during `UpiCaseService.evaluate()` and `UpiRiskScorer.evaluate()`.
3. **Analytics Integration**:
   - Add `top_dmv_vpas: List[Dict[str, Any]]` to `service.get_analytics()`:
     - Returns ranked list of VPAs: `[{"vpa": str, "dmv_score": float, "bank": str, "psp": str, "flagged_count": int, "total_amount": float, "last_activity": str}]`.
   - Case drawer receives `caseData.dmv_score` (or calculated from case trigger).

### 2.3 Workload Heatmap Data Engine (R5)
1. **7x24 Matrix Aggregation**:
   - Rows: 7 days of week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday).
   - Columns: 24 hours of the day (0 to 23).
   - Window: Rolling 30 days (`datetime.now(timezone.utc) - timedelta(days=30)`).
2. **Data Model**:
   - In `service.get_analytics()`, aggregate case timestamps from `_cases` and `_txn_log`.
   - Output structure in analytics response:
     ```json
     "workload_heatmap": [
       {"day": 0, "day_name": "Mon", "hour": 0, "count": 4, "total_amount": 120000.0},
       ...
       {"day": 6, "day_name": "Sun", "hour": 23, "count": 8, "total_amount": 340000.0}
     ]
     ```
   - Also provide helper 7x24 matrix: `"heatmap_matrix": [[count_0_0, ..., count_0_23], ... [count_6_0, ..., count_6_23]]`.

### 2.4 Device Telemetry Rules (R2) & Campaign Fingerprinting (R3)
1. **Telemetry Rules**:
   - `R_SIM_DEVICE_MISMATCH` (SIM-swap / device swap on same payer).
   - `R_IMPOSSIBLE_TRAVEL` (Geographic distance / elapsed time > 500km in <30 min).
   - `R_DATACENTER_IP` (Known hosting / VPN / Tor IP ranges: AWS, GCP, Azure, DigitalOcean, Tor exits).
2. **Campaign Fingerprinting**:
   - `CampaignSignatureStore` in `app/engine/campaign.py`: Extracts behavioral vector (amount rounding, hour bucket, velocity, device class).
   - When similarity >= threshold, emit `R_CAMPAIGN_MATCH` and populate `campaign_id` on `UpiEvaluationResponse`.

### 2.5 Live Auto-Feed Engine (R6)
1. **Autonomous Background Task**:
   - Managed background async task in `UpiCaseService`: `start_autofeed(rate_per_sec=10)`, `stop_autofeed()`, `is_autofeed_active()`.
   - Generates realistic synthetic transactions via `app/synthetic/upi_generator.py`.
   - Routes each transaction through the live pipeline (`service.evaluate()`), triggering honeypots, telemetry rules, DMV scores, federation rounds, and broadcasting `UPI_EVALUATED`, `new_case`, `stats_update` over WebSocket.
   - Endpoints: `POST /upi/autofeed/start`, `POST /upi/autofeed/stop`, `GET /upi/autofeed/status`.

---

## 3. Caveats

1. **No External Pip Installation**:
   - Sandbox network isolation prevents downloading packages from PyPI (e.g. `reportlab`, `weasyprint`).
   - Pure-python generation with pre-installed `matplotlib` + `PIL` is required and fully functional.
2. **Matplotlib Config Dir Environment**:
   - Matplotlib logs a non-fatal warning if `HOME` is read-only.
   - Must set `os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")` before importing `matplotlib`.
3. **Database Fallback Mode**:
   - When `DATABASE_URL` is empty, system operates in high-performance in-memory fallback mode. All models and endpoints must handle both active PostgreSQL sessions and in-memory fallback gracefully.

---

## 4. Conclusion & Recommended Action Plan

### 4.1 Implementation Roadmap for Backend
1. **New Module `app/forensics/sar_pdf.py`**:
   - Implements `build_sar_pdf(case_data: Dict[str, Any]) -> bytes` using `matplotlib.backends.backend_pdf` and `PIL`.
   - Embeds title, metadata boxes, SAR narrative markdown text, ring members table, and forensic graph PNG.
2. **Expose SAR PDF Endpoints**:
   - Add `GET /cases/{case_id}/sar/pdf` to `app/main.py`.
   - Add `GET /cases/{case_id}/sar/pdf` to `app/api/upi.py`.
   - Return `Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="SAR_{case_id}.pdf"'})`.
3. **Enhance Analytics Engine in `app/services/upi_cases.py`**:
   - Add `workload_heatmap` (7x24 grid over 30 days).
   - Add `top_dmv_vpas` (Top VPAs ranked by DMV score).
4. **Update `app/models/upi_models.py`**:
   - Add `dmv_score: float = 0.0` and `campaign_id: Optional[str] = None` to `UpiEvaluationResponse`.
5. **Implement Device Telemetry Rules (R2) in `app/engine/upi_rules.py`**:
   - Add `rule_sim_device_mismatch()`, `rule_impossible_travel()`, `rule_datacenter_ip()`.
6. **Implement Campaign Engine (R3) in `app/engine/campaign.py`**:
   - Add `R_CAMPAIGN_MATCH` rule and signature clustering.
7. **Implement Live Auto-Feed Mode (R6) in `app/services/upi_cases.py` & `app/api/upi.py`**:
   - Provide clean start/stop/status controls and real-time WebSocket event emission.

---

## 5. Verification Method

### 5.1 Independent Test Commands
```bash
# 1. Run full Pytest suite (must remain 100% green, 559+ passing)
./.venv/bin/pytest tests/ -v

# 2. Run Ruff linter across backend code
./.venv/bin/ruff check app tests

# 3. Test SAR PDF Generation directly via Python
./.venv/bin/python -c "
from app.services.upi_cases import get_upi_case_service
from app.synthetic.upi_generator import generate_labeled_stream
svc = get_upi_case_service()
stream, _ = generate_labeled_stream(total_txns=10, fraud_ratio=0.5, seed=42)
for item in stream:
    svc.evaluate(item.txn)
cases = svc.list_cases()
print(f'Opened {len(cases)} cases')
"

# 4. Frontend verification
cd frontend && npm run lint && npm run build && cd ..
```

### 5.2 Specific Test Cases to Add
- `tests/test_sar_pdf.py`:
  - `test_sar_pdf_existing_case_returns_200_and_pdf_mimetype()`
  - `test_sar_pdf_nonexistent_case_returns_404()`
  - `test_sar_pdf_binary_starts_with_pdf_header()`
  - `test_sar_pdf_includes_ring_members_and_narrative()`
- `tests/test_workload_heatmap.py`:
  - `test_analytics_includes_7x24_workload_heatmap()`
  - `test_workload_heatmap_buckets_day_and_hour_bounds()`
- `tests/test_dmv_score.py`:
  - `test_upi_check_returns_dmv_score_field()`
  - `test_top_vpas_by_dmv_score_in_analytics()`
- `tests/test_device_telemetry_rules.py`:
  - `test_sim_device_mismatch_trigger()`
  - `test_impossible_travel_trigger()`
  - `test_datacenter_ip_trigger()`
- `tests/test_campaign_fingerprint.py`:
  - `test_campaign_signature_stored_on_block()`
  - `test_campaign_match_rule_trigger()`
- `tests/test_autofeed.py`:
  - `test_autofeed_start_stop_lifecycle()`
