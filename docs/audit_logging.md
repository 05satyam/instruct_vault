# Audit Logging (recommended)

Log these fields for every render/eval execution:
- prompt path
- git ref or SHA
- spec_version
- dataset path (if any)
- policy module (if any)
- safe / strict-vars / redact flags
- timestamp

Example payload:
```
{
  "prompt": "prompts/support_reply.prompt.yml",
  "ref": "prompts/v1.2.0",
  "spec_version": "1.0",
  "dataset": "datasets/support_cases.jsonl",
  "policy": "docs/policy_pack.py",
  "safe": true,
  "strict_vars": true,
  "redact": true,
  "timestamp": "2026-02-02T12:00:00Z"
}
```
