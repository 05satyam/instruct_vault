"""Plumbing benchmarks for InstructVault.

Measures: render latency, bundle load time, validation throughput, bundle
size, and (best-effort) memory footprint. Uses only InstructVault's runtime
dependencies — no extra installs required.

Usage:
    python benchmarks/run.py
    python benchmarks/run.py --num-prompts 1000 --iters 10000
    python benchmarks/run.py --json results.json
"""
from __future__ import annotations
import argparse
import gc
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ``resource`` is Unix-only — on Windows we just report memory as unavailable
try:
    import resource  # type: ignore[import-not-found]
    _RESOURCE_AVAILABLE = True
except ImportError:
    _RESOURCE_AVAILABLE = False

# Prefer the in-repo source if running from a checked-out clone, but fall back
# silently to whatever ``instructvault`` is installed in the environment.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from instructvault import InstructVault  # noqa: E402
from instructvault.bundle import write_bundle  # noqa: E402
from instructvault.io import load_prompt_spec  # noqa: E402


PROMPT_TEMPLATE = """\
spec_version: "1.0"
name: prompt_{i}
description: Benchmark prompt #{i}
modelParameters:
  model: gpt-4o
  temperature: 0.3
variables:
  required: [ticket_text]
  optional: [customer_name]
messages:
  - role: system
    content: |
      You are a concise, empathetic support engineer for prompt {i}.
  - role: user
    content: |
      Customer: {{{{ customer_name | default("there") }}}}
      Ticket: {{{{ ticket_text }}}}
tests:
  - name: includes_ticket
    vars:
      ticket_text: "My order arrived damaged."
    assert:
      contains_all: ["Ticket:"]
"""


