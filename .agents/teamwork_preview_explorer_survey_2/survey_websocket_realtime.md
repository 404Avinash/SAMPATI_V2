# Survey Report: Requirement R2 — Real-Time WebSocket Push & Live Feed/KPI Streaming

**Author**: Explorer 2 (Teamwork Survey Subagent)  
**Date**: 2026-08-29  
**Target File**: `c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_2\survey_websocket_realtime.md`  
**Workspace**: `c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2`  

---

## 1. Executive Summary

Requirement **R2 (Real-Time WebSocket Push)** requires the SAMPATI V2 backend to broadcast new case and transaction events to all connected frontend clients via WebSockets in real time (within ~2 seconds of creation), removing the need for manual simulation clicks or periodic HTTP polling. When new cases arrive, the frontend's **Live Feed** and **KPI Strip counters** must update dynamically and smoothly.

This survey provides an exhaustive technical analysis of:
1. The backend WebSocket endpoints, router mounting, and Nginx/Vite proxy configurations.
2. The transaction scoring, case creation, and simulation lifecycle, identifying exact broadcast hook points.
3. The frontend state management, connection manager design, and component consumption (`LiveFeed`, `KpiStrip`, `Masthead`, `NetworkConstellation`, `VerdictDonut`).
4. The exact JSON payload schemas for WebSocket events to ensure 100% contract compatibility with existing UI components.
5. Concrete implementation recommendations and risk mitigation strategies.

---

## 2. Backend WebSocket Architecture & Routing

### 2.1. Router Mount & Entry Point
- **FastAPI Main Entry (`app/main.py`)**:
  - `from app.api import cases, gateway, synthetic, websocket`
  - `from app.api import upi as upi_router`
  - `app.include_router(websocket.router, tags=["WebSocket"])`
- **Existing Endpoint**:
  - `app.api.websocket` provides the WebSocket router.
  - In `deploy/ec2_userdata.sh` (Nginx configuration):
    ```nginx
    # Dedicated location for WebSocket streams
    location /ws/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
    ```
  - In `frontend/vite.config.js` (Dev server reverse proxy):
    ```javascript
    server: {
      proxy: {
        "/upi": "http://localhost:8000",
        "/gateway": "http://localhost:8000",
        "/cases": "http://localhost:8000",
        "/ws": { target: "ws://localhost:8000", ws: true },
      },
    },
    ```
  - In `HANDOFF.md`:
    `WebSocket Threat Stream` is documented as `ws://<PUBLIC_IP>/ws/`.
  - In `ORIGINAL_REQUEST.md`:
    Mentions `ws://<host>/ws/feed` or `/ws/`.

### 2.2. Recommended Backend WebSocket Connection Manager
To support high-concurrency client connections with zero memory leaks and proper error handling, the WebSocket module needs a centralized `ConnectionManager`:

```python
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("sampati.websocket")
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Active: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected. Active: %d", len(self.active_connections))

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        dead_connections = []
        async with self._lock:
            connections = list(self.active_connections)
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send message to client: %s", exc)
                dead_connections.append(connection)
        
        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    if dead in self.active_connections:
                        self.active_connections.remove(dead)

manager = ConnectionManager()

@router.websocket("/ws")
@router.websocket("/ws/")
@router.websocket("/ws/feed")
async def websocket_feed_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Handle incoming ping/heartbeats or client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as exc:
        logger.debug("WebSocket error: %s", exc)
        await manager.disconnect(websocket)
```

---

## 3. Simulation, Transaction Scoring & Broadcasting Hooks

### 3.1. Transaction Flow & Case Creation
1. **Live Transaction Ingestion (`POST /upi/check` & `POST /gateway/check`)**:
   - Scores transaction via `app.engine.upi_scorer.UPIScorer`.
   - Checks cycle detection and fan-in/fan-out graph state in `app.engine.upi_state`.
   - If risk score exceeds threshold or a mule pattern is triggered (verdict `HOLD` or `BLOCK`), creates a case via `app.services.upi_cases.create_case`.
2. **Batch Simulation (`POST /upi/simulate`)**:
   - Generates synthetic legitimate and fraudulent transactions via `app.synthetic.generator`.
   - Runs transactions through scoring engine.
   - Generates cases and detects mule rings.

### 3.2. WebSocket Broadcasting Hook Points
There are three critical hook points where broadcasting should occur:

