# Roadmap

This roadmap is intentionally narrow. InstructVault works best when the core stays small and predictable.

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
