# Project: SAMPATI V2 UPI Mule-Network Detection Switch Upgrade

## Architecture
SAMPATI V2 is a real-time UPI switch-level mule-network fraud detection platform comprising a high-throughput FastAPI backend and an interactive React/Vite frontend.
- **Backend Architecture**:
  - `app/engine/`: Sub-millisecond inline rule and graph scoring (UpiScorer, UpiHotState).
  - `app/models/`: SQLAlchemy 2.0 declarative async models for PostgreSQL persistence (`upi_cases`, `mule_rings`, `case_feedback`, `aggregate_stats`).
  - `app/db/`: Async session factory, connection pooling optimized for AWS RDS t3.micro (pool_size=5, max_overflow=10), auto-migration on startup (`init_db`), health probe with DB ping.
  - `app/api/`: REST APIs for `/upi/check`, `/upi/simulate`, `/upi/cases`, `/upi/stats`, `/upi/federation`, and WebSocket feed (`/ws`, `/ws/`, `/ws/feed`).
  - `app/services/`: Case lifecycle management (`UpiCaseService`), SAR generation, token economy, analyst feedback resolution.
  - `deploy/`: EC2 userdata bootstrap, Dockerfile, Nginx proxy configuration.
- **Frontend Architecture**:
  - `frontend/src/components/`:
    - `NetworkConstellation.jsx`: Interactive HTML5 Canvas force-directed graph with hit detection for nodes and edges, hover tooltips, click-to-case integration with `CaseDrawer`, continuous risk-score edge gradient, and INR transaction amount tooltips.
    - `VerdictHistoryChart.jsx`: Recharts AreaChart displaying Allow/Hold/Block verdict velocity over time, located directly below `KpiStrip`.
    - `LiveFeed.jsx`: Real-time reactive stream of newly detected fraud cases with Framer Motion slide-in animations.
    - `KpiStrip.jsx`: Live counter tiles with smooth `useCountUp` animations driven by WebSocket stats updates.
    - `CaseDrawer.jsx`: Slide-out deep-dive drawer for case analysis and analyst feedback.
    - `Masthead.jsx`: Header with real-time WebSocket connection status badge.
  - `frontend/src/hooks/`:
    - `useWebSocket.js`: Self-healing, auto-reconnecting WebSocket client hook.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | RDS PostgreSQL Persistence Models | SQLAlchemy 2.0 models for `upi_cases`, `mule_rings`, `case_feedback`, and `aggregate_stats` with JSONB attributes and indexing | M1 | ORIGINAL_REQUEST §R1 |
