# Contributing

Thanks for contributing to InstructVault.

## Development setup
```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

## Pull requests
- Keep changes focused and small
- Add tests for new behavior
- Run `python -m pytest` locally
- Update docs if user-facing behavior changes
