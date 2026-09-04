# BRIEFING — 2026-09-04T01:50:30Z

## Mission
Investigate and design R2: Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP) & Frontend Dashboard Integration for SAMPATI V2.

## 🔒 My Identity
- Archetype: explorer
- Roles: Read-only investigation, problem analysis, synthesizing findings, producing structured reports
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r2
- Original parent: dcfa3ce2-0d8a-4c92-b530-f081ee91ac86
- Milestone: R2 - Simulated Institutional Signal Adapters & Frontend Integration

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Base working directory strictly within .agents/teamwork_preview_explorer_survey_r2
- Propose concrete implementation designs, exact file paths, schemas, and verification steps

## Current Parent
- Conversation ID: dcfa3ce2-0d8a-4c92-b530-f081ee91ac86
- Updated: 2026-09-04T01:50:30Z

## Investigation State
- **Explored paths**:
  - `app/models/threat_intel.py`, `app/models/upi_models.py`
  - `app/api/intel.py`, `app/api/upi.py`, `app/api/federation.py`
  - `app/engine/honeypot.py`, `app/engine/upi_rules.py`, `app/engine/upi_scorer.py`
  - `app/services/upi_cases.py`, `app/services/threat_intel_service.py`
  - `frontend/src/components/CaseDrawer.jsx`, `frontend/src/pages/ThreatIntelPage.jsx`, `frontend/src/pages/OverviewPage.jsx`, `frontend/src/components/LiveFeed.jsx`
- **Key findings**:
  - StandardFraudSignal format maps directly to `ThreatSignalCreateRequest` in `app/models/threat_intel.py`.
  - Honeypots are identified in `app/engine/honeypot.py` with `DEFAULT_HONEYPOTS` and `HONEYPOT_PREFIXES`.
  - Mock NPCI MuleHunter Adapter: returns deterministic mule probability (0.96 HIGH for honeypots/known bad, hash-based low for clean).
  - Mock DPIP Smart Registry Adapter: queries/updates national registry by VPA or SHA-256 hash (returns threat level HIGH / 0.90 for bad, CLEAN / 0.0 for clean).
  - Mock PSP Adapter: generates `StandardFraudSignal` payloads with tags, severity, and pushes to mesh graph.
  - `/upi/check` response schema needs `mock_npci_score: float`, `mock_dpip_threat_level: Union[float, int, str]`, and `contributing_signals: List[Dict[str, Any]]`.
  - Frontend components (`CaseDrawer.jsx`, `ThreatIntelPage.jsx`, `LiveFeed.jsx`) need institution labels (NPCI, DPIP, PhonePe, Paytm).
- **Unexplored areas**: None. All requirements analyzed in full depth.

## Key Decisions Made
- Architected comprehensive adapter framework in `app/adapters/` with clean Pydantic models and REST endpoints.
- Designed 100% deterministic VPA mapping ensuring honeypot and known-bad VPAs always return HIGH from mock NPCI and non-zero `mock_npci_score` & `mock_dpip_threat_level`.

## Artifact Index
- DISPATCH.md — Task assignment and requirements
- BRIEFING.md — Situational awareness and working memory
- progress.md — Liveness heartbeat and step tracking
- handoff.md — 5-component structured investigation report
