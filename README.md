<div align="center">
  <img src="docs/assets/logo_light.svg" alt="InstructVault logo" width="500" />
</div>

# InstructVault (`ivault`)
[![PyPI version](https://img.shields.io/pypi/v/instructvault.svg)](https://pypi.org/project/instructvault/)
[![Python versions](https://img.shields.io/pypi/pyversions/instructvault.svg)](https://pypi.org/project/instructvault/)
[![CI](https://github.com/05satyam/instruct_vault/actions/workflows/ci.yml/badge.svg)](https://github.com/05satyam/instruct_vault/actions/workflows/ci.yml)
[![Release](https://github.com/05satyam/instruct_vault/actions/workflows/release.yml/badge.svg)](https://github.com/05satyam/instruct_vault/actions/workflows/release.yml)

**Version prompts in Git, test them in CI, load them locally at runtime.**

InstructVault is a Git-first prompt-as-code toolkit for engineering teams. Prompts live as YAML/JSON files, prompt changes go through PRs and CI, releases are pinned by tag or SHA, and apps render prompts from a local repo checkout or bundle artifact.

## 30-second try
```bash
pip install instructvault
ivault init
ivault validate prompts
ivault render prompts/hello_world.prompt.yml --vars '{"name":"Ava"}'
```

PyPI: https://pypi.org/project/instructvault/  
GitHub: https://github.com/05satyam/instruct_vault

## Why Teams Use It
- **Git-native governance**: review prompt changes with the same PR, CODEOWNERS, and branch protection flow as code.
- **CI checks for prompts**: validate specs, run deterministic evals, and emit JSON or JUnit reports.
- **Reproducible releases**: deploy prompt versions by tag, SHA, or build-time bundle.
- **Local runtime**: no hosted registry call is required to fetch prompts at inference time.
- **Framework agnostic**: output is plain `{role, content}` messages for any LLM stack.

## Tiny Example
Create a prompt:

```yaml
# prompts/support_reply.prompt.yml
spec_version: "1.0"
name: support_reply
modelParameters:
  model: gpt-4o
  temperature: 0.3
variables:
  required: [ticket_text]
  optional: [customer_name]
messages:
  - role: system
    content: "You are a concise, empathetic support engineer."
  - role: user
    content: |
      Customer: {{ customer_name | default("there") }}
      Ticket: {{ ticket_text }}
tests:
  - name: includes_ticket
    vars:
      ticket_text: "My order arrived damaged."
    assert:
      contains_all: ["Ticket:"]
```

Render it in your app:

```python
from instructvault import InstructVault

vault = InstructVault(repo_root=".")
messages = vault.render(
    "prompts/support_reply.prompt.yml",
    vars={"ticket_text": "My order is delayed", "customer_name": "Ava"},
    ref="prompts/v1.0.0",
)
```

## CLI
```bash
ivault init
ivault validate prompts
ivault render prompts/support_reply.prompt.yml --vars '{"ticket_text":"Need refund"}'
ivault eval prompts/support_reply.prompt.yml --report out/report.json --junit out/junit.xml
ivault diff prompts/support_reply.prompt.yml --ref1 prompts/v1.0.0 --ref2 HEAD
ivault bundle --prompts prompts --out out/ivault.bundle.json --ref prompts/v1.0.0
```

## Where It Fits
| Approach | Versioned in Git | CI-friendly | Local runtime | Hosted dependency |
| --- | --- | --- | --- | --- |
| Prompt strings inside app code | Partial | Partial | Yes | No |
| Prompts in a database or admin UI | Usually not | Usually not | No | Usually yes |
| Hosted prompt registry/platform | Varies | Varies | Usually no | Yes |
| **InstructVault** | **Yes** | **Yes** | **Yes** | **No** |

## System Flow
```mermaid
flowchart LR
  A[Prompt files] --> B[PR review]
  B --> C[CI validate + eval]
  C --> D[Tag, SHA, or bundle]
  D --> E[App runtime]
  E --> F[Rendered messages]
```

## Install For Development
```bash
git clone https://github.com/05satyam/instruct_vault.git
cd instruct_vault
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

## Docs
- `docs/dropin_guide.md` - add InstructVault to an existing repo
- `docs/cookbooks.md` - OpenAI, LangChain, LlamaIndex, RAG, policies, bundles
- `docs/why_instructvault.md` - when to use InstructVault vs other approaches
- `docs/spec.md` - prompt spec and validation rules
- `docs/stability.md` - stable surfaces and compatibility expectations
- `docs/ci.md` - CI setup and reports
- `docs/governance.md` - CODEOWNERS and release guardrails
- `docs/roadmap.md` - roadmap, in-scope, and out-of-scope work
- `docs/performance.md` - performance principles, benchmarks (`benchmarks/`) and how to run them
- `docs/playground.md` - optional local/hosted playground

## Examples
- `examples/ivault_demo_template/README.md`
- `examples/llamaindex_demo/README.md`
- `examples/notebooks/instructvault_colab.ipynb`
- `examples/notebooks/instructvault_rag_colab.ipynb`
- `examples/notebooks/instructvault_openai_colab.ipynb`
- `examples/policies/policy_example.py`
- `examples/policies/policy_pack.py`

## License
Apache-2.0
