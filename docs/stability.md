# Stability Contract

This document explains which parts of InstructVault are intended to be stable for users adopting the project.

## Stable today
- Prompt spec `1.x`
- CLI command names: `init`, `validate`, `render`, `eval`, `diff`, `resolve`, `bundle`, `migrate`, `lock`, `verify`, `schema`
- SDK entry point: `from instructvault import InstructVault`
- Bundle format version `1.0`
- Lockfile format version `1.0` (`lock_version`)
- JSON and JUnit report output shapes where already documented

## Versioning and releases
- The project follows [Semantic Versioning](https://semver.org/).
- [Conventional Commits](https://www.conventionalcommits.org/) guide the version
  bump: `fix:` → patch, `feat:` → minor, `feat!:`/`BREAKING CHANGE:` → major.
- Releases are cut manually by a maintainer (see `CONTRIBUTING.md` → "Cutting a
  release"). Pushing a `v*` tag triggers the `release` workflow, which builds and
  publishes to PyPI.
- The published package ships a `py.typed` marker; type hints are part of the API.

## Compatibility expectations
- `1.x` prompt spec changes should be backward compatible with `1.0`.
- Breaking prompt spec changes require a major version bump.
- Existing CLI command names should not change without a deprecation path.
- Lockfile and bundle format bumps are additive within a major version.
- Deprecated behavior should be called out in `CHANGELOG.md`.

## Less stable areas
- Playground package and UI details
- Example app structure
- Optional docs and cookbook patterns

## Upgrade guidance
- Read `CHANGELOG.md` before upgrading.
- Run `ivault validate prompts` and `ivault eval ...` in CI against the new version.
- Use `ivault migrate prompts` when spec migrations are introduced.
