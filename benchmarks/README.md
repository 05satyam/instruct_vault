# InstructVault Benchmarks

Plumbing benchmarks for the InstructVault runtime — render latency, bundle load
time, validation throughput, bundle size, and memory footprint.

These benchmarks measure **the library itself**, not LLM quality. They answer
the kind of question infra teams ask before adopting a new dependency:

> Is the prompt-loading and rendering cost negligible compared to the LLM call
> it precedes?

## What gets measured

| Metric | Question it answers |
| --- | --- |
| Render latency | Is rendering effectively free vs. an LLM call (≈ hundreds of ms)? |
| Bundle load time | Does it scale to a fleet of hundreds of prompts? |
| Validation throughput | Does `ivault validate` slow down CI for big repos? |
| Bundle size | How fat is the artifact you deploy with your app? |
| Memory footprint | OK for serverless / edge runtimes? |

## How to run

The standalone script needs **only the runtime dependencies** that
InstructVault already requires — no extra installs.

```bash
# Default: 100 prompts, 5000 render iterations
python benchmarks/run.py

# Try a bigger fleet
python benchmarks/run.py --num-prompts 1000 --iters 10000

# Emit JSON for downstream charts/CI
python benchmarks/run.py --json results.json
```

A statistical version using `pytest-benchmark` is also available
(`pip install pytest-benchmark` and run `pytest benchmarks/test_perf.py
--benchmark-only`). It reports min / mean / median / stddev across runs.

## What the numbers do *not* claim

- They are **not** universal performance guarantees. Filesystem, CPU, Python
  version, and container layout all matter.
- They are **not** a measurement of LLM quality.
- Render latency is for InstructVault's render path *only* — it does not
  include any LLM call.

The point is to show:
1. The order of magnitude (microseconds, not milliseconds) so adopters know
   the runtime cost is dominated by the LLM, not the prompt registry.
2. That bundle and validate costs scale linearly and predictably.

## Reproducing in CI

The benchmarks are intentionally **not** part of the default `pytest` test
suite, so they don't slow down CI. If you want to track perf over time, run
the script in a separate CI job and store the JSON output as an artifact.
