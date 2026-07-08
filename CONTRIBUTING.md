# Contributing

Thanks for contributing to InstructVault.

## Development setup

Create a fresh virtual environment (do **not** reuse a stale one — if activation
fails with a "no such file" error, delete `.venv/` and recreate it):

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Run the full local check the same way CI does:

```bash
ruff check src tests                     # lint
mypy src/instructvault                   # types (strict)
python -m pytest --cov=instructvault --cov-fail-under=80   # tests + coverage floor
```

`ruff` and `mypy` are pinned to exact versions in `[project.optional-dependencies].dev`
so local results match CI exactly.

## Pull requests
- Keep changes focused and small.
- Add tests for new behavior; keep coverage at or above the CI floor.
- Run `ruff`, `mypy`, and `pytest` locally before pushing.
- Update docs if user-facing behavior changes.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for messages
  (`feat:`, `fix:`, `docs:`, `chore:` …) — releases and the changelog are derived
  from them.
- If you change the prompt spec, regenerate the schema: `ivault schema --out schemas/prompt.schema.json`.

## How to add a model provider

Providers are small, self-contained callables — a good first PR. A provider takes
rendered messages plus model params and returns the model's reply text:

1. Add a function in `src/instructvault/providers.py` with the signature
   `Callable[[List[Dict[str, str]], Dict[str, object]], str]`. Import any heavy
   SDK **lazily inside the function** so the core stays dependency-free.
2. Register it in the `_PROVIDERS` dict.
3. Add a test using the deterministic `mock` provider pattern (no network).

The same provider abstraction powers both `--provider` (output evals) and
`--judge-provider` (LLM-as-judge), so one addition covers both.

## Good first contributions
- Documentation improvements with runnable examples
- Additional framework integration examples
- New model providers / adapters
- Tests for uncovered CLI edge cases
- CI template improvements for other systems

Look for or create issues labeled `good first issue`, `docs`, `tests`, or `integration`.
