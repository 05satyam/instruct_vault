# Spec Contract

## Versioning
- `spec_version` is required for prompts.
- Current stable series: **1.x**
- Minor versions (1.1, 1.2, …) must remain backward compatible with 1.0.
- Breaking changes require a major version (2.0).

## Deprecation
- Deprecated fields must continue to parse for at least one minor release.
- Deprecations are documented in `CHANGELOG.md`.

## Migration
Use:
```
ivault migrate prompts
```
This checks for missing `spec_version` and reports any files that need updates.
Use `--apply` to write `spec_version: 1.0` into YAML prompts.

## Data Model (1.0)
Required:
- `spec_version`
- `name`
- `messages`
- `tests` (at least one inline test)

Optional:
- `description`
- `modelParameters` (alias: `model_defaults`)
- `variables`

## Tests
Each test must include at least one assertion:
- `contains_any`
- `contains_all`
- `not_contains`
 - `matches` (regex)
 - `not_matches` (regex)
 - `json_schema` (JSON Schema validation)
