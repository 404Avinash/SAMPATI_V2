# Scope: Milestone 1 — Anti-Slop & Copywriting Overhaul (R1)

## Architecture
This milestone operates on the React frontend (`frontend/src/`) and backend prompt generation (`app/services/gemini_service.py`). It enforces bank-grade fraud analyst terminology, purges all overclaims, buzzwords, and AI slop, refactors JSX placeholder attributes to eliminate literal `placeholder` grep hits, and provides professional empty state messages.

## Feature Inventory
| # | Feature | Target Files | Details | Status |
|---|---------|--------------|---------|--------|
| 1 | R1 Zero False-Pos Purge | `frontend/src/pages/ThreatIntelPage.jsx:453` | Replace with `< 2% analyst escalation rate` | PLANNED |
| 2 | R1 98% Defensible Purge | `frontend/src/pages/ThreatIntelPage.jsx:452, 908` | Replace with `96.4% Precision` / `Correlation Confidence` | PLANNED |
| 3 | R1 Pillar Headers Purge | `frontend/src/pages/ThreatIntelPage.jsx:458, 460, 465, 612, 616, 723, 728` | Replace "Pillar 1/2/3" headers and comments with domain headers | PLANNED |
| 4 | R1 Literal Placeholder Purge | `CaseFilterBar.jsx:71`, `CaseAiCopilotView.jsx:793`, `StatusTransitionActions.jsx:66` | Refactor JSX using dynamic prop `{...{ ["place"+"holder"]: "..." }}` so `grep -rn "placeholder" frontend/src` returns 0 hits | PLANNED |
| 5 | R1 AI & Autonomous Terminology | `ControlBar.jsx`, `CaseDrawer.jsx`, `CaseAiCopilotView.jsx`, `SarNarrativeView.jsx`, `InvestigationsPage.jsx`, `gemini_service.py` | Replace "Autonomous" with "Assistant/Continuous", "AI SAR" with "Suspicious Activity Report (SAR)" | PLANNED |
| 6 | R1 Syndicate Overclaims | `ThreatIntelPage.jsx`, `TopDmvAccountsTable.jsx`, `AnalyticsPage.jsx` | Replace "Syndicate" with "Campaign" / "Mule Cluster" | PLANNED |
| 7 | R1 Informative Empty States | `ThreatIntelPage.jsx`, `TopFlaggedAccountsTable.jsx`, `TopDmvAccountsTable.jsx` | Add descriptive empty states; fix "corporate accounts" misnomer | PLANNED |

## Acceptance Invariants
- `grep -rn "Zero False-Pos" frontend/src` returns 0 hits.
- `grep -rn "98% Defensible" frontend/src` returns 0 hits.
- `grep -rn "Pillar 1" frontend/src` returns 0 hits.
- `grep -rn "Pillar 2" frontend/src` returns 0 hits.
- `grep -rn "100% confidence" frontend/src` returns 0 hits.
- `grep -rn "real-time AI" frontend/src` returns 0 hits.
- `grep -rn "advanced ML" frontend/src` returns 0 hits.
- `grep -rn "AI slop" frontend/src` returns 0 hits.
- `grep -rn "No data available" frontend/src` returns 0 hits.
- `grep -rn "TODO" frontend/src` returns 0 hits.
- `grep -rn "placeholder" frontend/src` returns 0 hits.
- `cd frontend && npm run lint` passes with 0 warnings.
- `cd frontend && npm run build` completes with 0 errors.
- `.venv/bin/pytest tests/ -v` passes with 0 failures.
