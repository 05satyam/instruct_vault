# Cookbooks

## 1) Basic CI (GitHub Actions)
Run prompt checks only when prompt files change.

```
on:
  pull_request:
    paths:
      - "prompts/**"
      - "datasets/**"
  push:
    branches: [ main ]
    paths:
      - "prompts/**"
      - "datasets/**"
```

## 2) Release prompts with tags
```
git tag prompts/v1.2.0
git push origin prompts/v1.2.0
```

## 3) Bundle prompts at build time
```
ivault bundle --prompts prompts --out out/ivault.bundle.json --ref prompts/v1.2.0
```

## 4) Load bundle at runtime
```python
from instructvault import InstructVault

vault = InstructVault(bundle_path="out/ivault.bundle.json")
msgs = vault.render("prompts/support_reply.prompt.yml", vars={"ticket_text": "Order delayed"})
```

## 5) Prompt repo separated from app repo
- Store prompts in a separate repo
- Pin via submodule or build-time fetch
- Bundle during CI and ship artifact to the app

## 6) Agentic RAG integration
```python
from instructvault import InstructVault

vault = InstructVault(repo_root=".")
system = vault.render("prompts/rag_system.prompt.yml", vars={"domain":"support"})
```
Use `system` to seed your agent, then append tool outputs and retrieval results.

## 7) Tool-using agent prompt
Create `prompts/tool_agent.prompt.yml` with a system message that defines tools and constraints.
Render once per request and pass tool outputs back as additional messages.

## 8) Multi-tenant prompt versioning
- Use tags per tenant: `prompts/acme/v1.2.0`
- Load by ref at runtime: `ref="prompts/acme/v1.2.0"`

## 9) Simple RAG (non-agentic)
**Goal:** retrieve context and inject into a prompt.

Prompt:
```yaml
spec_version: "1.0"
name: rag_answer
variables:
  required: [question, context]
messages:
  - role: system
    content: "Answer using only the provided context. If missing, say you don't know."
  - role: user
    content: "Question: {{ question }}\n\nContext:\n{{ context }}"
```

Usage:
```python
from instructvault import InstructVault

vault = InstructVault(repo_root=".")
context = "\\n".join(retrieved_chunks)
msgs = vault.render("prompts/rag_answer.prompt.yml", vars={"question": q, "context": context})
```

## 10) Agentic RAG (with tool use)
**Goal:** allow the agent to call tools, then answer using retrieved evidence.

Prompt:
```yaml
spec_version: "1.0"
name: rag_agent
variables:
  required: [question]
messages:
  - role: system
    content: |
      You are a retrieval-augmented agent. Use tools when needed.
      Always cite evidence from tool results.
  - role: user
    content: "Question: {{ question }}"
```

Agent loop (sketch):
```python
from instructvault import InstructVault

vault = InstructVault(repo_root=".")
msgs = vault.render("prompts/rag_agent.prompt.yml", vars={"question": q})

# pass msgs to your agent runtime, execute tools, then append tool outputs
# and final answer to the message list.
```

## 11) Cloud dataset pre-step (S3)
**Goal:** keep core deterministic by downloading datasets before `ivault eval`.

CI step (AWS CLI):
```bash
aws s3 cp s3://your-bucket/datasets/support_cases.jsonl datasets/support_cases.jsonl
ivault eval prompts/support_reply.prompt.yml --dataset datasets/support_cases.jsonl --report out/report.json
```

GitHub Actions snippet:
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-region: us-east-1
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
- run: aws s3 cp s3://your-bucket/datasets/support_cases.jsonl datasets/support_cases.jsonl
- run: ivault eval prompts/support_reply.prompt.yml --dataset datasets/support_cases.jsonl --report out/report.json
```

Notes:
- The dataset is still local when `ivault` runs.
- Keep dataset files versioned or checksum-locked for reproducibility.
