# InstructVault (ivault)
### Git-First Prompt Registry, CI Evals, Governance & Zero-Latency Runtime

---

## Project Vision

**InstructVault** exists to make prompts **first-class, governed, testable, versioned artifacts** — just like code — without adding runtime latency or forcing a proprietary platform.

Modern AI systems rely on prompts, yet prompts are often:
- edited informally
- deployed without review
- hard to version or roll back
- tightly coupled to vendors or frameworks
- unsafe to change at scale

InstructVault solves this by aligning prompts with the tools enterprises already trust:

> **Git for versioning**  
> **CI/CD for safety**  
> **PRs for governance**  
> **Local runtime for speed**  

---

## North Star

> **Prompts live in Git.  
> Prompt changes flow through CI/CD.  
> Prompt releases are immutable and reproducible.  
> Runtime stays fast, local, and framework-agnostic.**

If InstructVault ever violates this, it is a bug — not a feature.

---

## Core Design Principles (Non-Negotiable)

### 1. Git Is the Source of Truth
- Prompts are plain text files in Git
- Versions are git tags, SHAs, or branches
- No prompt database or server required

### 2. Zero Runtime Latency
- No network calls during inference
- No prompt fetch services
- Prompts are loaded from:
  - local repo checkout
  - build-time bundled artifacts
  - pinned git SHAs

CI can be heavy. Runtime must be light.

### 3. Framework & Vendor Agnostic
- Output format is standard `{ role, content }`
- Works with:
  - OpenAI / Anthropic SDKs
  - LangChain / LlamaIndex
  - Bedrock / Vertex / local models
- No hard dependency on any provider

### 4. CI/CD & Governance First
- Prompt changes must go through:
  - Pull Requests
  - reviews
  - automated checks
- No direct writes to production prompts
- UI tools (playground) **must** open PRs

### 5. Small Core, Extensible Edges
- Core package stays tiny and auditable
- Heavy integrations are optional plugins
- Playground is a separate package

---

## What InstructVault Provides

### 1. Core Package (`instructvault`)
Published on PyPI.

**Responsibilities**
- Prompt specification & validation
- Deterministic rendering
- Git ref loading (tag / SHA / branch)
- Deterministic evaluations
- CLI (`ivault`)
- Runtime SDK

**Explicit Non-Goals**
- No hosted service
- No database
- No forced LLM calls
- No cloud SDKs in core

---

## Prompt Specification

Prompts are stored as portable YAML files:

```yaml
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



## Design Goals

Human-readable

Diff-friendly

Deterministic

Compatible with GitHub Models .prompt.yml format (superset)

CLI (ivault)

The CLI is the primary interface.

## Required Commands

ivault init — scaffold prompts, datasets, CI

ivault validate — schema + static checks

ivault render — render prompt with variables

ivault eval — run deterministic tests

ivault diff — compare prompts across git refs

ivault resolve — resolve tag/branch to SHA

## CLI Rules

Deterministic behavior

CI-friendly exit codes

JSON and JUnit outputs

No side effects unless explicitly requested

## Runtime SDK

A minimal, predictable API:

```
from instructvault import InstructVault

vault = InstructVault(".")
messages = vault.render(
  "prompts/support_reply.prompt.yml",
  vars={"ticket_text": "Order delayed"},
  ref="prompts/v1.2.0"
)

```

### Runtime Guarantees

No network calls

No hidden caching

No global state

Safe to embed anywhere

## CI/CD Model (“PromptOps”)

### Prompt-Only Pipelines

CI should run only when prompt-related paths change:

```
prompts/**
datasets/**
.github/workflows/ivault.yml

```

This avoids slowing application pipelines.

### CI Stages (Baseline)

#### Stage 1: Validation

YAML schema validation

required variables

spec correctness

#### Stage 2: Deterministic Evals

inline prompt tests

dataset-driven tests (JSONL / CSV)

#### Stage 3: Reports

JSON (machine-readable)

JUnit XML (CI dashboards)

CI must fail clearly and early.


## Advanced CI (Optional, Pluggable)

Not part of core, but supported via extensions:

model endpoint execution

datasets from DB / S3 / APIs

guardrails (PII, policy rules)

LLM-as-judge (explicit opt-in)


## Governance Model
Git-Native Governance

InstructVault integrates with existing Git governance.

Recommended setup:

CODEOWNERS for prompts/**

branch protection rules

required CI checks

immutable prompt releases via tags


## Prompt Releases

Prompts should be released like software:

immutable tags (e.g. prompts/v1.3.0)

production loads only from tags or SHAs

rollbacks are trivial

## Auditability

Every prompt execution should be able to log:

prompt name

git SHA

dataset version

This enables reproducibility and compliance.


## Prompt Playground (Companion Package)
Why a Playground Exists

faster iteration

easier experimentation

accessibility for non-engineers

Why It Is Separate

keeps core auditable

avoids unnecessary dependencies

allows self-hosting


## Playground Rules

reads prompts from local repo

uses ivault internally

can:

edit prompts

render previews

run evals

compare git refs

must never push directly to main


## Governed Writes

If the playground writes to Git:

create branch

commit changes

open Pull Request

rely on CI + CODEOWNERS

No bypasses.


## Repository Layout (Recommended)

```
repo/
  prompts/
    *.prompt.yml
  datasets/
    *.jsonl
  src/               # application code
  .github/
    workflows/
      ivault.yml
    CODEOWNERS

```

### Enterprise Variant

prompts in a separate repo

pinned via submodule or build-time fetch

bundled into artifacts at build time

Both are supported.


## Quality Bar (“No Bugs” Philosophy)

Absolute rules:

full unit test coverage for core logic

CLI tested via Typer CliRunner

strict typing (mypy)

linting enforced

deterministic behavior

clear error messages

### We optimize for:

boring correctness

predictable upgrades

long-term maintainability


## Non-Goals (Explicit)

Not a hosted SaaS

Not a prompt marketplace

Not a tracing platform

Not a model management system

Not a replacement for LangChain or LlamaIndex

### InstructVault fits into existing stacks — it does not replace them.


## What Success Looks Like

InstructVault is successful if:

teams adopt it without friction

prompts are reviewed like code

CI catches prompt regressions

rollbacks are instant

runtime remains fast

no vendor lock-in is introduced

---

If Git already works in your org, InstructVault should feel obvious.
If it feels magical, something is wrong.

```

---

If you want next:
- a **CONTRIBUTING.md** (OSS standards, PR rules)
- a **v1.0 release checklist**
- a **Playground architecture doc**
- or a **Pitch README for GitHub landing page**

just tell me what’s next.

```