# Stability Contract

This document explains which parts of InstructVault are intended to be stable for users adopting the project.

## Stable today
- Prompt spec `1.x`
- CLI command names: `init`, `validate`, `render`, `eval`, `diff`, `resolve`, `bundle`, `migrate`
- SDK entry point: `from instructvault import InstructVault`
- Bundle format version `1.0`
- JSON and JUnit report output shapes where already documented

## Compatibility expectations
- `1.x` prompt spec changes should be backward compatible with `1.0`.
- Breaking prompt spec changes require a major version bump.
- Existing CLI command names should not change without a deprecation path.
- Deprecated behavior should be called out in `CHANGELOG.md`.

## Less stable areas
- Playground package and UI details
- Example app structure
- Optional docs and cookbook patterns

## Upgrade guidance
- Read `CHANGELOG.md` before upgrading.
- Run `ivault validate prompts` and `ivault eval ...` in CI against the new version.
- Use `ivault migrate prompts` when spec migrations are introduced.
