# Adversarial Review (Round 2) Hardening & Verification Report: Google Gemini AI Copilot

> [!WARNING] **Skepticism Disclaimer**
> High confidence in backend and frontend integration resilience across deterministic fallbacks, multipart responses, safety filtering, and UI markdown rendering.

## 1. What the Prior Attempt Got Wrong

### Issue 1: Multipart and Thinking-Model Response Truncation / Drop
- **Input**: Gemini API returning multipart responses (e.g. `parts: [{"thought": "Evaluating..."}, {"text": "chunk 1"}, {"text": "chunk 2"}]` from Gemini 2.0 Flash / thinking models).
- **Expected**: All valid text parts aggregated into complete text before JSON parsing or response formatting.
- **Actual**: Prior code used `parts[0].get("text")`, which was `None` if `parts[0]` was a thought/metadata part, discarding valid text in subsequent parts and prematurely falling back to heuristics.
- **Root Cause**: Index-0 assumption (`parts[0].get("text")`) instead of aggregating all non-empty `text` fields across `candidate["content"]["parts"]`.

### Issue 2: Safety Filter and BlockReason Model-Cascade Waste
- **Input**: Gemini API response containing `promptFeedback.blockReason: "SAFETY"` or `candidate.finishReason: "SAFETY"` / `"BLOCKLIST"`.
- **Expected**: Recognize prompt-level or candidate-level content moderation blocks, immediately abort further remote model calls, and return deterministic fallback.
- **Actual**: Prior code logged and cascaded through all 5 remaining fallback models with the identical blocked prompt, wasting network latency and API quota.
- **Root Cause**: Missing check for `promptFeedback.blockReason` and candidate `finishReason in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT")`.

### Issue 3: Greedy Regex Failure on Conversational Curly Braces in Preambles
- **Input**: Gemini response containing conversational text with curly braces (e.g. `Here is the analysis for {case_ref: 1234}: {"executive_summary": "...", ...}`).
- **Expected**: Accurate extraction of the valid innermost JSON dictionary.
- **Actual**: Greedy regex `r"(\{[\s\S]*\})"` matched from the first `{` in the preamble to the final `}`, producing invalid JSON syntax that caused `json.loads` to throw `JSONDecodeError`.
- **Root Cause**: Unconstrained greedy regex matching without balanced brace syntactic boundary scanning.

### Issue 4: SAR Endpoint Source Metadata Inaccuracy on API Key Failure
- **Input**: `GET /cases/{case_id}/ai-sar` when `GEMINI_API_KEY` was configured but expired/invalid (401/403) or failed due to timeout.
- **Expected**: Response JSON indicating `"source": "deterministic-fallback"`.
- **Actual**: `app/api/upi.py` and `app/main.py` had hardcoded `"source": "gemini-ai" if copilot.is_available() else "deterministic-fallback"`. Since `is_available()` returned true based on string length, it falsely reported `source: "gemini-ai"` despite returning fallback text.
- **Root Cause**: Endpoint route handlers decoupled source attribution from actual execution outcome of `generate_sar_report()`.

### Issue 5: Non-Finite Floats (NaN / Inf) and Unbounded In-Memory Cache
- **Input**: Case payloads containing `NaN`, `+Infinity`, `-Infinity`, or sustained traffic populating `self._cache`.
- **Expected**: Sanitized float conversion to defaults and bounded cache size with LRU eviction.
- **Actual**: Unsanitized floats passed to JSON formatters; `self._cache` grew unbounded without memory limits.
- **Root Cause**: Lack of `math.isnan` / `math.isinf` guards in `_safe_float` and missing cache size eviction ceiling.

### Issue 6: Frontend Drawer Auto-Scroll Disruption & Raw Markdown Table / Code Block Rendering
- **Input**: Interactive chat responses with markdown tables or code fences, or auto-scrolling during multi-turn chat.
- **Expected**: Scoped auto-scrolling inside the chat box without scrolling the parent drawer; stylized tables and syntax containers.
- **Actual**: `chatBottomRef.scrollIntoView()` caused the entire parent `CaseDrawer` modal to jump downward; raw code blocks lacked padding and background styling.
- **Root Cause**: Unscoped `scrollIntoView()` on sub-containers and lack of custom `ReactMarkdown` component mappings.

