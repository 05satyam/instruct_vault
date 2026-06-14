# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- `InstructVault.render()` now returns a `RenderResult` with provider adapters (`to_openai`, `to_anthropic`, `to_litellm`, `to_dict`) and the spec's model metadata. It still subclasses `list`, so existing message-iteration code is unchanged.
- `RenderResult` is exported from the top-level package.
- Opt-in output evals: `ivault eval --provider <name>` runs prompts through a model and asserts on the reply. Off by default to keep CI deterministic.

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
