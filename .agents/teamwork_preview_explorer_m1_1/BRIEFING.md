# BRIEFING — 2026-09-03T10:17:00Z

## Mission
Investigate and design complete technical specifications for Pydantic models in `app/models/threat_intel.py` (with robust Indian regex entity extraction for Phone, UPI ID, URL, and social engineering tags) and SQLAlchemy `ThreatSignalModel` in `app/models/upi_persistence.py` for Milestone M1 Early Warning Intelligence Layer.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, analyzer, synthesizer
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1
- Original parent: 708f3126-0948-4197-8593-5296c58527f6
- Milestone: M1 (Encyclopedia Knowledge Base)
- Updated Assignment: M1 (Threat Intel Schemas, Regex Entity Extraction, DB Persistence)
- Current Orchestrator Parent: 93ffe563-3fed-400b-b381-966248be98c4

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Extract comprehensive formula dictionary and explanation templates
- Write analysis to .agents/teamwork_preview_explorer_m1_1/analysis.md
- Produce handoff to .agents/teamwork_preview_explorer_m1_1/handoff.md
- Deliver complete, drop-in Python technical specifications and code for `app/models/threat_intel.py` and `app/models/upi_persistence.py`
- Ensure dual-mode database persistence compatibility with PostgreSQL and offline in-memory fallback

## Current Parent
- Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4
- Updated: 2026-09-03T10:17:00Z

## Investigation State
- **Explored paths**:
  * `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (R1 Early Warning Intelligence Layer, lines 352-354)
  * `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md` (M1 Feature scope, R1 interface contracts)
  * `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md` (Survey architecture & R1 findings)
  * `app/models/upi_models.py` (BaseModel patterns, Field, utcnow helper)
  * `app/models/upi_persistence.py` (Base, UpiBase, JSON_TYPE, compound indexes, mock mode)
  * `app/db/session.py` (init_db, get_engine, in-memory fallback)
  * `app/engine/campaign.py` (CampaignSignatureStore, FRAUD_KEYWORD_CLUSTERS, compute_similarity)
  * `tests/test_m1_persistence.py` (declarative schema validation, passing tests)
- **Key findings**:
  1. Regex for Indian mobile numbers handles +91/91/0 prefixes, formats with spaces/hyphens, and enforces boundary checking to prevent 12-digit UTR/transaction ID collisions.
  2. Regex for UPI IDs (`[a-zA-Z0-9.\-_]{2,64}@...`) strictly avoids email providers (.com, .in, etc.) and accurately extracts valid bank/PSP handles.
  3. URL regex captures http/https, IP endpoints, www, and phishing TLDs while avoiding trailing punctuation and email false positives via negative lookbehind `(?<!@)`.
  4. Tag categorization covers all 8 major Indian social engineering scam vectors.
  5. `ThreatSignalModel` seamlessly integrates with `Base.metadata.tables` under `threat_signals`, supports JSON/JSONB, foreign keys to `upi_cases` and `mule_rings`, and has graceful in-memory and mock fallback.
- **Unexplored areas**: None within the scope of M1 schemas and persistence models.

## Key Decisions Made
- Provided standalone pure-Python regex extraction function `extract_entities(text: str) -> ExtractedEntities` with zero external dependencies.
- Standardized `ThreatSignalCreateRequest` to accept either structured fields, raw SMS/message text, or both, automatically extracting entities when unstructured content is supplied.
- Designed `ThreatSignalModel` with four compound indexes for rapid query performance: `(source, created_at)`, `(severity, created_at)`, `(phone, created_at)`, and `(upi_id, created_at)`.
- Designed `to_dict()` and `__init__` methods on `ThreatSignalModel` to ensure 100% test compatibility with both PostgreSQL/SQLite async sessions and mock test environments.

## Artifact Index
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/handoff.md — Complete 5-component technical specifications and code for M1
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/progress.md — Liveness heartbeat
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/DISPATCH.md — Incoming message dispatch log
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/BRIEFING.md — Situational memory and state

