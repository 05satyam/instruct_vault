"""Statistical benchmarks via ``pytest-benchmark``.

Run with:

    pip install pytest-benchmark
    pytest benchmarks/test_perf.py --benchmark-only

These tests are intentionally **not** picked up by the default ``pytest``
invocation (``pyproject.toml`` restricts ``testpaths`` to ``tests``), so they
do not slow down CI.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent

# Prefer in-repo source if available, otherwise rely on whatever is installed.
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Make ``run.py`` (sibling file in benchmarks/) importable regardless of cwd.
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from instructvault import InstructVault  # noqa: E402
from instructvault.bundle import write_bundle  # noqa: E402
from instructvault.io import load_prompt_spec  # noqa: E402
from run import PROMPT_TEMPLATE  # noqa: E402


@pytest.fixture(scope="module")
def repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a 100-prompt corpus once per module."""
    tmp = tmp_path_factory.mktemp("ivault-bench")
    prompts_dir = tmp / "prompts"
    prompts_dir.mkdir()
    for i in range(100):
        (prompts_dir / f"prompt_{i:04d}.prompt.yml").write_text(
            PROMPT_TEMPLATE.format(i=i), encoding="utf-8"
        )
    subprocess.run(
        ["git", "init", "-q", str(tmp)],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return tmp


@pytest.fixture(scope="module")
def bundle_path(repo: Path) -> Path:
    out = repo / "out" / "ivault.bundle.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_bundle(out, repo_root=repo, prompts_dir=repo / "prompts", ref=None)
    return out


def test_render_from_worktree(benchmark, repo: Path) -> None:
    """Per-render latency when reading the file from disk every time."""
    vault = InstructVault(repo_root=repo)
    vars_ = {"ticket_text": "delayed", "customer_name": "Ava"}
    benchmark(vault.render, "prompts/prompt_0000.prompt.yml", vars=vars_)


def test_render_from_bundle(benchmark, bundle_path: Path) -> None:
    """Per-render latency from a pre-built bundle (no per-render file I/O)."""
    vault = InstructVault(bundle_path=bundle_path)
    vars_ = {"ticket_text": "delayed", "customer_name": "Ava"}
    benchmark(vault.render, "prompts/prompt_0000.prompt.yml", vars=vars_)


def test_bundle_cold_load(benchmark, bundle_path: Path) -> None:
    """Time to instantiate a vault from a 100-prompt bundle."""
    benchmark(InstructVault, bundle_path=bundle_path)


def test_validate_one_prompt(benchmark, repo: Path) -> None:
    """Parse + validate a single prompt file."""
    text = (repo / "prompts" / "prompt_0000.prompt.yml").read_text(encoding="utf-8")
    benchmark(load_prompt_spec, text, allow_no_tests=False)
