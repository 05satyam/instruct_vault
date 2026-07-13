<div align="center">
  <img src="docs/assets/logo_light.svg" alt="InstructVault logo" width="500" />
</div>

# InstructVault (`ivault`) - Prompt changes deserve code review and CI.
[![PyPI version](https://img.shields.io/pypi/v/instructvault.svg)](https://pypi.org/project/instructvault/)
[![Python versions](https://img.shields.io/pypi/pyversions/instructvault.svg)](https://pypi.org/project/instructvault/)
[![CI](https://github.com/05satyam/instruct_vault/actions/workflows/ci.yml/badge.svg)](https://github.com/05satyam/instruct_vault/actions/workflows/ci.yml)
[![Release](https://github.com/05satyam/instruct_vault/actions/workflows/release.yml/badge.svg)](https://github.com/05satyam/instruct_vault/actions/workflows/release.yml)
[![Downloads](https://img.shields.io/pypi/dm/instructvault.svg)](https://pypi.org/project/instructvault/)
[![License](https://img.shields.io/pypi/l/instructvault.svg)](https://github.com/05satyam/instruct_vault/blob/main/LICENSE)
[![Types](https://img.shields.io/badge/types-py.typed-blue.svg)](https://peps.python.org/pep-0561/)



InstructVault is a Git-native quality gate for prompts. It catches prompt problems, runs deterministic tests, and versions releases through your
existing pull-request workflow—without requiring a hosted prompt platform.

**Version prompts in Git, test them in CI, load them locally at runtime.**

Prompts live as YAML/JSON files. Changes go through PRs and CI, releases are pinned by tag or SHA, and your app renders them from a local checkout or a bundle artifact — no hosted registry in the request path.

## Quickstart
```bash
pip install instructvault
ivault init                                              # scaffold prompts/, datasets/, CI workflow
ivault validate prompts                                  # check every prompt spec
ivault render prompts/hello_world.prompt.yml --vars '{"name":"Ava"}'
```

## A prompt looks like this
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
tests:                       # at least one test is required
  - name: includes_ticket
    vars: { ticket_text: "My order arrived damaged." }
    assert: { contains_all: ["Ticket:"] }
```

## Use it in your app
`render()` returns a list of `{role, content}` messages that also carries the spec's model config, so it drops straight into any client:

```python
from openai import OpenAI
from instructvault import InstructVault

client = OpenAI()
vault = InstructVault(repo_root=".")               # or bundle_path="out/ivault.bundle.json"

result = vault.render(
    "prompts/support_reply.prompt.yml",
    vars={"ticket_text": "My order is delayed", "customer_name": "Ava"},
    ref="prompts/v1.0.0",                          # pin to a tag/SHA (omit for working tree)
)

response = client.chat.completions.create(**result.to_openai())
```

`result` is a plain list, so `for m in result: m.content` still works. Adapters: `.to_openai()`, `.to_anthropic()`, `.to_litellm()`, `.to_dict()`.

## CLI
| Command | Purpose |
| --- | --- |
| `ivault init` | Scaffold `prompts/`, `datasets/`, and a CI workflow |
| `ivault validate <path>` | Validate prompt specs (add `--policy` for custom rules) |
| `ivault lint <path> --fail-under warning` | Quality gate: report prompt smells (secrets, missing docs), score, and gate CI |
| `ivault render <prompt> --vars '{...}'` | Render messages locally |
| `ivault eval <prompt> --report out/report.json --junit out/junit.xml` | Run tests/datasets, emit reports |
| `ivault diff <prompt> --ref1 <a> --ref2 <b>` | Diff a prompt across two refs |
| `ivault bundle --prompts prompts --out out/ivault.bundle.json --ref <tag>` | Build a deployable bundle |
| `ivault lock --prompts prompts --out ivault.lock.json` | Write a content-addressed lockfile |
| `ivault verify ivault.lock.json` | Fail if prompts drift from the lockfile |
| `ivault schema --out schemas/prompt.schema.json` | Emit the prompt JSON Schema |
| `ivault resolve <ref>` / `ivault migrate prompts` | Resolve a ref to a SHA / migrate specs |

By default `eval` asserts against the **rendered prompt** — fully deterministic, no network. Add `--provider openai` to instead call a model and assert on its **reply** (needs `OPENAI_API_KEY`), or `--provider ollama` to run against a local model (defaults to `http://127.0.0.1:11434`, override with `OLLAMA_HOST`). Network is strictly opt-in, so CI stays deterministic unless you ask for a provider.

## Where it fits
| Approach | Versioned in Git | CI-friendly | Local runtime | Hosted dependency |
| --- | --- | --- | --- | --- |
| Prompt strings in app code | Partial | Partial | Yes | No |
| Prompts in a database / admin UI | Usually not | Usually not | No | Usually yes |
| Hosted prompt registry/platform | Varies | Varies | Usually no | Yes |
| **InstructVault** | **Yes** | **Yes** | **Yes** | **No** |

```mermaid
flowchart LR
  A[Prompt files] --> B[PR review] --> C[CI validate + eval] --> D[Tag, SHA, or bundle] --> E[App runtime]
```

## Develop locally
```bash
git clone https://github.com/05satyam/instruct_vault.git
cd instruct_vault
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

## Docs & examples
- [`docs/dropin_guide.md`](docs/dropin_guide.md) — add InstructVault to an existing CI/CD repo
- [`docs/cookbooks.md`](docs/cookbooks.md) — OpenAI, LangChain, LlamaIndex, RAG, policies, bundles
- [`docs/lockfiles_and_judge.md`](docs/lockfiles_and_judge.md) — reproducible releases + LLM-as-judge evals
- [`docs/lint.md`](docs/lint.md) — the prompt quality gate (`ivault lint`) and rule catalog
- [`docs/spec.md`](docs/spec.md) — prompt spec and validation rules
- [`docs/ci.md`](docs/ci.md) · [`docs/governance.md`](docs/governance.md) · [`docs/stability.md`](docs/stability.md) · [`docs/roadmap.md`](docs/roadmap.md) · [`docs/performance.md`](docs/performance.md)
- Examples: [`examples/ivault_demo_template`](examples/ivault_demo_template/README.md), [`examples/llamaindex_demo`](examples/llamaindex_demo/README.md), [`examples/notebooks`](examples/notebooks), [`examples/policies`](examples/policies)

## License
Apache-2.0
