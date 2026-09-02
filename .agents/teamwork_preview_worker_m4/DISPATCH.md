## 2026-09-02T18:17:45Z

You are Worker for Milestone M4 (Frontend UI Command Integration & Rebranding).
Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m4

Read the following before starting:
- Original Request: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
- Scope Document: /home/avi/Downloads/Sampati_v2/PROJECT.md
- Frontend Survey Analysis: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_frontend/analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Write Ownership:
- `frontend/src/views/CaseAiCopilotView.jsx`
- `frontend/src/components/CaseDrawer.jsx`
- `frontend/src/services/api.js`
- Any frontend styling or components in `frontend/src/`

Task Instructions:
1. Rebrand all UI elements from "AI Copilot" / "Copilot" to "Gemini Assistant":
   - `frontend/src/components/CaseDrawer.jsx`: Tab label "Gemini Assistant", tooltip, icon.
   - `frontend/src/views/CaseAiCopilotView.jsx`: Header title "Gemini Assistant", subtitle, input placeholder ("Ask Gemini Assistant to analyze case, explain rules, trigger federation, simulate transactions, or block VPAs..."), suggestion prompt pills.
2. UI Command Integration & Tool Execution Display:
   - In `CaseAiCopilotView.jsx`, parse and handle `tool_executions` returned in API responses from `chatWithCopilot` / `chatWithAssistant`.
   - Render structured system message cards (`ToolExecutionCard`) inside the chat log whenever a tool is executed:
     - Shows tool type badge/icon:
       * Federation Round (🔄 Federation Intelligence Round)
       * Simulation (⚡ Synthetic Batch Simulation)
       * Block/Hold (🛑 Block / Hold VPA & Txn)
       * Export SAR PDF (📄 SAR Report PDF Export)
     - Shows status pill (e.g. `success` with emerald badge, `failed` with rose badge).
     - Shows arguments and result summary details (e.g., PSP consensus count, transaction count, frozen VPA, PDF link).
     - For SAR PDF export, provide an interactive download/open button or link.
3. Quick Command Pills:
   - Add prompt suggestions for agentic operations: "Explain why DMV score spiked", "Trigger a federation round", "Simulate 20 mule transactions", "Export SAR to PDF".
4. Verification & Clean Code:
   - Run `cd frontend && npm run lint` ensuring 0 errors and 0 warnings (`--max-warnings 0`).
   - Run `cd frontend && npm run build` ensuring successful production build.
   - Run backend tests `./.venv/bin/pytest tests/ -q` to ensure no backend regressions.

Deliverables:
Write handoff report with verification outputs to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m4/handoff.md`.
Send message back when completed.
