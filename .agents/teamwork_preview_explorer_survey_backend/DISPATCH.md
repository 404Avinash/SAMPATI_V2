# Backend Survey Explorer Dispatch

## 2026-09-02T17:41:30Z
Conduct a comprehensive investigation of the backend architecture regarding AI Copilot / Gemini Assistant.
Investigate:
1. All backend endpoints related to AI Copilot: `/cases/{case_id}/ai-briefing`, `/cases/{case_id}/ai-chat`, and any other AI/Copilot endpoints in `app/api/` or `app/routers/`.
2. How LLM/Gemini is invoked (`app/services/gemini.py` or similar service layers).
3. Data structures and models for Cases, Transactions, Rule Evaluations, and Graph/Network topology. How are they loaded and passed to AI endpoints?
4. How system prompts and user prompts are currently constructed.
5. All backend occurrences of "AI Copilot" / "Copilot" vs "Gemini Assistant" that need rebranding.
6. How the backend can structure raw case transaction history, evaluated rule breakdown, and network topology data to inject into the system prompt.
