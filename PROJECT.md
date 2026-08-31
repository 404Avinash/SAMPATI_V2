# Project: SAMPATI V2 Sprint 2 — Full PRD & Autonomous Live Auto-Feed

## Architecture
SAMPATI V2 is an operational UPI fraud detection platform featuring a FastAPI backend, React 18 / Vite 5 dashboard, PostgreSQL persistence, and real-time WebSocket feed (`/ws/feed`). Sprint 2 completes the full PRD (F-04 to F-08) and introduces the Autonomous Live Auto-Feed mode.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SAMPATI V2 ARCHITECTURE                                  │
│                                                                                             │
│  [ FRONTEND (React 18 / Vite 5 / Tailwind) ]                                                │
│    ├── Overview (KpiStrip, ControlBar, NetworkConstellation with Timeline Slider)          │
│    ├── CaseDrawer (AI SAR narrative, Forensics, DMV Gauge, Export SAR Button)               │
│    ├── AnalyticsPage (Time-Series, 7x24 Workload Heatmap, Top VPAs by DMV Table)            │
│    └── AppStateContext (Reactive WebSocket hub, Auto-Feed toggle & telemetry state)         │
│                                           ▲                                                 │
│                                    WebSocket /ws/feed                                       │
│                                           │                                                 │
│  [ BACKEND CORE (FastAPI / Async Engine) ]                                                  │
│    ├── Live Auto-Feed Engine (app/services/autofeed.py) -> 5–20 tx/s synthetic stream      │
│    ├── Risk Scoring Pipeline (app/engine/upi_scorer.py):                                    │
│    │     ├─ Layer 1: Rules (R01-R07, R_HONEYPOT, R_SIM_DEVICE_MISMATCH,                   │
│    │     │                 R_IMPOSSIBLE_TRAVEL, R_DATACENTER_IP, R_CAMPAIGN_MATCH)          │
│    │     ├─ Layer 2: Adaptive EWMA Behavioral Anomaly Model                                 │
│    │     └─ Layer 3: Federated Mule Network Mesh                                            │
│    ├── Dead Money Velocity (DMV) Engine (Dormancy vs Outflow Burst 0–100)                   │
│    ├── Campaign DNA Fingerprint Store (app/engine/campaign.py)                              │
│    ├── Forensics & SAR PDF Generator (app/forensics/sar_pdf.py via Matplotlib/PIL)          │
│    └── REST API Gateway (app/main.py, app/api/upi.py, app/api/federation.py)                │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Dead Money Velocity (DMV) Score | 0–100 score per VPA measuring dormancy + sudden outflow burst | M1, M4 | ORIGINAL_REQUEST §R1 |
| 2 | SIM-Device Mismatch Rule | `R_SIM_DEVICE_MISMATCH` (30 pts) detecting SIM swaps and device changes | M1 | ORIGINAL_REQUEST §R2 |
| 3 | Impossible Travel Rule | `R_IMPOSSIBLE_TRAVEL` (35 pts) detecting >500km in <30min / >1000km/h | M1 | ORIGINAL_REQUEST §R2 |
| 4 | Datacenter / VPN IP Rule | `R_DATACENTER_IP` (25 pts) detecting AWS/GCP/Azure/DO/Tor CIDR subnets | M1 | ORIGINAL_REQUEST §R2 |
| 5 | Transaction DNA Campaign Fingerprinting | `R_CAMPAIGN_MATCH` (30 pts), campaign signature store on BLOCK, `campaign_id` | M1 | ORIGINAL_REQUEST §R3 |
| 6 | One-Click SAR PDF Export | `GET /cases/{case_id}/sar/pdf` with narrative, ring members, forensic graph | M2, M4 | ORIGINAL_REQUEST §R4 |
| 7 | Analyst Workload Heatmap | 7x24 day-of-week × hour-of-day case volume grid over rolling 30 days | M2, M4 | ORIGINAL_REQUEST §R5 |
| 8 | Autonomous Live Auto-Feed Engine | 5–20 tx/s background transaction generation, live evaluation, WebSocket broadcast | M3, M4 | ORIGINAL_REQUEST §R6 |
| 9 | Live Auto-Feed UI Controls | Dashboard toggle button with live TPS telemetry, KPI ticking, auto constellation | M4 | ORIGINAL_REQUEST §R6 |
| 10| Full E2E Test Suite & Adversarial Hardening | Comprehensive multi-tier test suite verifying all R1–R6 requirements with 0 regressions | M5 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Risk Engine Extensions | DMV metric, 3 Telemetry Rules (`R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL`, `R_DATACENTER_IP`), Campaign DNA (`R_CAMPAIGN_MATCH`), model updates (`dmv_score`, `campaign_id`) | none | PLANNED |
| M2 | Backend Services & Reporting | `app/forensics/sar_pdf.py`, `GET /cases/{case_id}/sar/pdf`, 7x24 Heatmap aggregation, Top VPAs by DMV in `service.get_analytics()` | M1 | PLANNED |
| M3 | Autonomous Live Auto-Feed Engine | Background async generator (5–20 tx/s), full scoring pass-through, WebSocket hub broadcast, start/stop endpoints (`/upi/autofeed/*`) | M1 | PLANNED |
| M4 | Frontend Dashboard Integration | CaseDrawer DMV gauge & Export SAR button, Analytics Heatmap & DMV table, Auto-Feed toggle button & state in `AppStateContext.jsx` | M2, M3 | PLANNED |
| M5 | E2E Testing Track & Final Quality Gate | Tiers 1–4 requirement tests, Tier 5 adversarial hardening, 100% test pass, clean build & lint | M1, M2, M3, M4 | PLANNED |

