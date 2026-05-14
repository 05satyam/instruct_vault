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

A ready-made plumbing benchmark suite lives in the `benchmarks/` folder. It
covers the five things infra teams typically ask about: render latency,
bundle load, validation throughput, bundle size, and resident memory.

```bash
# Standalone — no extra deps beyond what InstructVault already needs.
python benchmarks/run.py
python benchmarks/run.py --num-prompts 1000 --iters 10000 --json results.json

# Statistical (min/median/stddev/IQR) via pytest-benchmark.
pip install -e ".[benchmark]"
pytest benchmarks/test_perf.py --benchmark-only
```

The benchmarks are intentionally **not** part of the default `pytest` run, so
CI is unaffected.

### What the benchmarks do not claim

- They are **not** universal performance guarantees. Filesystem, CPU,
  container layout, and Python version all matter.
- They measure the **InstructVault path only** — no LLM call is involved.
  A typical LLM call is 100–1000× slower than rendering a prompt, so the
  goal here is just to show that the prompt-registry overhead is negligible.

If you want a meaningful number for your deployment, run the suite inside
your container image with your real prompt corpus size.
