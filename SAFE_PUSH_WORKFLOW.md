# SAMPATI_V2 Safe Push Workflow & Fast Execution Guide

This document defines the automated verification and push workflow for the **SAMPATI_V2** repository so any AI agent or developer can commit and push changes safely without full codebase re-exploration.

---

## 🚀 Fast Automated Push Command

To validate and push changes in a single line:

```bash
./.venv/bin/pytest && ./.venv/bin/ruff check app tests && (cd frontend && npm run lint && npm run build) && git add . && git commit -m "feat: updates" && git push origin main
```

---

## 🛠️ Verification Checklist Details

| Stage | Command | Location | Success Criteria |
| :--- | :--- | :--- | :--- |
| **Backend Unit Tests** | `./.venv/bin/pytest` | Workspace Root | 559/559 tests pass |
| **E2E Integration** | `./.venv/bin/python tests/test_e2e_suite.py` | Workspace Root | 231/231 tests pass |
| **Python Linter** | `./.venv/bin/ruff check app tests` | Workspace Root | All checks pass |
| **Frontend Linter** | `npm run lint` | `frontend/` | 0 errors, 0 warnings (`--max-warnings 0`) |
| **Frontend Build** | `npm run build` | `frontend/` | Vite build succeeds |
| **Git Push** | `git push origin main` | Workspace Root | Pushed via SSH (`git@github.com:...`) |

---

## 🔒 Configuration Notes

1. **Virtual Environment**: Python dependencies reside in `./.venv/`. Do not run system `pytest` (Python 3.14 missing packages).
2. **Git Authentication**: Remote URL is set to `git@github.com:404Avinash/SAMPATI_V2.git` using SSH keys.
3. **Agent Integration**: `AGENTS.md` and `.agents/skills/safe-push/SKILL.md` automatically instruct Antigravity agents on future requests.