| F2 | Connection Pooling & Auto-Migration | AsyncPG connection pool for AWS RDS t3.micro (pool_size=5, max_overflow=10), `create_all` startup hook, and `DATABASE_URL` environment loading | M1 | ORIGINAL_REQUEST §R1 |
| F3 | Database-Backed Case & Stats APIs | Modernized `/upi/cases`, `/upi/cases/{id}`, `/upi/stats`, and `/health` endpoints querying PostgreSQL | M1 | ORIGINAL_REQUEST §R1 |
| F4 | Dependency & Deployment Packaging | Updated `requirements.txt` (asyncpg, sqlalchemy), `Dockerfile`, and `deploy/ec2_userdata.sh` | M1 | ORIGINAL_REQUEST §R1 |
| F5 | WebSocket Broadcast Hub | Centralized `ConnectionManager` handling `/ws`, `/ws/`, and `/ws/feed` with broadcast support | M2 | ORIGINAL_REQUEST §R2 |
| F6 | Transaction & Case Event Emitters | Real-time broadcast hooks in `create_case`, `simulate`, and federation pipelines (< 2s latency) | M2 | ORIGINAL_REQUEST §R2 |
| F7 | Frontend WebSocket Hook & Feed Stream | `useWebSocket` hook in React updating `cases` list and `Masthead` status badge | M3 | ORIGINAL_REQUEST §R2 |
| F8 | Reactive KPI Counters | Real-time KPI strip counter updates on WebSocket events without page refresh | M3 | ORIGINAL_REQUEST §R2 |
| F9 | Interactive Constellation Hit Detection | Mouse move & click hit testing for nodes and edges on the HTML5 Canvas | M3 | ORIGINAL_REQUEST §R3 |
| F10 | Node Tooltip & Role Tagging | Hover tooltip on canvas nodes showing VPA and node role (Victim, Collector Hub, Layering Hop, Cash-Out) | M3 | ORIGINAL_REQUEST §R3 |
| F11 | Constellation Click-to-Case Drawer | Canvas node click opens `CaseDrawer` for corresponding case | M3 | ORIGINAL_REQUEST §R3 |
| F12 | Continuous Risk-Score Edge Gradient | Edge color intensity varies smoothly with risk score (faint slate -> amber -> bright red) | M3 | ORIGINAL_REQUEST §R3 |
| F13 | Transaction Amount Tooltip on Hover | Edge hover displays formatted transaction amount (₹ INR) and flow direction | M3 | ORIGINAL_REQUEST §R3 |
| F14 | Verdict History Recharts Component | `VerdictHistoryChart` AreaChart with Allow, Hold, Block series, axes, legend, and live stream indicator | M4 | ORIGINAL_REQUEST §R4 |
| F15 | Dashboard Layout & History Ingestion | Panel positioned below `KpiStrip` in `App.jsx`, receiving continuous data points from WS & simulations | M4 | ORIGINAL_REQUEST §R4 |
| F16 | End-to-End Test Suite & Verification | Full opaque-box test suite across Tiers 1-5 and adversarial hardening | M5 | ORIGINAL_REQUEST §AC |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend RDS PostgreSQL Persistence | F1, F2, F3, F4: SQLAlchemy models, asyncpg connection pool, startup table creation, API endpoints, requirements.txt, Dockerfile, ec2_userdata.sh | none | DONE |
| M2 | Backend Real-Time WebSocket Push Hub | F5, F6: ConnectionManager, multi-route WS endpoints, broadcast hooks in case creation and simulation | M1 | DONE |
| M3 | Frontend Real-Time Stream & Interactive Constellation | F7, F8, F9, F10, F11, F12, F13: `useWebSocket`, canvas hit detection, node tooltips, click-to-case, edge gradients, INR amounts | M2 | DONE |
| M4 | Verdict History Line/Area Chart & Dashboard | F14, F15: `VerdictHistoryChart.jsx` Recharts component, `App.jsx` integration, layout placement, build verification | M3 | DONE |
| M5 | Full E2E Test Suite & Adversarial Hardening | F16: Execute 100% of E2E test suite (Tiers 1-5) and forensic integrity audit | M1, M2, M3, M4 | DONE |

---

## Interface Contracts

### Backend Database Schema ↔ API Layer
- `UpiCaseModel` -> Table `upi_cases`:
  - `case_id`: String(64) PRIMARY KEY
  - `created_at`: DateTime(timezone=True)
  - `status`: String(32) ('OPEN', 'INVESTIGATED', 'RESOLVED')
  - `verdict`: String(16) ('ALLOW', 'HOLD', 'BLOCK')
  - `risk_score`: Integer (0-100)
  - `trigger_txn`: JSONB
  - `rule_hits`: JSONB
  - `adaptive_score`: Float
  - `network_score`: Float
  - `ring_hash`: String(64) FK -> `mule_rings.ring_hash` (nullable)
  - `ring_members_vpas`: JSONB
  - `token_economy`: JSONB
  - `sar_markdown`: Text
  - `visual_path`: String(255)
  - `topology`: JSONB
  - `resolution`: String(64)
  - `investigated_at`: DateTime(timezone=True)
  - `resolution_notes`: Text

### Backend WebSocket ↔ Frontend Client
- Endpoint: `/ws/feed` (and aliases `/ws`, `/ws/`)
- Event `new_case` & `stats_update` JSON formats verified and active.

### Constellation Graph Component ↔ App State
- Props and hover/click event callbacks verified and active.

---

## Code Layout
- Verified exclusive write boundaries and clean build artifacts in `frontend/dist/`.
