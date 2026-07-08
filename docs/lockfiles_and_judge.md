# Lockfiles and judge assertions

Two features that make InstructVault safer to adopt at scale: **content-addressed
lockfiles** for reproducible releases, and **opt-in LLM-as-judge assertions** for
semantic quality checks that never compromise deterministic CI.

## Lockfiles: pin exactly what ships

A lockfile records a canonical `sha256` of every prompt's *parsed* spec. Because
the hash is over the parsed content (not the raw bytes), it is independent of
file format (YAML vs JSON) and line endings (CRLF vs LF) — so the same prompts
produce the same lockfile on every machine, OS, and CI runner.

```bash
# Write (or refresh) the lockfile from the working tree
ivault lock --prompts prompts --out ivault.lock.json

# Fail if the current prompts no longer match the lockfile
ivault verify ivault.lock.json --prompts prompts
```

`ivault init` generates an initial `ivault.lock.json` and wires `ivault verify`
into the scaffolded workflow. From then on, any prompt change that isn't
accompanied by a fresh `ivault lock` fails CI with an explicit drift report:

```
Lockfile drift detected:
  changed: prompts/support_reply.prompt.yml
```

This turns "did a prompt change?" into a reviewable, enforced signal — the same
guarantee `package-lock.json` or `poetry.lock` give for dependencies.

You can also lock a specific git ref for release pipelines:

```bash
ivault lock --prompts prompts --ref prompts/v1.2.0 --out ivault.lock.json
```

## Judge assertions: semantic checks, deterministic by default

Deterministic assertions (`contains_any`, `matches`, `json_schema`, …) are fast,
free, and network-free — they are the default and always run. But some qualities
("is this summary accurate and concise?") are hard to express as string matches.

A `judge` assertion describes the quality in a rubric and delegates scoring to a
model. Crucially, it is **opt-in**: it only runs when you pass a judge provider,
and is otherwise **skipped (not failed)**, so `ivault eval` stays deterministic
in normal CI.

```yaml
tests:
  - name: mentions_topic
    vars: { article: "The city council approved a transit budget." }
    assert:
      contains_any: ["transit", "budget", "council"]   # always runs
      judge:
        rubric: "The summary is a single, accurate sentence capturing the main point."
        threshold: 0.7                                  # runs only with --judge-provider
```

```bash
# Deterministic only — judge is reported as SKIP:
ivault eval prompts/judged_summary.prompt.yml

# With a judge model (needs OPENAI_API_KEY):
ivault eval prompts/judged_summary.prompt.yml --judge-provider openai
```

See [`examples/prompts/judged_summary.prompt.yml`](../examples/prompts/judged_summary.prompt.yml)
for a complete, runnable example.

### Recommended pattern
- Keep deterministic assertions as your **required** gate (they never flake).
- Run judge assertions in a **separate, non-blocking** job (or on a schedule),
  since they cost tokens and are inherently non-deterministic.
