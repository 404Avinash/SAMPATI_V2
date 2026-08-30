# SAMPATI_V2 Repository Guidelines & Automated Safe-Push Protocol

## Fast Safe-Push & Commit Protocol

When the user asks to **"push code"**, **"commit and push"**, or **"commit changes safely"**, follow this automated validation protocol **without re-scanning the entire codebase**:

### 1. Environment & Tools
- **Python Virtualenv**: `./.venv/bin/python` / `./.venv/bin/pytest` / `./.venv/bin/ruff`
- **Frontend Directory**: `frontend/` (Node.js / Vite)
- **Git Remote SSH**: `origin` is set to `git@github.com:404Avinash/SAMPATI_V2.git`

### 2. Standard Safe-Push Command Sequence
Execute the fast validation sequence in terminal:

```bash
# Step 1: Run Pytest + Ruff + Frontend Lint + Frontend Build
./.venv/bin/pytest && ./.venv/bin/ruff check app tests && cd frontend && npm run lint && npm run build && cd ..

# Step 2: Stage, Commit, and Push via SSH
git add .
git commit -m "<type>(<scope>): <concise message>"
git push origin main
```

### 3. Pipeline Checks Reference
- **Pytest**: `./.venv/bin/pytest` (559+ tests)
- **E2E Suite**: `./.venv/bin/python tests/test_e2e_suite.py --verbose`
- **Ruff Check**: `./.venv/bin/ruff check app tests`
- **Frontend ESLint**: `cd frontend && npm run lint` (`--max-warnings 0` rule enforced)
- **Frontend Build**: `cd frontend && npm run build`

### 4. Special Gotchas & Fixes
- **ESLint in React Hooks**: In React cleanup functions (e.g. `useEffect`), do not directly access mutable refs like `stateRef.current` without `// eslint-disable-next-line react-hooks/exhaustive-deps` or storing in a local variable outside return.
- **Git Authentication**: Always push via SSH (`git@github.com:404Avinash/SAMPATI_V2.git`) to avoid non-interactive HTTPS credentials prompts.
