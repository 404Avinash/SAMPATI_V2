# Plan — SAMPATI V2 Upgrade Orchestration

## Strategy
Following the Teamwork Project Pattern:
1. **Phase 0: Survey**
   - Spawn 3 parallel Explorers:
     - Explorer 1: Backend architecture, persistence layer (in-memory state, models, FastAPI endpoints, Docker/deploy scripts, PostgreSQL driver setup).
     - Explorer 2: Real-Time WebSocket & Frontend Live Feed/KPI counters (existing /ws/ endpoint, frontend WS integration, state management).
     - Explorer 3: Interactive Constellation Visualizer (canvas graph, node hover/click, edge coloring/amount tooltips) and Verdict History Line Chart (Recharts integration below KPI strip).
2. **Phase 1: Architecture & Decomposition (PROJECT.md & TEST_INFRA.md)**
   - Synthesize survey findings.
   - Decompose into Milestones (M1-M4) with strict interface contracts.
   - Parallel E2E Testing Track initialization.
3. **Phase 2: Execution of Milestones**
   - Direct iteration loop or sub-orchestrator per milestone:
     - Explorer -> Worker -> Reviewers -> Challenger -> Auditor -> Gate.
4. **Phase 3: E2E Integration & Verification**
   - Full test suite run across all tiers (Tiers 1-4).
   - Adversarial verification (Tier 5).
5. **Phase 4: Completion & Victory Report**
