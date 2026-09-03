# DISPATCH: teamwork_preview_worker_m1_fix

## Identity
- Role: Worker for Milestone 1 Iteration 2 (Remediation of Challenger 1 Edge Cases)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_fix
- Parent: teamwork_preview_orchestrator_11 (Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4)

## Mandatory Integrity Warning
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Mission & Inputs
- Read Challenger 1 findings: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1/handoff.md`.
- Read Challenger 1 test suite: `/home/avi/Downloads/Sampati_v2/tests/test_threat_intel_adversarial_challenger.py`.
- Target files:
  1. `app/models/threat_intel.py`
  2. `app/services/graph_service.py`
  3. `app/services/threat_intel_service.py`

## Remediation Tasks
1. **URL Trailing Parentheses (`app/models/threat_intel.py`)**:
   In `extract_entities(text)`:
   Strip trailing punctuation including `)`:
   `u = m.group(1).rstrip(".,;:!?)>\"'")`
   Also refine `URL_REGEX` to avoid including closing parentheses when not matched by an opening parenthesis.

2. **Enterprise / Subdomain Email Non-Collision in `UPI_REGEX` (`app/models/threat_intel.py`)**:
   In `UPI_REGEX`:
   The current regex matches `username@handle` but when encountering `support@alerts.hdfcbank.com`, it matches `support@alerts` because `.hdfcbank.com` is after `@alerts`.
   Fix `UPI_REGEX` by ensuring that after the handle there is NO dot followed by domain letters (`(?!\.[a-zA-Z]{2,})`) or by requiring word boundary `\b` where the handle is NOT immediately followed by a dot and another subdomain/domain.
   Verify that:
   - `support@alerts.hdfcbank.com` is NOT extracted as a UPI VPA.
   - `john.doe@corporate.company.co.in` is NOT extracted as a UPI VPA.
   - Genuine UPI VPAs like `phish_trap@oksbi`, `merchant@hdfcbank`, `user.name@paytm`, `someone@ybl` ARE correctly extracted.

3. **None Guard in `FraudGraphService` (`app/services/graph_service.py`)**:
   In `_resolve_node_id(self, entity_id, entity_type)` and `get_subgraph(self, entity_id, depth)`:
   Add guard:
   ```python
   if not entity_id or not isinstance(entity_id, str):
       return ""  # or return empty graph / safe fallback
   ```
   Ensure `g.get_subgraph(None)` returns an empty subgraph dict `{"nodes": [], "edges": []}` without raising `AttributeError`.

4. **None/Non-String Filter in `compute_campaign_similarity` (`app/services/threat_intel_service.py`)**:
   In `compute_campaign_similarity`:
   Safely handle tags containing `None` or non-string items:
   ```python
   tag_str = " ".join(str(t) for t in tags if t is not None).lower()
   ```

5. **Verification**:
   - Run Challenger 1 test suite: `./.venv/bin/pytest tests/test_threat_intel_adversarial_challenger.py -v` (must pass 100%).
   - Run original M1 test suite: `./.venv/bin/pytest tests/test_threat_intel_r1.py -v` (must pass 30/30).
   - Run linter: `./.venv/bin/ruff check app tests` (0 errors).
   - Run master regression: `./.venv/bin/pytest tests/ -q` (0 failures).

Write handoff report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_fix/handoff.md` and send message to parent.

## 2026-09-03T10:43:02Z
You are teamwork_preview_worker_m1_fix.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_fix.
Read your instructions at /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_fix/DISPATCH.md.
Also read:
- /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_m1_1/handoff.md
- /home/avi/Downloads/Sampati_v2/tests/test_threat_intel_adversarial_challenger.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Remediate the 4 defects:
1. Strip trailing parentheses and punctuation on URLs in `extract_entities` in `app/models/threat_intel.py`.
2. Ensure `UPI_REGEX` in `app/models/threat_intel.py` rejects multi-subdomain/enterprise emails like `support@alerts.hdfcbank.com` and `user@mail.google.com` (do not extract `support@alerts`).
3. Add None/empty guard in `_resolve_node_id` and `get_subgraph` in `app/services/graph_service.py` to prevent AttributeError.
4. Filter None/non-string items in `compute_campaign_similarity` in `app/services/threat_intel_service.py` to prevent TypeError.

Verify with:
- `./.venv/bin/pytest tests/test_threat_intel_adversarial_challenger.py -v`
- `./.venv/bin/pytest tests/test_threat_intel_r1.py -v`
- `./.venv/bin/ruff check app tests`

Write report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_fix/handoff.md` and report completion back to parent via send_message.
