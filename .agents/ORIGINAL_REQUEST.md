# Original User Request

## Initial Request — 2026-09-02T17:40:48Z

Upgrade the existing Gemini AI Copilot into an autonomous "Gemini Assistant". The assistant must have deep contextual awareness of the platform's inner workings and the ability to execute platform operations autonomously via function calling.

Requirements:
1. R1. Deep Context Injection & Rebranding:
   - Rename UI and backend references from "AI Copilot" to "Gemini Assistant".
   - Enhance `/cases/{case_id}/ai-briefing` and `/cases/{case_id}/ai-chat` backend endpoints to inject maximum context into the LLM system prompt (raw case transaction history, evaluated rule breakdown, network topology data, core algorithmic definitions extracted directly from `ENCYCLOPEDIA.md` to explain *exactly* why a rule fired in plain English).
2. R2. Agentic Operations (Function Calling):
   - Equip Gemini Assistant with an agentic loop (Gemini native function calling or robust prompt routing) allowing operations:
     a) Block or Hold a specific transaction/VPA.
     b) Trigger a Federation Intelligence Round.
     c) Export the SAR (Suspicious Activity Report) to PDF.
     d) Simulate a new batch of transactions.
3. R3. UI Command Integration:
   - Update frontend (e.g. `CaseAiCopilotView.jsx` or equivalent renamed component) to seamlessly display tool execution statuses in the chat log (e.g. showing system messages when Assistant triggers a federation round).

Acceptance Criteria:
- Automated Testing & Regression: Existing pytest suite (`.venv/bin/pytest tests/ -v`, 737+ tests) passes with 0 failures.
- New unit tests specifically verifying that the Gemini Assistant's chat endpoint can successfully parse and route tool execution requests for Federation and Simulation.
- Frontend UI displays "Gemini Assistant" instead of "AI Copilot".
- When a user types "Trigger a federation round" into Assistant chat, system calls backend federation execution logic and reports success.
- When a user asks "Explain why the DMV score spiked", response incorporates algorithmic definitions from Encyclopedia context.
- Frontend ESLint (`cd frontend && npm run lint`) has 0 errors/warnings and `npm run build` succeeds.

## 2026-09-03T06:46:15Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Execute the final polish and intelligence upgrade for SAMPATI V2. Integrate a true unsupervised Machine Learning model (Isolation Forest) to complement the rule engine, and wire up all dead dashboard buttons with reactive UI feedback so the platform feels dynamic and alive.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. True Machine Learning Layer (Isolation Forest)
Add a true Machine Learning model to the scoring pipeline (`app/engine/upi_scorer.py`). Implement an Unsupervised Isolation Forest (using `scikit-learn` or similar) to detect multivariate anomalies (e.g., unusual combinations of amount, time-of-day, and velocity). The output must be included in the `/upi/check` response as `ml_anomaly_score` and factored into the final verdict.

### R2. Dashboard Interactivity & API Wiring
The frontend dashboard currently feels static because several buttons are not fully wired. Ensure the "Start Live Feed", "Run batch simulation", and "Federation round" buttons on the Overview page correctly trigger their respective backend FastAPI endpoints. Specifically, the Live Feed must initiate continuous WebSocket traffic that dynamically updates the charts and topology graph.

### R3. Reactive UI Toast Notifications
Implement a toast notification system (e.g., `react-toastify`, `react-hot-toast`, or a custom component) across the dashboard. Clicking any operational button must immediately display a success/error popup (e.g., "Live Feed Started!", "Federation Round Triggered") so the user gets instant feedback.

## Verification Resources
- Existing comprehensive pytest suite (833 tests) runs via `.venv/bin/pytest tests/ -v`.
- Frontend builds via `cd frontend && npm run build`.

## Acceptance Criteria

### Automated Testing
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures.
- [ ] The frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).

### Capabilities Verification
- [ ] The `/upi/check` API response JSON explicitly includes an `ml_anomaly_score` field.
- [ ] Clicking "Start Live Feed" on the dashboard successfully initiates a stream of transactions that visibly update the "Verdict Velocity & History" chart in real-time.
- [ ] Clicking actionable buttons on the dashboard triggers a visible Toast Notification confirming the action.
</USER_REQUEST>

## 2026-09-03T07:02:48Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Execute the final ML/UI polish and completely overhaul the dashboard's terminology to align with the new "Collaborative Fraud-Intelligence Mesh" narrative. The system must wire up dead buttons, add an Isolation Forest ML model, and strip out all overambitious claims in favor of defensible, signal-correlation phrasing.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. True Machine Learning Layer (Isolation Forest)
Add a true Machine Learning model to the scoring pipeline (`app/engine/upi_scorer.py`). Implement an Unsupervised Isolation Forest (using `scikit-learn` or similar) to detect multivariate anomalies (e.g., unusual combinations of amount, time-of-day, and velocity). The output must be included in the `/upi/check` response as `ml_anomaly_score` and factored into the final verdict.

