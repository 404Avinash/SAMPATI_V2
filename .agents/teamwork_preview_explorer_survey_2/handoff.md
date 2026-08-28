# Handoff Report — Requirement R2: Real-Time WebSocket Push Survey

## 1. Observation
- **Original User Request**: Investigated `ORIGINAL_REQUEST.md` (lines 31-38, 71-77) for Requirement R2 (Real-Time WebSocket Push).
- **Backend Architecture**:
  - `app/main.py` lines 16, 70 imports and includes `websocket.router`.
  - Reverse proxy in `deploy/ec2_userdata.sh` lines 79-88 configures `location /ws/` with `Upgrade $http_upgrade` and `Connection "upgrade"`.
  - Development proxy in `frontend/vite.config.js` line 11 configures `"/ws": { target: "ws://localhost:8000", ws: true }`.
  - Root deployment documentation `HANDOFF.md` line 118 specifies `WebSocket Threat Stream` at `ws://<PUBLIC_IP>/ws/`.
- **Frontend Architecture**:
  - `frontend/src/App.jsx` manages `stats` and `cases` state, but has NO active WebSocket client connection; updates only occurred via explicit HTTP `api.simulate()`, `api.cases()`, `api.stats()`.
  - `frontend/src/components/LiveFeed.jsx` uses `framer-motion` `AnimatePresence` to render `cases.slice(0, 40)`.
  - `frontend/src/components/KpiStrip.jsx` animates 6 counters (`evaluated`, `allowed`, `held`, `blocked`, `rings`, `dpip`) using `useCountUp`.
  - `frontend/src/components/Masthead.jsx` contains a live status indicator currently bound to local boolean `live`.
- **Report Location**: Detailed technical survey report written to `c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_2\survey_websocket_realtime.md`.

## 2. Logic Chain
1. *Endpoint Compatibility*: Since Nginx proxies `/ws/` and Vite proxies `/ws`, supporting routes `@router.websocket("/ws")`, `@router.websocket("/ws/")`, and `@router.websocket("/ws/feed")` provides seamless compatibility across production and dev environments.
2. *Broadcast Architecture*: An asynchronous `ConnectionManager` with connection pooling, broadcast locks, and automatic dead-connection cleanup handles concurrent dashboard sessions reliably without degrading sub-10ms transaction scoring latencies.
3. *Broadcasting Hook Points*: By hooking `ConnectionManager.broadcast()` into `app.services.upi_cases.create_case` and the transaction simulation loop in `app.api.upi.simulate`, every new fraud case or simulation step will trigger immediate WebSocket delivery.
4. *Frontend Smooth Ingestion*:
   - Adding a reusable `useWebSocket` hook in `frontend/src/hooks/useWebSocket.js` handles auto-reconnect, keepalive, and JSON parsing.
   - Prepending incoming cases to `cases` state (`[newCase, ...prev.slice(0, 99)]`) triggers `framer-motion` slide-in animations in `LiveFeed` without re-fetching all cases over HTTP.
   - Updating `stats` triggers `useCountUp` in `KpiStrip` to smoothly transition counter values.
   - Passing connection status to `Masthead` activates the green pulsing "LIVE FEED" badge.

## 3. Caveats
- Browser WebSocket connections in local development connect through the Vite dev server proxy (`ws://localhost:5173/ws/feed`), while in production/Docker they connect through Nginx (`ws://<IP>/ws/feed` or `ws://localhost:8000/ws/feed`). The frontend hook must dynamically derive the WebSocket URL from `window.location`.
- During high-throughput simulations (e.g. 2000 transactions), emitting individual WebSocket events for every single allowed transaction could saturate client rendering. Batching progress updates via periodic `stats_update` while immediately pushing flagged `new_case` events achieves optimal responsiveness.

## 4. Conclusion
Requirement R2 is thoroughly surveyed and completely specified. The implementation requires:
1. Backend `ConnectionManager` with `/ws`, `/ws/`, and `/ws/feed` routes and broadcast hooks in `create_case` and `simulate`.
2. Frontend `useWebSocket` hook in `App.jsx` for reactive updates to `cases`, `stats`, and `Masthead` live indicator.
3. The specified JSON payload schemas ensure 100% data contract compatibility with existing UI components.

## 5. Verification Method
1. **Backend WebSocket Verification**:
   Connect to `ws://localhost:8000/ws/feed` using a WebSocket client (`wscat` / Python client). Send a test UPI transaction via `POST /upi/check` or trigger `/upi/simulate`. Confirm receipt of a valid JSON `new_case` event within < 200ms.
2. **Frontend UI Reactive Update Verification**:
   Launch the web dashboard. Confirm the header badge displays `LIVE FEED`. Trigger a transaction on the backend without interacting with the UI. Verify that a new row smoothly appears in `LiveFeed` and that `KpiStrip` numbers increment automatically without page reload.
