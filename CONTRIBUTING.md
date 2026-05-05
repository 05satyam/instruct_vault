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

## Good first contributions
- Documentation improvements with runnable examples
- Additional framework integration examples
- Tests for uncovered CLI edge cases
- CI template improvements for other systems

Look for or create issues labeled `good first issue`, `docs`, `tests`, or `integration`.