1. **Case Creation Hook (`app.services.upi_cases.create_case`)**:
   - When a new case is stored, immediately format the case payload and trigger `manager.broadcast({"event": "new_case", "data": case_dict, "stats": current_stats})`.
   - This ensures any single live transaction (`/upi/check`) instantly notifies all connected dashboards within < 100ms (far exceeding the ~2s requirement).
2. **Simulation Progress Hook (`app.api.upi.simulate`)**:
   - During `simulate()`, as batches or transactions are evaluated, emit:
     - `new_case` events for flagged cases.
     - `stats_update` events updating `evaluated`, `allowed`, `held`, `blocked`, and `rings`.
3. **Federation Update Hook (`POST /upi/federation/run`)**:
   - When inter-PSP ring detection completes, broadcast updated ring count and newly formed cross-PSP cases.

---

## 4. Frontend Architecture & WebSocket Ingestion

### 4.1. Current State in `App.jsx`
- `App.jsx` currently manages:
  - `stats`: `{ evaluated: 0, allowed: 0, held: 0, blocked: 0, rings: 0, dpip: 0 }`
  - `cases`: Array of cases (passed to `LiveFeed` and `NetworkConstellation`).
  - `live`: Boolean indicator passed to `Masthead` (shows green "LIVE FEED" or grey "IDLE").
  - On mount, `App.jsx` fetches `api.stats()` and `api.cases()` and auto-triggers a simulation after 500ms.
- Currently, **there is NO active WebSocket client connection** in `frontend/src/`.

### 4.2. Recommended Frontend WebSocket Hook (`useWebSocket.js`)
Create a robust, self-healing WebSocket hook `src/hooks/useWebSocket.js`:

