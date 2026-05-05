# Performance Notes

InstructVault is designed to keep the runtime path simple:
- load prompt text from the local repo or bundle
- parse the prompt spec
- render deterministic message output

There are no network calls in the core runtime path unless your application adds them.

## What "lightweight" means here
- No hosted control plane is required to fetch prompts at inference time
- Core dependencies stay focused on CLI, parsing, validation, and templating
- Runtime reads from local disk or a build artifact

## What this document does not claim
This repo does not publish universal latency numbers because performance depends on:
- filesystem and container environment
- prompt size
- bundle size
- application startup model

## How to benchmark locally
Measure the path that matters in your deployment:

1. Render from the worktree
```bash
python3 - <<'PY'
from instructvault import InstructVault

vault = InstructVault(repo_root=".")
for _ in range(1000):
    vault.render("prompts/hello_world.prompt.yml", vars={"name": "Ava"})
PY
```

2. Render from a bundle
```bash
ivault bundle --prompts prompts --out out/ivault.bundle.json
python3 - <<'PY'
from instructvault import InstructVault

vault = InstructVault(bundle_path="out/ivault.bundle.json")
for _ in range(1000):
    vault.render("prompts/hello_world.prompt.yml", vars={"name": "Ava"})
PY
```

3. Compare with your application baseline
- same container image
- same filesystem layout
- same prompt corpus size

That will give you a meaningful local number instead of a synthetic repo claim.