## Interface Contracts

### 1. `UpiEvaluationResponse` (in `app/models/upi_models.py`)
```python
class UpiEvaluationResponse(BaseModel):
    txn_id: str
    risk_score: int
    action: str  # ALLOW, HOLD, BLOCK
    reasons: List[str]
    rule_breakdown: List[RuleHit]
    rule_score: int
    adaptive_score: float
    network_score: float
    execution_latency_ms: float
    evaluated_at: datetime
    case_id: Optional[str] = None
    dmv_score: float = Field(default=0.0, description="Dead Money Velocity score (0-100)")
    campaign_id: Optional[str] = Field(default=None, description="Active fraud campaign identifier if matched")
```

### 2. SAR PDF Export Endpoint
- **HTTP Route**: `GET /cases/{case_id}/sar/pdf` and `GET /upi/cases/{case_id}/sar/pdf`
- **Success Response**: Binary stream `%PDF-1.4`, `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="SAR_{case_id}.pdf"`
- **404 Response**: `{"detail": "UPI case '{case_id}' not found"}`

### 3. Analytics Response Extensions (`GET /stats/analytics` & `GET /upi/stats/analytics`)
```json
{
  "workload_heatmap": [
    {"day": 0, "day_name": "Mon", "hour": 0, "count": 5, "total_amount": 150000.0},
    ...
    {"day": 6, "day_name": "Sun", "hour": 23, "count": 8, "total_amount": 320000.0}
  ],
  "top_dmv_vpas": [
    {
      "vpa": "dormant.cashout@okhdfcbank",
      "bank": "HDFC Bank",
      "dmv_score": 94.5,
      "dormancy_days": 84,
      "outflow_rate": "98% in 6m",
      "amount": 1850000.0
    }
  ]
}
```

### 4. Auto-Feed Lifecycle REST Endpoints
- `POST /upi/autofeed/start` -> Body: `{"rate_tps": 12.0, "fraud_ratio": 0.15, "bursty": true}` -> `{"status": "started", "active": true, "tps": 12.0}`
- `POST /upi/autofeed/stop` -> `{"status": "stopped", "active": false, "total_generated": N}`
- `GET /upi/autofeed/status` -> `{"active": bool, "rate_tps": float, "fraud_ratio": float, "total_generated": int, "total_flagged": int, "started_at": str, "uptime_seconds": float}`

## Code Layout
- `app/models/upi_models.py`: Data contracts (`UpiTransaction`, `UpiEvaluationResponse`, `RuleHit`)
- `app/engine/upi_rules.py`: Deterministic rules (R01-R07, honeypot, telemetry rules)
- `app/engine/campaign.py`: Transaction DNA campaign signature store and matcher
- `app/engine/dmv.py`: Dead Money Velocity scoring engine
- `app/engine/upi_scorer.py`: 3-layer risk evaluation coordinator
- `app/forensics/sar_pdf.py`: Pure-Python SAR PDF generator (Matplotlib/PIL)
- `app/services/autofeed.py`: Autonomous background transaction generator
- `app/services/upi_cases.py`: `UpiCaseService` singleton managing cases, stats, and analytics
- `app/api/upi.py`: UPI REST endpoints
- `app/main.py`: Top-level FastAPI application and root routes
- `frontend/src/services/api.js`: REST client functions
- `frontend/src/context/AppStateContext.jsx`: Global reactive state and WebSocket handler
- `frontend/src/components/CaseDrawer.jsx`: Case dossier with DMV gauge & Export SAR button
- `frontend/src/pages/AnalyticsPage.jsx`: Analytics page with 7x24 Heatmap & Top DMV accounts
- `frontend/src/components/ControlBar.jsx`: Simulation and Auto-Feed controls
- `tests/`: Pytest test suite across all 5 tiers
