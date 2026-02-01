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

Alternative (from repo root):
```
export IVAULT_REPO_ROOT=/path/to/your/repo
PYTHONPATH=. uvicorn ivault_playground.app:app --reload
```

Then open:
- `http://127.0.0.1:8000/` (landing page)
- `http://127.0.0.1:8000/docs` (API docs)

Environment:
- `IVAULT_REPO_ROOT` (default: current working directory)
 - `IVAULT_PLAYGROUND_API_KEY` (optional; if set, require `x-ivault-api-key` header)

Notes:
- This minimal playground has no auth; put it behind your org auth if hosted.
- PR-only writes are not implemented yet (API is read-only + eval).
