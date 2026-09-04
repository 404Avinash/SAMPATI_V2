# SAMPATI V2 — Architecture & Technology Stack

This document provides a comprehensive breakdown of the entire SAMPATI V2 system, explaining exactly how the frontend interface maps to the backend engine, and detailing the specific Artificial Intelligence and Machine Learning models used in the platform.

---

## 1. Frontend: The Visualization UI (React 18)

The frontend is a Single Page Application (SPA) built with **React 18**, bundled by **Vite**, and styled with **Tailwind CSS**. It is designed to render massive amounts of live data without lagging the browser.

### A. Navigation & Routing
*   **React Router DOM:** Handles all page transitions instantly. When you click the top navbar (e.g., *Threat Intelligence* to *Topology Mesh*), the URL changes and the new components are injected without the page ever reloading.
*   **WebSockets & React Context:** A persistent WebSocket connection pipes data directly from the backend into a global React Context (`AppStateContext.jsx`). This allows the red notification badges (like `Investigations`) to update instantly across the entire app.

### B. Topology Mesh Visualizers
The visualizers are the core of the dashboard, rendering live fraud data via two different technologies:
1.  **Constellation Force Graph (Logical View):** 
    *   *Tech:* HTML5 `<canvas>` + Custom Vanilla JS Physics Engine.
    *   *How it works:* It does not use external libraries like D3.js. It runs a custom `requestAnimationFrame` loop 60 times a second, calculating Hooke's Law (spring tension for transactions) and Coulomb's Law (magnetic repulsion for accounts) to organically cluster fraudulent mule rings together.
2.  **India Mule Corridors (Geographic View):** 
    *   *Tech:* **Leaflet.js** (v1.9.4) + **Esri World Light Gray Canvas**.
    *   *How it works:* It uses a minimalist, professional gray map tile-set from Esri to provide geographic context (state lines, cities) without visual clutter. Real-world GPS coordinates are plotted on top using Leaflet vector overlays to show where money is physically moving.

---

## 2. Backend: The Processing Engine (FastAPI)

The backend is built in **Python** using **FastAPI**, an extremely fast, asynchronous web framework designed to handle thousands of concurrent transactions.

### A. Data Handling & State Management
1.  **Ingestion:** Transactions are sent to FastAPI endpoints via standard HTTP REST requests.
2.  **Hot Cache (Redis):** Before the ML models can score a transaction, they need to know the account's recent history. The backend queries **Redis**, a lightning-fast in-memory database, to retrieve the "Hot State" (velocity, 10-minute transaction history) of the account in sub-milliseconds.
3.  **Cold Storage (PostgreSQL):** Once a transaction is fully processed and scored, the final verdict and forensic metadata are permanently logged into a PostgreSQL relational database using `asyncpg` and SQLAlchemy.
4.  **WebSocket Broadcast:** The backend simultaneously broadcasts the final verdict to the React frontend via WebSockets, triggering the map and graph animations.

---

## 3. The ML & AI Scoring Engine

SAMPATI V2 does not rely on a single algorithm; it uses a multi-layered defense-in-depth approach consisting of deterministic rules, traditional Machine Learning, and cutting-edge Generative AI.

### Layer 1: Deterministic Heuristics (Rule Engine)
Before hitting complex models, transactions pass through hardcoded algorithmic rules designed to catch mathematically impossible behavior.
*   *Example:* **Dead Money Velocity (DMV)** checks if dormant accounts suddenly burst with high-volume activity.
*   *Example:* **Geo-Velocity Checks** verify if an account initiated a transaction in Delhi and then another in Mumbai 5 seconds later (impossible travel time).

### Layer 2: Unsupervised Machine Learning
*   **Model Used:** **Isolation Forest** (Canonical ICDM 2008 algorithm).
*   *How it works:* Built in pure NumPy (with a Scikit-Learn fallback), this model is trained on a baseline of normal retail UPI transactions. Because fraud constantly evolves, this *unsupervised* model doesn't need to know what fraud looks like; it just mathematically identifies if a transaction looks "anomalous" compared to normal behavior across multiple dimensions.

### Layer 3: Supervised Machine Learning
*   **Model Used:** **Random Forest Classifier** (Binary Classification).
*   *How it works:* This custom Pure NumPy classification tree extracts 13 standardized features from the UPI payload (amount, time of day, device fingerprint, hop count). It compares these features against historical, labeled fraud signatures to generate a final probability score (0.0 to 1.0) and assigns the final verdict: `ALLOW`, `HOLD`, or `BLOCK`.

### Layer 4: Generative AI (Forensic Investigator)
*   **Model Used:** **Google Gemini LLM** (`google-generativeai` API).
*   *How it works:* If the ML pipeline issues a `BLOCK` verdict, human analysts usually have to spend hours figuring out *why* the ML model blocked it. SAMPATI solves this by feeding the raw ML scores and transaction data to Google Gemini. Gemini acts as an autonomous forensic analyst, automatically drafting a human-readable, highly detailed Suspicious Activity Report (SAR) in PDF format, explaining the exact logic behind the block.

---

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
