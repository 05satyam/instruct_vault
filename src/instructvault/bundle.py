from __future__ import annotations
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .io import load_prompt_spec
from .spec import PromptSpec
from .store import PromptStore

@dataclass(frozen=True)
class BundlePrompt:
    path: str
    spec: PromptSpec

def _list_files_at_ref(repo_root: Path, ref: str, rel_dir: str) -> List[str]:
    cmd = ["git", "-C", str(repo_root), "ls-tree", "-r", "--name-only", ref, rel_dir]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise ValueError(res.stderr.strip() or f"Could not list files at ref {ref}")
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]

def _is_prompt_file(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".prompt.yml") or lower.endswith(".prompt.yaml") or lower.endswith(".prompt.json")

def collect_prompts(repo_root: Path, prompts_dir: Path, ref: Optional[str]) -> List[BundlePrompt]:
    store = PromptStore(repo_root)
    prompts: List[BundlePrompt] = []
    if ref is None:
        if not prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")
        try:
            prompts_dir.relative_to(repo_root)
        except Exception:
            raise ValueError("prompts_dir must be within repo_root")
        for p in sorted(prompts_dir.rglob("*.prompt.y*ml")):
            rel_path = p.relative_to(repo_root).as_posix()
            spec = load_prompt_spec(p.read_text(encoding="utf-8"), allow_no_tests=True)
            prompts.append(BundlePrompt(rel_path, spec))
        for p in sorted(prompts_dir.rglob("*.prompt.json")):
            rel_path = p.relative_to(repo_root).as_posix()
            spec = load_prompt_spec(p.read_text(encoding="utf-8"), allow_no_tests=True)
            prompts.append(BundlePrompt(rel_path, spec))
        if not prompts:
            raise ValueError(f"No prompt files found in {prompts_dir}")
        return prompts

    rel_dir = prompts_dir.relative_to(repo_root).as_posix()
    for rel_path in _list_files_at_ref(repo_root, ref, rel_dir):
        if not _is_prompt_file(rel_path):
            continue
        spec = load_prompt_spec(store.read_text(rel_path, ref=ref), allow_no_tests=True)
        prompts.append(BundlePrompt(rel_path, spec))
    if not prompts:
        raise ValueError(f"No prompt files found at ref {ref} in {rel_dir}")
    return prompts

def write_bundle(out_path: Path, *, repo_root: Path, prompts_dir: Path, ref: Optional[str]) -> None:
    prompts = collect_prompts(repo_root, prompts_dir, ref)
    payload = {
        "bundle_version": "1.0",
        "ref": ref or "WORKTREE",
        "prompts": [
            {"path": p.path, "spec": p.spec.model_dump(by_alias=True)}
            for p in prompts
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
