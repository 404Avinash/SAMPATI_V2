# DISPATCH: teamwork_preview_challenger_m1_1

## Identity
- Role: Challenger 1 for Milestone 1 (Adversarial Empirical Verification)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1
- Parent: teamwork_preview_orchestrator_11 (Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4)

## Mission & Inputs
- Authoritative request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (lines 336–379, R1).
- Scope & architecture: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`.
- Target files: `app/models/threat_intel.py`, `app/services/graph_service.py`, `app/services/threat_intel_service.py`, `app/api/intel.py`.

## Adversarial Verification Objectives
1. Stress-test regex entity extractor with dirty, adversarial inputs:
   - Nested numbers, 12-digit UPI reference numbers (UTRs), timestamps like 202609031234, international prefixes (+1, +44).
   - Unusual email vs UPI VPA collisions (e.g. `test@gmail.com` vs `merchant@okhdfcbank`).
   - Obfuscated URLs: `hxxp://`, IP addresses with ports, subdomains with unicode/punycode, trailing periods/slashes.
   - Mixed multi-lingual text or zero-width spaces in social engineering keywords.
2. Stress-test `FraudGraphService` under rapid concurrent node and edge additions, cycles, self-loops, and deep ego-graph queries.
3. Test campaign similarity calculation across corner cases (empty tags, conflicting tags, single character strings).
4. Run empirical verification scripts using `./.venv/bin/python`.
5. Issue verdict: `APPROVE` or `REJECT` (with concrete failure reproductions).
6. Write report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1/handoff.md`.
7. Send completion message to parent.

## 2026-09-03T10:36:08Z
You are teamwork_preview_challenger_m1_1.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1.
Read your instructions at /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1/DISPATCH.md.
Also read:
- /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md

Adversarially stress-test:
1. Regex entity extraction (`extract_entities`) with dirty, obfuscated, and boundary-colliding inputs (12-digit UTRs, timestamps, email vs VPA collision, dirty URLs).
2. `FraudGraphService` under high-frequency updates, cycles, self-loops, and ego-graph queries.
3. Campaign similarity calculations on edge-case inputs.

Run empirical verification using `./.venv/bin/python`.
Issue a verdict: APPROVE or REJECT.
Write report to /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1/handoff.md.
Report completion back to parent via send_message.
