# InstructVault (ivault) — Vision

## Purpose
InstructVault makes prompts **first‑class, governed, testable, versioned artifacts** — just like code — while keeping runtime **fast and local**.

## North Star
**Prompts live in Git.**  
**Prompt changes flow through CI/CD.**  
**Prompt releases are immutable and reproducible.**  
**Runtime stays fast, local, and framework‑agnostic.**

If InstructVault ever violates this, it is a bug — not a feature.

## Non‑Negotiables
1) **Git is the source of truth**  
   Prompts are files; versions are tags/SHAs/branches. No prompt database required.

2) **Zero runtime latency**  
   No network calls at inference time. Load from local repo or build‑time bundles.

3) **Framework & vendor agnostic**  
   Output is standard `{ role, content }` messages. Works with any LLM stack.

4) **Governance first**  
   Prompt changes go through PRs, reviews, and CI checks. No direct writes.

5) **Small core, extensible edges**  
   Core stays tiny and auditable. Heavy integrations are optional and separate.

## What the Core Provides
- Prompt spec + validation
- Deterministic rendering
- Git ref loading
- Deterministic evals (inline + dataset)
- CLI (`ivault`) and runtime SDK

## What the Core Explicitly Does Not Provide
- Hosted services or databases
- Forced LLM calls
- Cloud SDK dependencies in core

## Prompt Spec (YAML/JSON)
```yaml
spec_version: "1.0"
name: support_reply
variables:
  required: [ticket_text]
messages:
  - role: system
    content: "You are a support engineer."
  - role: user
    content: "Ticket: {{ ticket_text }}"
tests:
  - name: must_include_ticket
    vars: { ticket_text: "Order damaged" }
    assert: { contains_any: ["Ticket:"] }
```

## CLI Contract
`init`, `validate`, `render`, `eval`, `diff`, `resolve`, `bundle`  
Deterministic behavior, CI‑friendly exit codes, JSON/JUnit outputs where applicable.

## CI/CD Model (PromptOps)
- Run checks only when prompt paths change  
- Stages: **validate → eval → report**  
- Fail fast and clearly

## Governance Model
Use existing Git governance: CODEOWNERS, branch protection, required CI checks.

## Success Criteria
- Teams adopt without friction
- Prompt changes are reviewed like code
- CI catches regressions
- Rollbacks are instant
- Runtime stays fast and local
