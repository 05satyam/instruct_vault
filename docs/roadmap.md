# Roadmap

This roadmap is intentionally narrow. InstructVault works best when the core stays small and predictable.

## Recently shipped (0.6.0)
- Content-addressed lockfiles (`ivault lock` / `ivault verify`) for reproducible, drift-checked releases.
- Thread-safe runtime spec caching in the SDK (immutable refs cached; worktree revalidated by mtime).
- Opt-in LLM-as-judge assertions (`assert.judge`) that stay skipped unless a judge provider is supplied.
- Published JSON Schema (`ivault schema`) for editor autocomplete.
- Reusable GitHub Action, pre-commit hook, cross-OS/Python CI matrix, and tag-triggered PyPI publishing.

## Prompt quality gate (in progress)
A deterministic, git-first analog to SonarQube for prompts, built as thin,
complete slices rather than a broad half-finished feature:
- `ivault lint` engine with a stable `Finding` contract, severity gating, and a
  Markdown scorecard for CI summaries. **Shipped** with rules `IV001` (secret in
  template) and `IV002` (missing description).
- Planned rules (tracked as issues): prompt-injection smell, PII in template,
  prompt-too-long / token budget, hardcoded-value-should-be-a-variable.
- Planned reporting: SARIF output for GitHub Code Scanning; a lint baseline so
  large repos can adopt incrementally ("fail only on new findings").
- Eval depth: regression baselines and cost/latency budgets.

## Near-term priorities
- Stronger end-to-end examples for common LLM stacks
- Better contributor onboarding and repo hygiene
- More CI templates and integration guides
- Clearer compatibility and migration documentation
- Broader test coverage for CLI and bundle workflows

## In scope
- Prompt spec evolution with backward compatibility
- Deterministic validation and eval improvements
- Better Git, CI, and release workflow support
- Lightweight SDK and bundle ergonomics
- Optional integrations that do not bloat the core runtime

## Explicitly out of scope for the core
- Hosted prompt registry or database
- Built-in model serving
- Required cloud dependencies
- Online prompt editing control plane
- Analytics, dashboards, or productized approval workflows

## How to evaluate new ideas
A proposed feature is a good fit when it strengthens one of these:
- Git as the source of truth
- Deterministic CI checks
- Reproducible prompt releases
- Fast local runtime

If it weakens those constraints, it likely belongs outside the core.
