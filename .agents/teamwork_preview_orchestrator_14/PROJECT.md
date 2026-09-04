# Project: SAMPATI V2 — UI Critical Bugs & India Geo Map Visualization

## Architecture
Frontend Single Page Application (React 18 + Vite + Tailwind CSS) with backend FastAPI services:
- **Threat Intel Flow**: `ThreatIntelPage.jsx` communicates with `/intel/signals` and `/intel/campaigns`. Displays Pre-Transaction Signals, Entity Extraction Flow, and Suspected Campaign Clusters.
- **Topology Visualizer**: `OverviewPage.jsx` hosts the network topology visualizer. Supports dual views: canvas-based force simulation (`NetworkConstellation.jsx`) and vector-based geographic map (`GeoMuleMap.jsx`).
- **Constellation Engine**: Canvas 2D force simulation rendering transaction nodes, fraud corridors, particle pulses, and playback timeline.
- **Velocity Engine**: Real-time sliding window telemetry tracking transaction verdicts (ALLOW, HOLD, BLOCK) per second (`AppStateContext.jsx`, `VerdictHistoryChart.jsx`).

## Feature Inventory
| # | Feature | Description | Milestone | Status | Source |
|---|---------|-------------|-----------|--------|--------|
| 1 | R1. Geographic India Map Visualization | Add `GeoMuleMap.jsx` rendering stylized India map with animated arcs between major hubs (Mumbai, Bengaluru, Delhi, Jamtara, Mewat, Kolkata, etc.) and integrate into Overview/Threat Intel | M1 | DONE | Survey 1 |
| 2 | R2. Fix Threat Intel Page Crash | Fix runtime object-rendering error in `ThreatIntelPage.jsx` (`matched_campaign` object in JSX) with defensive extraction, identifier aliases, and ErrorBoundary | M1 | DONE | Survey 1 |
| 3 | R3. Whitewash Constellation Graph | Change `NetworkConstellation.jsx` canvas background to `#ffffff`, high-contrast node borders/shadows, saffron active stroke, clear risk edge gradients, and light HUD theme | M1 | DONE | Survey 2 |
| 4 | R4. Fix Verdict Velocity Rolling Rate | Update `AppStateContext.jsx` with 1s sliding window bucket aggregator, update `VerdictHistoryChart.jsx` to show TPS rate instead of cumulative total, and provide `VerdictVelocityChart.jsx` alias | M1 | DONE | Survey 3 |

## Code Layout & File Boundaries
- `frontend/src/components/overview/GeoMuleMap.jsx` (New file): Geographic India map component
- `frontend/src/components/common/ErrorBoundary.jsx` (New file): Safe error boundary wrapper
- `frontend/src/components/VerdictVelocityChart.jsx` (New file): Re-export alias for test contracts & imports
- `frontend/src/pages/ThreatIntelPage.jsx`: Safe campaign label rendering & entity extraction
- `frontend/src/components/NetworkConstellation.jsx`: Canvas whitening, color contrast, and light HUD
- `frontend/src/context/AppStateContext.jsx`: 1-second discrete bucket sliding window TPS aggregator
- `frontend/src/components/VerdictHistoryChart.jsx`: Rolling rate presentation, header TPS counter, rate tooltip
- `frontend/src/pages/OverviewPage.jsx`: Topology view toggle (Constellation vs India Map)

## Milestones
| # | Name | Scope | Dependencies | Status | Key Outputs |
|---|------|-------|-------------|--------|-------------|
| 1 | UI Critical Bugs & India Geo Map | R1, R2, R3, R4 implementation, testing, and verification | Survey Complete | DONE | 8 frontend files updated/created; 969 pytest passed; 0 ESLint warnings; Vite build clean |

## Interface Contracts
- **GeoMuleMap Component**:
  `GeoMuleMap({ cases = [], threatSignals = [], onSelectCase })`
- **ThreatIntel Campaign Label**:
  `getCampaignLabel(campaign: string | { campaign_id?: string, name?: string, campaign_name?: string }) => string | null`
- **Verdict Velocity Time-Series Point**:
  `{ time: string, timestamp: number, ALLOW: number, HOLD: number, BLOCK: number, allowed: number, held: number, blocked: number, total: number }` (where rates represent transactions per second)