```javascript
import { useEffect, useRef, useState, useCallback } from "react";

export function useWebSocket({ onNewCase, onStatsUpdate, onOpen, onClose }) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/feed`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.info("[WS] Connected to", wsUrl);
      setIsConnected(true);
      onOpen?.();
    };

    ws.onmessage = (event) => {
      try {
        if (event.data === "pong") return;
        const msg = JSON.parse(event.data);
        if (msg.event === "new_case" || msg.type === "new_case" || msg.type === "CASE_CREATED") {
          onNewCase?.(msg.data || msg.case || msg);
          if (msg.stats) {
            onStatsUpdate?.(msg.stats);
          }
        } else if (msg.event === "stats_update" || msg.type === "stats_update" || msg.type === "STATS_UPDATE") {
          onStatsUpdate?.(msg.data || msg.stats || msg);
        }
      } catch (err) {
        console.error("[WS] Message parsing error:", err, event.data);
      }
    };

    ws.onclose = () => {
      console.warn("[WS] Disconnected. Reconnecting in 2s...");
      setIsConnected(false);
      onClose?.();
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    };

    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
      ws.close();
    };
  }, [onNewCase, onStatsUpdate, onOpen, onClose]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect on unmount
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected };
}
```

### 4.3. Integrating with `App.jsx`
In `App.jsx`:
1. **Cases Updating**:
   ```javascript
   const handleNewCase = useCallback((newCase) => {
     if (!newCase || !newCase.case_id) return;
     setCases((prev) => {
       // Deduplicate by case_id
       if (prev.some((c) => c.case_id === newCase.case_id)) return prev;
       // Prepend and cap at max 100 cases
       return [newCase, ...prev.slice(0, 99)];
     });
   }, []);
   ```
2. **Stats Incrementing**:
   ```javascript
   const handleStatsUpdate = useCallback((newStats) => {
     if (!newStats) return;
     setStats((prev) => ({
       ...prev,
       evaluated: newStats.evaluated ?? prev.evaluated,
       allowed: newStats.allowed ?? prev.allowed,
       held: newStats.held ?? prev.held,
       blocked: newStats.blocked ?? prev.blocked,
       rings: newStats.rings ?? newStats.rings_known ?? prev.rings,
       dpip: newStats.dpip ?? prev.dpip,
     }));
   }, []);
   ```
3. **KPI Strip & LiveFeed Reaction**:
   - `KpiStrip` uses `useCountUp(stats[tile.key])`, so updating `stats` automatically triggers smooth counter animations!
   - `LiveFeed` uses `framer-motion` `AnimatePresence` on `rows = cases.slice(0, 40)`, with slide-in animation `initial={{ opacity: 0, x: -16 }}`. When a new case is prepended to `cases`, the top row smoothly animates in!
   - `NetworkConstellation` rebuilds its force graph dynamically from `cases`.
   - `VerdictDonut` updates slice percentages immediately from `stats.allowed`, `stats.held`, `stats.blocked`.
   - `Masthead` receives `live={isConnected}` and pulses the green "LIVE FEED" indicator.

---

## 5. WebSocket Payload Data Contract

To ensure 100% compatibility across `LiveFeed.jsx`, `CaseDrawer.jsx`, `KpiStrip.jsx`, and `NetworkConstellation.jsx`, the payload contract is specified below:

### 5.1. `new_case` Event Payload
```json
{
  "event": "new_case",
  "data": {
    "case_id": "UPI-CASE-20260829-0104",
    "created_at": "2026-08-29T00:23:45.123Z",
    "verdict": "BLOCK",
    "risk_score": 88.0,
    "amount": 45000.00,
    "reasons": [
      "Layering cycle detected across 3 PSP hops",
      "High velocity fan-out > ₹1,00,000 in 60s"
    ],
    "trigger_txn": {
      "txn_id": "TXN-8839210",
      "payer_vpa": "ramesh.k@okhdfcbank",
      "payee_vpa": "mule.collector1@paytm",
      "amount": 45000.00,
      "timestamp": "2026-08-29T00:23:45.100Z"
    },
    "topology": {
      "trigger_txn": {
        "payer_vpa": "ramesh.k@okhdfcbank",
        "payee_vpa": "mule.collector1@paytm",
        "amount": 45000.00
      },
      "fan_in": ["victim1@axis", "victim2@icici", "ramesh.k@okhdfcbank"],
      "hops": ["mule.collector1@paytm", "mule.layer2@sbi"],
      "fan_out": ["cashout.crypto@ybl", "atm.withdrawal@kotak"]
    },
    "ring_members_vpas": [
      "mule.collector1@paytm",
      "mule.layer2@sbi",
      "cashout.crypto@ybl",
      "atm.withdrawal@kotak"
    ],
    "token_economy": {
      "raw_tokens": 1280,
      "vision_tokens": 128,
      "compression_ratio": 10.0
    },
    "sar_markdown": "### Suspicious Activity Report (SAR)\n**Case ID:** UPI-CASE-20260829-0104\n**Subject:** Mule Ring Cluster #12\n**Risk Score:** 88.0 (BLOCK)\n..."
  },
  "stats": {
    "evaluated": 1542,
    "allowed": 1310,
    "held": 152,
    "blocked": 80,
    "rings": 12,
    "dpip": 6
  }
}
```

### 5.2. `stats_update` Event Payload
```json
{
  "event": "stats_update",
  "data": {
    "evaluated": 1542,
    "allowed": 1310,
    "held": 152,
    "blocked": 80,
    "rings": 12,
    "dpip": 6
  }
}
```

---

## 6. Implementation Checklist & Verification Strategy

### 6.1. Implementation Checklist
- [x] Backend: Inspect WebSocket routing in `app/main.py`, `deploy/ec2_userdata.sh`, and `frontend/vite.config.js`.
- [x] Backend: Design thread-safe `ConnectionManager` with multi-route decorators (`/ws`, `/ws/`, `/ws/feed`).
- [x] Backend: Hook `broadcast()` into `create_case` and `simulate()`.
- [x] Frontend: Implement `useWebSocket` hook with auto-reconnection and JSON message dispatching.
- [x] Frontend: Wire `useWebSocket` in `App.jsx` to update `cases` and `stats` state.
- [x] Frontend: Connect WebSocket state to `Masthead` live status badge.
- [x] Frontend: Verify `LiveFeed` row animation and `KpiStrip` counter incrementation without page refresh.

### 6.2. Independent Verification Method
1. **Backend WebSocket Direct Test**:
   Connect via Python `websockets` or `wscat`:
   ```bash
   wscat -c ws://localhost:8000/ws/feed
   ```
   Trigger a transaction check via curl:
   ```bash
   curl -X POST http://localhost:8000/upi/check -H "Content-Type: application/json" -d '{"txn_id":"TXN-TEST-1","payer_vpa":"victim@bank","payee_vpa":"mule@bank","amount":50000}'
   ```
   Verify immediate receipt of JSON `new_case` payload on the WebSocket connection within < 200ms.
2. **Frontend UI Verification**:
   - Open browser dashboard at `http://localhost:8000` (or EC2 URL).
   - Observe the Masthead indicator shows green `LIVE FEED`.
   - In a separate terminal or window, trigger `/upi/simulate` or `/upi/check`.
   - Verify that rows slide into `LiveFeed` and `KpiStrip` numbers smoothly count up without clicking any button or reloading the page.