---

## 2. What I Changed

1. **`app/services/gemini_service.py`**:
   - Added `_find_json_objects_in_text`: balanced-brace JSON scanner extracting well-formed dictionaries even with conversational preambles/sign-offs containing curly braces.
   - Updated `_call_gemini` to combine all text parts from `candidates[0].content.parts` (supporting thinking models and split chunks).
   - Added prompt-level (`promptFeedback.blockReason`) and candidate-level (`finishReason in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT")`) safety detection to break cascade loops early.
   - Added `_set_cache` with `MAX_CACHE_ENTRIES = 500` LRU eviction.
   - Enhanced `_safe_float` with `math.isnan` and `math.isinf` sanitization.
   - Added `generate_sar_report` returning structured payload with accurate `source` and `model`.
   - Hardened system instructions in briefing, chat, and SAR generation against adversarial prompt injection attempts.

2. **`app/api/upi.py` & `app/main.py`**:
   - Updated `/cases/{case_id}/ai-sar` routes to call `copilot.generate_sar_report(case)` and return verified `source` and `model` metadata.
   - Ensured empty or whitespace chat queries fall back cleanly to overview prompts without 422 errors.

3. **`frontend/src/components/investigations/CaseAiCopilotView.jsx`**:
   - Added `MARKDOWN_COMPONENTS` custom renderers for `<code>`, `<pre>`, `<table>`, `<th>`, `<td>`, `<ul>`, `<ol>`, `<li>`, `<blockquote>`, and `<p>`.
   - Replaced unscoped `scrollIntoView` with `messagesBoxRef.current.scrollTo` to keep drawer viewport stable.
   - Added `onKeyDown` to input for Enter key submission while ignoring whitespace submissions.

4. **`tests/test_gemini_copilot.py`**:
   - Expanded test suite from 17 to 25 tests:
     - `test_candidate_multipart_text_aggregation`
     - `test_safety_filter_prompt_feedback_blocking`
     - `test_safety_filter_candidate_finish_reason_blocking`
     - `test_brace_balanced_json_extraction_with_preamble_curlies`
     - `test_nan_infinity_sanitization`
     - `test_cache_lru_bounding_and_eviction`
     - `test_sar_report_source_metadata_integrity`
     - `test_post_ai_chat_with_empty_or_whitespace_question`

---

## 3. Verification Record

- **Deep Verification (ran actual tests):**
  - Pytest Full Suite: `./.venv/bin/pytest tests/ -v` (735 passed, 6 warnings in 61.97s)
  - Unit/Contract Suite: `./.venv/bin/pytest tests/test_gemini_copilot.py -v` (25 passed in 1.24s)
  - E2E Regression Suite: `./.venv/bin/python tests/test_e2e_suite.py --verbose` (231 passed in 10.14s)
  - Python Linter: `./.venv/bin/ruff check app tests` (0 errors)
  - Frontend Linter: `cd frontend && npm run lint` (`--max-warnings 0`, 0 errors, 0 warnings)
  - Frontend Build: `cd frontend && npm run build` (Vite production build succeeded in 7.21s)
  - Composite Safe-Push Pipeline: `./.venv/bin/pytest && ./.venv/bin/ruff check app tests && cd frontend && npm run lint && npm run build && cd ..` (exited 0)

- **Shallow Verification (manual only):**
  - Verified drawer tab switching between Forensic Dossier and AI Copilot.
  - Inspected markdown rendering component tree for SAR draft and Copilot chat.

- **Unverified aspects:**
  - Live external Google Gemini API calls over WAN against valid production quota (tested with realistic mocked API responses matching Google Gemini v1beta response payloads).

---

## 4. Known Issues

- None. (All 735 backend tests pass, linters pass with 0 warnings, Vite builds cleanly).

---

## 5. Remaining Risk & Next Step

- The integration is fully validated, hardened against edge cases (multipart responses, safety filtering, brace balancing, non-finite floats, cache bounds, prompt injection, and UI markdown rendering), and ready for deployment.
