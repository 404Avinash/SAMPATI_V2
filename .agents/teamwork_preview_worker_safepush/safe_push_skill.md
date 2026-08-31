# Local Copy of safe-push skill

Source: /home/avi/Downloads/Sampati_v2/.agents/skills/safe-push/SKILL.md

```markdown
# Safe Push Skill for SAMPATI_V2

Use this skill whenever the user requests a commit or push operation.

## Quick Execution Steps

1. Run pre-commit pipeline validation:
   ```bash
   ./.venv/bin/pytest && ./.venv/bin/ruff check app tests && (cd frontend && npm run lint && npm run build)
   ```

2. If all pass cleanly:
   ```bash
   git add .
   git commit -m "<descriptive message>"
   git push origin main
   ```

## Key Configuration Locations
- Virtual Environment: `./.venv/`
- Pytest Suite: `tests/`
- Ruff Target: `app/` and `tests/`
- Frontend: `frontend/`
- Remote: `git@github.com:404Avinash/SAMPATI_V2.git`
```
