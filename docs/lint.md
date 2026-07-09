# Prompt lint (`ivault lint`)

`ivault lint` is a deterministic **quality gate** for prompts — think of it as a
linter/SonarQube for your prompt specs. Where `ivault validate` enforces hard
schema correctness, `lint` reports *quality smells*: things worth flagging that
are not necessarily fatal. It runs fully offline (no model calls), so it is safe
in default CI.

## Usage

```bash
# Human-readable report
ivault lint prompts

# Machine-readable, for tooling
ivault lint prompts --format json

# Markdown scorecard (great for a GitHub Actions job summary)
ivault lint prompts --format md >> "$GITHUB_STEP_SUMMARY"

# Fail CI if any finding is at/above a severity
ivault lint prompts --fail-under warning
```

By default `lint` never fails the build; it only reports. Pass `--fail-under`
(`error`, `warning`, or `info`) to turn it into a gate.

## GitHub Actions scorecard

The composite Action ships with a `lint` input (default `true`) that
automatically appends the Markdown scorecard to the job summary — no extra
workflow YAML needed:

```yaml
- uses: 05satyam/instruct_vault@v1
  with:
    prompts: my-prompts
    lint: true                    # default; produces the scorecard
    fail-under: warning           # optional; fail CI at warning or above
```

The scorecard appears in the **Job Summary** section of the checks tab as an
"InstructVault Prompt Lint" block. Because `$GITHUB_STEP_SUMMARY` works on
private repos, this is the simplest path to a prompt-quality dashboard for any
repo using the Action.

When `fail-under` is set and the threshold is exceeded, the step fails and the
overall check is marked red. Unset, lint is purely advisory and won't fail.

## Severities

| Severity | Meaning |
| --- | --- |
| `error` | Should almost always be fixed (e.g. a leaked secret). |
| `warning` | A smell worth addressing; not fatal. |
| `info` | Advisory. |

## Finding shape (`--format json`)

The JSON output is a stable contract:

```json
{
  "ok": true,
  "counts": {"info": 0, "warning": 1, "error": 0},
  "findings": [
    {
      "rule_id": "IV002",
      "severity": "warning",
      "message": "Prompt has no description; ...",
      "prompt_path": "prompts/greeter.prompt.yml",
      "location": null,
      "help_url": "https://github.com/05satyam/instruct_vault/blob/main/docs/lint.md#iv002"
    }
  ]
}
```

## Rule catalog

### IV000
A prompt file could not be parsed at all. Emitted as an `error` so a malformed
spec never silently passes the gate.

### IV001
**Hardcoded secret in template** (`error`). A secret-looking token (API key,
private key block, etc.) was found in the prompt text committed to git. Move it
to a runtime variable or secret store. This complements the render-time secret
scan, which inspects *values* rather than the template source.

### IV002
**Missing description** (`warning`). The prompt has no `description`. Add one so
reviewers and downstream consumers understand its purpose and ownership.

## Adding a rule

Rules live in `src/instructvault/lint.py`. Subclass `Rule`, set `id`,
`severity`, and `summary`, implement `check(spec, path) -> list[Finding]` (use
`self.finding(...)`), and register the instance in `_RULES`. Add tests and a
catalog entry here. Because the `Finding` contract is stable, each new rule is an
isolated, low-risk change — a good contribution.
