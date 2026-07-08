"""Content-addressed lockfiles for reproducible prompt deployments.

A lockfile pins every prompt to a canonical hash of its *parsed* spec, so the
identity is independent of file format (YAML vs JSON) and line endings
(CRLF vs LF). This makes lock/verify behave identically across repositories,
operating systems, and CI runners.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from .bundle import collect_prompts
from .spec import PromptSpec

LOCK_VERSION = "1.0"


def canonical_spec_hash(spec: PromptSpec) -> str:
    """Stable ``sha256:`` digest of a prompt spec, independent of source format."""
    payload = json.dumps(
        spec.model_dump(by_alias=True, mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_lock(repo_root: Path, prompts_dir: Path, ref: Optional[str]) -> Dict[str, Any]:
    prompts = collect_prompts(repo_root, prompts_dir, ref)
    entries = [
        {"path": p.path, "name": p.spec.name, "spec_sha256": canonical_spec_hash(p.spec)}
        for p in prompts
    ]
    entries.sort(key=lambda e: str(e["path"]))
    return {
        "lock_version": LOCK_VERSION,
        "ref": ref or "WORKTREE",
        "prompts": entries,
    }


def dumps_lock(lock: Dict[str, Any]) -> str:
    """Deterministic serialization: sorted keys, trailing newline, no timestamps."""
    return json.dumps(lock, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def write_lock(
    out_path: Path, *, repo_root: Path, prompts_dir: Path, ref: Optional[str]
) -> Dict[str, Any]:
    lock = build_lock(repo_root, prompts_dir, ref)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(dumps_lock(lock), encoding="utf-8")
    return lock


def _entry_map(prompts: List[Dict[str, Any]]) -> Dict[str, str]:
    return {str(e["path"]): str(e["spec_sha256"]) for e in prompts}


def verify_lock(
    lock: Dict[str, Any], *, repo_root: Path, prompts_dir: Path, ref: Optional[str]
) -> Tuple[bool, List[str]]:
    """Compare a lockfile against the current prompts. Returns (ok, human diffs)."""
    current = build_lock(repo_root, prompts_dir, ref)
    locked_entries = _entry_map(cast(List[Dict[str, Any]], lock.get("prompts", [])))
    current_entries = _entry_map(cast(List[Dict[str, Any]], current["prompts"]))

    diffs: List[str] = []
    for path in sorted(set(current_entries) - set(locked_entries)):
        diffs.append(f"added: {path}")
    for path in sorted(set(locked_entries) - set(current_entries)):
        diffs.append(f"removed: {path}")
    for path in sorted(set(locked_entries) & set(current_entries)):
        if locked_entries[path] != current_entries[path]:
            diffs.append(f"changed: {path}")
    return (not diffs), diffs
