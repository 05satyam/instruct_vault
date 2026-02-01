# Release checklist

## Core readiness
- Spec is stable and versioned (`spec_version`)
- CLI flags and outputs are documented
- JSON outputs are stable for CI usage
- Bundle format is versioned

## Quality
- All tests pass (`pytest`)
- No new lint errors (`ruff`, `mypy` if used)
- Backward compatibility noted in changelog

## Docs
- README updated for new features
- Cookbooks cover common enterprise flows
- CI templates are included for common systems

## Release steps
- Bump version in `pyproject.toml`
- Tag release: `git tag vX.Y.Z`
- Push tag and publish to PyPI
