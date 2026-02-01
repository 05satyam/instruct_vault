# ivault-playground (minimal)

This is an optional, minimal playground for teams that want a local or org-hosted UI.

Goals:
- browse prompts in a repo
- render with variables
- run evals
- PR-only writes (not implemented in this minimal version)

## Run locally
```
python -m venv .venv
source .venv/bin/activate
pip install -e .
export IVAULT_REPO_ROOT=/path/to/your/repo
PYTHONPATH=.. uvicorn ivault_playground.app:app --reload
```

Environment:
- `IVAULT_REPO_ROOT` (default: current working directory)
