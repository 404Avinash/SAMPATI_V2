# DISPATCH: teamwork_preview_explorer_m1_1

## Identity
- Role: Explorer 1 for Milestone 1 (Backend Schemas, Regex Entity Extraction, DB Persistence)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1
- Parent: teamwork_preview_orchestrator_11

## Mission & Inputs
- Read authoritative request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (lines 336–379, R1 Early Warning Intelligence Layer).
- Read project scope & architecture: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`.
- Read previous survey findings: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md`.
- Inspect existing models: `app/models/upi_models.py`, `app/models/upi_persistence.py`, `app/db/session.py`.

## Assignment
1. Investigate and specify the exact Pydantic schemas in `app/models/threat_intel.py`:
   - `ThreatSignalCreateRequest`: source, phone, upi_id, url, tags, raw_content, severity, confidence.
   - Robust regex extraction logic for Indian phone numbers (10 digits with optional +91/0), UPI IDs (alphanumeric/dot/hyphen@handle), URLs (http/https/domain), and social engineering tags ("Bank impersonation", "Urgency", "Lottery/Reward", "Electricity/Bill", "KYC suspension", "APK/Malware", etc.).
   - `ExtractedEntities`, `ThreatSignalResponse`, `ThreatSignalListResponse`.
2. Investigate and specify the exact SQLAlchemy model `ThreatSignalModel` in `app/models/upi_persistence.py`:
   - Columns: `id`, `signal_id`, `source`, `phone`, `upi_id`, `url`, `tags` (JSON/ARRAY), `raw_content`, `severity`, `confidence`, `extracted_entities` (JSON), `matched_campaign_id`, `matched_campaign_name`, `similarity_score`, `case_id` (ForeignKey optional), `ring_hash` (ForeignKey optional), `created_at`.
   - Ensure compatibility with `UpiBase` and in-memory fallback mode.
3. Write your complete findings and implementation plan to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_m1_1/handoff.md`.
4. Report completion back to parent via `send_message`.
