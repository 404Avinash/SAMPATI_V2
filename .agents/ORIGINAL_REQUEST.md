# Original User Request

## 2026-08-29T00:22:56+05:30

SAMPATI V2 is a real-time UPI mule-network fraud detection platform (FastAPI
backend + React/Vite frontend) deployed on AWS EC2 (Mumbai, ap-south-1) via
Docker + nginx. The backend currently stores all case data in-memory (lost on
restart). The frontend requires manual simulation clicks to update. This
upgrade migrates all persistence to AWS RDS PostgreSQL, adds a real-time
WebSocket push channel, and transforms the constellation visualizer into a
fully interactive graph.

Working directory: c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2

Integrity mode: development

## Requirements

### R1. AWS RDS PostgreSQL Persistence (Full Migration)
Replace all in-memory state in the backend with a persistent AWS RDS
PostgreSQL t3.micro database (free tier). All entities — UPI cases,
mule ring records, analyst feedback, and aggregate stats — must survive
container/instance restarts. The backend must auto-create tables on
startup if they do not exist, and must read the database connection
string from an environment variable (`DATABASE_URL`). The `requirements.txt`,
`Dockerfile`, and `deploy/ec2_userdata.sh` must be updated to pass the
`DATABASE_URL` env var into the container and provision the RDS instance
(or document the one-time setup step). Connection pooling must handle the
t3.micro's default max_connections (~87) without exhausting them.

### R2. Real-Time WebSocket Push
The backend must broadcast new case events to all connected frontend clients
via WebSocket as they are created (within ~2 seconds of a transaction being
processed), without the frontend needing to poll or click Simulate. The
frontend's live feed must update automatically when new cases arrive over
the WebSocket. The existing `/ws/` WebSocket endpoint already exists — it
must be wired to emit new-case payloads. The KPI strip counters must also
update in real time from the WebSocket stream without a page reload.

### R3. Interactive Constellation Visualizer
The existing canvas force-directed graph must become fully interactive:
- **Tooltips:** Hovering over any node shows the VPA address and node type
  (victim / collector-hub / layering-hop / cash-out).
- **Click to case:** Clicking a node that corresponds to a known case opens
  the CaseDrawer for that case (same drawer used in the live feed).
- **Risk-score edge colouring:** Edge colour intensity reflects the risk score
  of the associated case (low risk = faint, high risk = bright red), not just
  a binary flagged/unflagged.
- **Amount labels:** Edges show the transaction amount (formatted as ₹ INR)
  on hover.

### R4. Verdict History Line Chart
Add a new panel below the existing KPI strip showing a line/area chart of
verdict counts (ALLOW, HOLD, BLOCK) over time within the current session.
Each time the WebSocket delivers new cases or a simulation completes, the
chart appends a new data point. The chart must use the existing Recharts
dependency already in `package.json`.

## Acceptance Criteria

### R1 — RDS Persistence
- [ ] `asyncpg` or `psycopg[async]` is added to `requirements.txt` and the
      Dockerfile installs it
- [ ] On fresh container start with a valid `DATABASE_URL`, tables are created
      and the app starts without errors
- [ ] After running a simulation, stopping and restarting the container (same
      `DATABASE_URL`), `GET /upi/cases` returns the previously created cases
- [ ] `GET /upi/stats` reflects cumulative counts from the DB, not just the
      current session

### R2 — WebSocket Push
- [ ] Connecting to `ws://<host>/ws/feed` (or the existing WS path) receives
      a JSON event within 2 seconds of a new case being created by the engine
- [ ] The frontend live feed row appears without any manual user action after
      a simulation runs on the backend
- [ ] KPI strip counters increment in real time as events arrive

### R3 — Interactive Visualizer
- [ ] Hovering a node shows a tooltip with VPA and node type — no click needed
- [ ] Clicking a node with an associated case opens the CaseDrawer (same
      component used in the live feed)
- [ ] Edge colour varies continuously with risk score (not just red/grey)
- [ ] Hovering an edge shows the INR amount for that transaction

### R4 — Verdict History Chart
- [ ] A Recharts `LineChart` or `AreaChart` with three series (Allow/Hold/Block)
      is visible on the dashboard below the KPI strip
- [ ] The chart updates (new data point appended) each time new case data
      arrives via WebSocket or simulation
- [ ] Chart has a clear legend and formatted Y-axis (count) and X-axis (time)

### Cross-cutting
- [ ] `vite build` completes without errors after frontend changes
- [ ] The Docker container starts and `/health` returns 200 with a valid
      `DATABASE_URL` set
- [ ] No existing functionality is broken (simulate, federation, case drawer,
      feedback buttons all still work)
