# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
No unreleased changes.

## [0.6.0] - 2026-07-08
### Added
- **Lockfiles** for reproducible deployments: `ivault lock` writes a deterministic, content-addressed `ivault.lock.json`, and `ivault verify` fails on drift. Hashing is over the parsed spec, so YAML/JSON format and CRLF/LF line endings never cause false drift.
- **Runtime spec cache** in `InstructVault`: thread-safe, immutable refs cached for the process lifetime, worktree reads revalidated by mtime. Opt out with `cache=False` or reset with `clear_cache()`.
- **LLM-as-judge assertions** (`assert.judge` with `rubric`/`threshold`): opt-in and skipped (never failed) unless `--judge-provider` is set, so default CI stays deterministic.
- **`ivault schema`** emits a JSON Schema (committed at `schemas/prompt.schema.json`) for editor autocomplete and inline validation.
- **Ecosystem**: reusable composite GitHub Action (`action.yml`), a pre-commit hook (`.pre-commit-hooks.yaml`), a cross-OS/Python CI matrix, and Conventional-Commit semantic-release.
- `ivault validate` now accepts multiple paths (enables the pre-commit hook).

### Fixed
- `allow_no_tests` was silently ignored (bad Pydantic context read), which broke `bundle` and SDK runtime loads for test-less prompts.
- Secret scanner regex `\s` was escaped incorrectly and never matched whitespace-separated tokens; expanded coverage (Anthropic, GitHub, Google, Slack, PEM private keys).

### Security
- Path-traversal guard in `PromptStore` (prompt paths can no longer escape the repo root).
- Git subprocess calls now have timeouts and clearer errors so a wedged git cannot hang a runtime request.
- Package now ships a `py.typed` marker so downstream users get type information.

## [0.5.0] - 2026-06-13
### Added
- `InstructVault.render()` now returns a `RenderResult` with provider adapters (`to_openai`, `to_anthropic`, `to_litellm`, `to_dict`) and the spec's model metadata. It still subclasses `list`, so existing message-iteration code is unchanged.
- `RenderResult` is exported from the top-level package.
- Opt-in output evals: `ivault eval --provider <name>` runs prompts through a model and asserts on the reply. Off by default to keep CI deterministic.
- First-class `provider` field in `modelParameters` (enables `RenderResult.to_litellm()` provider/model routing).

### Changed
- Tightened README into a precise, linear quickstart → prompt → app → CLI flow.

## [0.3.1] - 2026-05-05
### Added
- Public roadmap and stability docs
- Comparison and performance guidance docs
- Integration request issue template

### Changed
- Sharper README positioning and framework integration examples
- Contributor and PR testing guidance now uses `python -m pytest`

## [0.2.2] - 2026-02-01
### Added
- Spec versioning (`spec_version`)
- JSON prompt support
- Build-time bundling (`ivault bundle`)
- JSON outputs for CLI commands
- Cookbooks, drop-in guide, and CI templates
- Minimal playground scaffold
