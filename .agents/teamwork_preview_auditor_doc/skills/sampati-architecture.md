---
name: sampati-architecture
description: Deep context on SAMPATI V2's working architecture, tech stack, data pipeline, and multi-layered ML engine. Read this to understand how the project works.
---

# SAMPATI V2 Architecture & Working Principles

This skill provides the core architectural context of SAMPATI V2. Use this knowledge to align any new features or bug fixes with the existing stack.

## 1. Frontend (React 18 + Vite)
- **Routing**: SPA powered by React Router DOM.
- **Topology Visualizers**: 
  - *Network Graph*: Custom HTML5 Canvas physics engine (no D3.js). Calculates Hooke's Law (springs) and Coulomb's Law (repulsion) in a `requestAnimationFrame` loop.
  - *Geographic Map*: Vanilla Leaflet.js rendering Esri World Light Gray Canvas tiles.
- **State**: React Context API fed by WebSockets.

## 2. Backend Pipeline (FastAPI)
- **Ingestion**: FastAPI async REST endpoints.
- **Hot Cache (Redis)**: Holds short-term account state (velocity, recent history) in-memory for sub-millisecond ML inference.
- **Cold Storage (PostgreSQL)**: Permanent logging of verdicts and ML scores via `asyncpg`.
- **Broadcasting**: WebSockets push live verdicts directly to the React frontend.

## 3. The ML & AI Scoring Engine
The system uses a multi-layered defense-in-depth approach:
- **Layer 1 (Rules)**: Deterministic heuristics catching physical impossibilities (e.g., Geo-velocity jumps, Dead Money Velocity bursts).
- **Layer 2 (Unsupervised ML - Isolation Forest)**: Mathematical anomaly detection trained only on normal traffic baselines to catch Zero-Day fraud (unseen patterns).
- **Layer 3 (Supervised ML - Random Forest Classifier)**: Pure NumPy implementation extracting 13 standardized features. Evaluated strictly on F1 Score and False-Positive Rate due to extreme class imbalance in financial data.
- **Layer 4 (Generative AI - Google Gemini)**: Acts as an autonomous forensic investigator. Reads raw ML scores and outputs plain-English Suspicious Activity Reports (SARs) in PDF format.

## 4. Data Flow & Dashboard Metrics (The "How" & "Why")
Understanding how the numbers on the screen (like the Overview Dashboard) actually work:

### What is showing?
The dashboard displays live Key Performance Indicators (KPIs):
- **Live Rings & Open Investigations**: The number of active, unresolved fraud networks currently wreaking havoc.
- **Intercepted Volume**: The total rupee amount (e.g., ₹6.78 Cr) the AI has successfully frozen.
- **Velocity Charts**: Live graphs showing the speed of transactions hitting the system.

### Why is it showing?
To provide **Explainability** and **Human-in-the-Loop** control. The AI makes decisions in milliseconds, but human analysts need these numbers to monitor the AI's performance, verify its accuracy, and take manual action (like exporting a PDF report) if a major syndicate is detected.

### How is it showing? (The Technical Flow)
1. **The Transaction**: A simulated transaction hits the FastAPI backend.
2. **The Calculation**: As the ML engine scores the transaction, it also updates rolling aggregate metrics (e.g., adding ₹500 to the total "Intercepted Volume") in the Redis cache.
3. **The Push**: The backend instantly blasts this updated JSON data over a persistent **WebSocket** connection.
4. **The Render**: The React frontend receives the WebSocket message, updates its global `AppStateContext`, and the numbers on the screen (like the red badge in the Navbar or the big numbers on the Overview page) magically update themselves without the user ever hitting refresh.
