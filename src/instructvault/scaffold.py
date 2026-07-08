from __future__ import annotations

from pathlib import Path

DEFAULT_PROMPT = '''spec_version: "1.0"
name: hello_world
description: Minimal example prompt.
variables:
  required: [name]
messages:
  - role: system
    content: "You are a helpful assistant."
  - role: user
    content: "Say hello to {{ name }}."
tests:
  - name: includes_name
    vars: { name: "Ava" }
    assert: { contains_any: ["Ava"] }
'''

DEFAULT_WORKFLOW = '''name: ivault (prompts)
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

jobs:
  prompts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install instructvault
      - run: ivault validate prompts
      # Fails if a prompt changed without running `ivault lock` to update the lockfile.
      - run: ivault verify ivault.lock.json --prompts prompts
      - run: ivault eval prompts/hello_world.prompt.yml --report out/report.json --junit out/junit.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: ivault-reports
          path: out/
'''

def init_repo(repo_root: Path) -> None:
    prompts = repo_root / "prompts"
    datasets = repo_root / "datasets"
    workflow = repo_root / ".github" / "workflows" / "ivault.yml"
    prompts.mkdir(parents=True, exist_ok=True)
    datasets.mkdir(parents=True, exist_ok=True)
    workflow.parent.mkdir(parents=True, exist_ok=True)

    sample_prompt = prompts / "hello_world.prompt.yml"
    if not sample_prompt.exists():
        sample_prompt.write_text(DEFAULT_PROMPT, encoding="utf-8")
    if not workflow.exists():
        workflow.write_text(DEFAULT_WORKFLOW, encoding="utf-8")

    # Generate an initial lockfile so `ivault verify` works out of the box.
    from .lock import write_lock

    lockfile = repo_root / "ivault.lock.json"
    if not lockfile.exists():
        write_lock(lockfile, repo_root=repo_root, prompts_dir=prompts, ref=None)
