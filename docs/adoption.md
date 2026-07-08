# Adoption playbook

A checklist for driving adoption once the codebase is trustworthy and instantly
runnable. Items marked **(maintainer)** require a human with repo/account access;
the rest are already in the codebase.

## Instantly runnable (step 6)
- [x] `ivault init` scaffolds prompts, datasets, a workflow, and a lockfile.
- [x] Runnable examples in [`examples/`](../examples).
- [ ] **(maintainer)** Publish a standalone `instruct-vault-starter` template repo
      (GitHub → "Use this template") that is green on first CI run.
- [ ] **(maintainer)** Record a ~60s terminal GIF of `init → validate → eval → render`
      and embed it near the top of the README.

## Distribution (step 7)
- [x] Composite GitHub Action ([`action.yml`](../action.yml)).
- [x] pre-commit hook ([`.pre-commit-hooks.yaml`](../.pre-commit-hooks.yaml)).
- [x] Editor autocomplete via committed JSON Schema (see `editor_setup.md`).
- [ ] **(maintainer)** Publish the Action to the GitHub Marketplace (create a
      release, tick "Publish this Action to the Marketplace").
- [ ] **(maintainer)** Add the repo to the [pre-commit hooks index](https://pre-commit.com/hooks.html).

## Trust signals (step 8)
- [x] Cross-OS/Python CI matrix, lint + mypy gate, coverage floor, schema-in-sync gate.
- [x] README badges; `docs/stability.md` versioning/compat policy; `py.typed`.
- [ ] **(maintainer)** Optional: wire Codecov for a live coverage badge.

## De-risk the bus factor (step 9)
- [x] "How to add a provider" guide in `CONTRIBUTING.md`.
- [ ] **(maintainer)** Create 5–10 `good first issue` issues (docs, providers, tests).
- [ ] **(maintainer)** Recruit 1–2 co-maintainers; document release access.

## Launch (step 10 — do last)
- [ ] **(maintainer)** Ensure steps 6–9 are done and the starter repo + GIF exist.
- [ ] **(maintainer)** Post to Show HN / r/MachineLearning / dev.to using the draft below.

### Launch post draft

> **Show HN: InstructVault — PromptOps in git, no prompt-registry SaaS**
>
> I kept seeing teams either hardcode prompts in app code (every change = a deploy)
> or pay for a hosted prompt platform (vendor lock-in + a network hop at inference).
>
> InstructVault treats prompts as code: YAML/JSON specs versioned in git, validated
> and evaluated in CI, pinned by tag/SHA/lockfile, and rendered locally at runtime —
> no hosted registry in the request path. It's a small, typed core with a CLI and SDK.
>
> New in this release: content-addressed lockfiles for reproducible releases, a
> runtime cache, opt-in LLM-as-judge evals (deterministic by default), a JSON Schema
> for editor autocomplete, a GitHub Action, and a pre-commit hook.
>
> Quickstart, docs, and a starter template: <link>
>
> Feedback welcome — especially on the prompt spec and the eval model.