### R2. Terminology & UI Overhaul (The Pivot)
Execute a global overhaul across the frontend and backend to align with the new narrative. Replace "Dead Money Velocity" with "Dormant-to-Active Velocity". Replace "Criminal Network" or "Criminal Hierarchy" with "Suspected Mule Cluster". Remove any claims of "100% confidence" or "100% traceable" from the UI. Add the tagline "Everyone sees a piece. SAMPATI connects the dots." prominently to the Overview dashboard headers.

### R3. Dashboard Interactivity & API Wiring
Ensure the "Start Live Feed", "Run batch simulation", and "Federation round" buttons on the Overview page correctly trigger their respective backend FastAPI endpoints. Specifically, the Live Feed must initiate continuous WebSocket traffic that dynamically updates the charts and topology graph. Implement a reactive toast notification system across the dashboard to provide immediate visual feedback for all button clicks.

## Verification Resources
- Existing comprehensive pytest suite (833 tests) runs via `.venv/bin/pytest tests/ -v`.
- Frontend builds via `cd frontend && npm run build`.

## Acceptance Criteria

### Automated Testing
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures.
- [ ] The frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).

### Capabilities Verification
- [ ] The `/upi/check` API response JSON explicitly includes an `ml_anomaly_score` field.
- [ ] A `grep` of the frontend source code returns 0 results for "Dead Money Velocity" and "Criminal Network".
- [ ] Clicking "Start Live Feed" on the dashboard successfully initiates a stream of transactions that visibly update the "Verdict Velocity & History" chart in real-time.
- [ ] Clicking actionable buttons on the dashboard triggers a visible Toast Notification confirming the action.
</USER_REQUEST>

## 2026-09-03T09:32:24Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Execute the massive "Intelligence Mesh" pivot based on the updated PRD. Build the new Early-Warning Signal ingestion backend and a dedicated "Threat Intelligence" dashboard tab to visualize pre-transaction social engineering threats. Simultaneously, complete the interrupted final polish: integrate the Isolation Forest ML model, wire all dead UI buttons, and execute the global terminology overhaul to enforce the "SAMPATI connects the dots" narrative.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. Early Warning Intelligence Layer (Backend)
Build the backend infrastructure (FastAPI routes + PostgreSQL models) to ingest "Pre-Transaction" threat signals. This must accept standard fraud signal JSON payloads (e.g., from the external mobile app or mock PSPs) containing identifiers (Phone, UPI ID, URL) and social engineering tags (e.g., "Bank impersonation", "Urgency"). These signals must automatically link to the central Fraud Graph.

### R2. Threat Intelligence Dashboard (Frontend)
Create a dedicated "Threat Intelligence" tab in the React frontend's top navigation bar. This view must visualize the incoming pre-transaction signals in real-time, display suspected Campaign clustering metrics (e.g., "Campaign similarity: 94%"), and explicitly visualize the entity extraction flow (SMS -> Phone/UPI/URL -> Graph).

### R3. Pitch Pivot & ML Polish (The Interrupted Tasks)
1. **ML Layer**: Add an Unsupervised Isolation Forest model (using `scikit-learn`) to `app/engine/upi_scorer.py` and output `ml_anomaly_score`.
2. **Terminology**: Execute a global find-and-replace to change "Dead Money Velocity" to "Dormant-to-Active Velocity", "Criminal Network" to "Suspected Mule Cluster", and strip all "100% confidence" claims. Add the tagline "Everyone sees a piece. SAMPATI connects the dots."
3. **UI Wiring**: Ensure the "Start Live Feed" and "Run batch simulation" buttons trigger real traffic. Implement reactive Toast Notifications for all button clicks.

## Verification Resources
- Existing comprehensive pytest suite (833 tests) runs via `.venv/bin/pytest tests/ -v`.
- Frontend builds via `cd frontend && npm run build`.

## Acceptance Criteria

### Automated Testing
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures, ensuring the new ingestion endpoints do not break existing evaluations.
- [ ] The frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).

### Capabilities Verification
- [ ] A new "Threat Intelligence" tab exists in the UI and displays a list of pre-transaction threat reports.
- [ ] The `/upi/check` API response JSON explicitly includes an `ml_anomaly_score` field.
- [ ] A `grep` of the frontend source code returns 0 results for "Dead Money Velocity" and "Criminal Network".
- [ ] Clicking "Start Live Feed" on the dashboard successfully initiates a stream of transactions that visibly update the charts in real-time with Toast notification feedback.
</USER_REQUEST>