def _setup_repo(tmp: Path, num_prompts: int) -> Path:
    """Create a temporary repo with N prompt files. Returns the repo root."""
    prompts_dir = tmp / "prompts"
    prompts_dir.mkdir()
    for i in range(num_prompts):
        (prompts_dir / f"prompt_{i:04d}.prompt.yml").write_text(
            PROMPT_TEMPLATE.format(i=i), encoding="utf-8"
        )
    # Initialise git so the bundle CLI path (which uses git ls-tree) works
    # if a user ever runs the bench against a real repo. For these benchmarks
    # we only ever bundle the worktree, so git is not strictly required.
    subprocess.run(
        ["git", "init", "-q", str(tmp)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return tmp


def _rss_mb() -> Optional[float]:
    """Best-effort resident-set-size in MB, or ``None`` on platforms without
    the ``resource`` module (Windows).

    Note: ``ru_maxrss`` is the **peak** RSS for the process, not its current
    RSS, so the value only ever goes up. We report it as a soft signal for
    "how big does this process get?", not as a delta measurement.

    ``ru_maxrss`` is reported in bytes on macOS and kilobytes on Linux/BSD.
    """
    if not _RESOURCE_AVAILABLE:
        return None
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return rss / (1024.0 * 1024.0)
    return rss / 1024.0


def _stats(samples: List[float]) -> Dict[str, float]:
    if not samples:
        return {"min": 0.0, "median": 0.0, "mean": 0.0, "p95": 0.0, "max": 0.0}
    s = sorted(samples)
    p95_idx = max(0, int(len(s) * 0.95) - 1)
    return {
        "min": s[0],
        "median": statistics.median(s),
        "mean": statistics.fmean(s),
        "p95": s[p95_idx],
        "max": s[-1],
    }


def bench_render(repo_root: Path, iters: int) -> Dict[str, Any]:
    """Render the same prompt many times and report per-render latency."""
    vault = InstructVault(repo_root=repo_root)
    prompt_path = "prompts/prompt_0000.prompt.yml"
    vars_ = {"ticket_text": "My order is delayed", "customer_name": "Ava"}

    # warm-up so jinja / yaml caches stabilise
    for _ in range(10):
        vault.render(prompt_path, vars=vars_)

    samples_us: List[float] = []
    for _ in range(iters):
        t0 = time.perf_counter_ns()
        vault.render(prompt_path, vars=vars_)
        samples_us.append((time.perf_counter_ns() - t0) / 1000.0)

    return {
        "iters": iters,
        "unit": "microseconds_per_render",
        **_stats(samples_us),
    }


def bench_bundle_load(repo_root: Path, num_prompts: int) -> Dict[str, Any]:
    """Build a bundle for the corpus, then measure cold load time."""
    bundle_path = repo_root / "out" / "ivault.bundle.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    write_bundle(
        bundle_path,
        repo_root=repo_root,
        prompts_dir=repo_root / "prompts",
        ref=None,
    )
    size_bytes = bundle_path.stat().st_size

    # Cold load (instantiate vault from bundle path)
    samples_ms: List[float] = []
    for _ in range(20):
        t0 = time.perf_counter_ns()
        InstructVault(bundle_path=bundle_path)
        samples_ms.append((time.perf_counter_ns() - t0) / 1_000_000.0)

    return {
        "num_prompts": num_prompts,
        "bundle_size_bytes": size_bytes,
        "bundle_size_kb_per_prompt": round(size_bytes / 1024.0 / num_prompts, 3),
        "load_unit": "milliseconds_to_load_bundle",
        **_stats(samples_ms),
    }


def bench_validate_throughput(repo_root: Path, num_prompts: int) -> Dict[str, Any]:
    """Throughput of parse + validate on every prompt file in the corpus."""
    prompt_files = sorted((repo_root / "prompts").glob("*.prompt.yml"))
    if len(prompt_files) != num_prompts:
        raise RuntimeError(
            f"expected {num_prompts} prompt files, found {len(prompt_files)}"
        )

    t0 = time.perf_counter_ns()
    for f in prompt_files:
        load_prompt_spec(f.read_text(encoding="utf-8"), allow_no_tests=False)
    elapsed_s = (time.perf_counter_ns() - t0) / 1_000_000_000.0

    return {
        "num_prompts": num_prompts,
        "elapsed_seconds": round(elapsed_s, 4),
        "prompts_per_second": round(num_prompts / elapsed_s, 1) if elapsed_s > 0 else None,
    }


def bench_memory(repo_root: Path, num_prompts: int) -> Dict[str, Any]:
    """Best-effort peak resident memory after rendering every prompt once.

    ``ru_maxrss`` is the **peak** RSS for the process, so this is a high-water
    mark rather than a working-set delta. Treat it as an upper bound on
    "how much memory will this process need?", not an InstructVault-only cost
    (the Python interpreter + pydantic + jinja2 imports dominate).
    """
    gc.collect()
    vault = InstructVault(repo_root=repo_root)
    prompt_files = sorted((repo_root / "prompts").glob("*.prompt.yml"))
    for f in prompt_files:
        rel = f.relative_to(repo_root).as_posix()
        vault.render(rel, vars={"ticket_text": "x", "customer_name": "y"})

    peak = _rss_mb()
    return {
        "num_prompts": num_prompts,
        "peak_rss_mb": round(peak, 2) if peak is not None else None,
        "available": peak is not None,
        "note": (
            "Peak RSS for the whole process (interpreter + imports + InstructVault). "
            "Reported only on Unix; None on Windows."
        ),
    }


def bench_render_via_bundle(bundle_path: Path, iters: int) -> Dict[str, Any]:
    """Render from a pre-built bundle (no file I/O per render)."""
    vault = InstructVault(bundle_path=bundle_path)
    prompt_path = "prompts/prompt_0000.prompt.yml"
    vars_ = {"ticket_text": "My order is delayed", "customer_name": "Ava"}

    for _ in range(10):
        vault.render(prompt_path, vars=vars_)

    samples_us: List[float] = []
    for _ in range(iters):
        t0 = time.perf_counter_ns()
        vault.render(prompt_path, vars=vars_)
        samples_us.append((time.perf_counter_ns() - t0) / 1000.0)

    return {
        "iters": iters,
        "unit": "microseconds_per_render",
        **_stats(samples_us),
    }


def run(num_prompts: int, iters: int) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ivault-bench-") as tmpdir:
        tmp = Path(tmpdir)
        repo_root = _setup_repo(tmp, num_prompts)

        render = bench_render(repo_root, iters)
        bundle = bench_bundle_load(repo_root, num_prompts)
        bundle_path = repo_root / "out" / "ivault.bundle.json"
        render_bundle = bench_render_via_bundle(bundle_path, iters)
        validate = bench_validate_throughput(repo_root, num_prompts)
        memory = bench_memory(repo_root, num_prompts)

        return {
            "config": {
                "num_prompts": num_prompts,
                "iters": iters,
                "python": sys.version.split()[0],
                "platform": platform.platform(),
            },
            "render_from_worktree": render,
            "render_from_bundle": render_bundle,
            "bundle_load_and_size": bundle,
            "validate_throughput": validate,
            "memory_footprint": memory,
        }


def _human(results: Dict[str, Any]) -> str:
    cfg = results["config"]
    r = results["render_from_worktree"]
    rb = results["render_from_bundle"]
    b = results["bundle_load_and_size"]
    v = results["validate_throughput"]
    m = results["memory_footprint"]

    lines = [
        "=" * 64,
        f"  InstructVault plumbing benchmarks",
        f"  Python {cfg['python']} on {cfg['platform']}",
        f"  Corpus: {cfg['num_prompts']} prompts, {cfg['iters']} render iters",
        "=" * 64,
        "",
        "Render latency (from worktree, per render):",
        f"  median = {r['median']:>8.1f} us    p95 = {r['p95']:>8.1f} us    max = {r['max']:>8.1f} us",
        "",
        "Render latency (from pre-built bundle, per render):",
        f"  median = {rb['median']:>8.1f} us    p95 = {rb['p95']:>8.1f} us    max = {rb['max']:>8.1f} us",
        "",
        "Bundle:",
        f"  size       = {b['bundle_size_bytes']/1024.0:>8.1f} KB total"
        f"  ({b['bundle_size_kb_per_prompt']} KB per prompt)",
        f"  cold load  = {b['median']:>8.2f} ms median over 20 instantiations",
        "",
        "Validate throughput:",
        f"  {v['prompts_per_second']} prompts/second"
        f"  ({v['elapsed_seconds']} s for {v['num_prompts']} prompts)",
        "",
        "Memory footprint (peak RSS, whole process):",
        (
            f"  peak = {m['peak_rss_mb']} MB"
            if m.get("available")
            else "  unavailable on this platform (Windows)"
        ),
        "",
        "Reminder: render latency is the InstructVault path only — it does NOT",
        "include any LLM call. A typical LLM call is 100-1000x slower.",
        "=" * 64,
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="InstructVault plumbing benchmarks")
    parser.add_argument("--num-prompts", type=int, default=100,
                        help="Number of prompts in the synthetic corpus")
    parser.add_argument("--iters", type=int, default=5000,
                        help="Number of render iterations to sample")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="Write full results as JSON to this path")
    args = parser.parse_args()

    if args.num_prompts < 1:
        print("--num-prompts must be >= 1", file=sys.stderr)
        return 2
    if args.iters < 100:
        print("--iters must be >= 100 for meaningful statistics", file=sys.stderr)
        return 2

    results = run(args.num_prompts, args.iters)
    print(_human(results))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nWrote JSON results to {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
