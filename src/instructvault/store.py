from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List, Optional

# Git operations should never hang a runtime request. Bound them defensively.
_GIT_TIMEOUT_SECONDS = 30


class PromptStore:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()

    def _safe_abspath(self, rel_path: str) -> Path:
        """Resolve ``rel_path`` inside the repo, rejecting traversal outside it."""
        candidate = (self.repo_root / rel_path.lstrip("/")).resolve()
        try:
            candidate.relative_to(self.repo_root)
        except ValueError:
            raise ValueError(f"Prompt path escapes repository root: {rel_path}") from None
        return candidate

    def _run_git(self, args: List[str], *, on_error: str) -> str:
        cmd = ["git", "-C", str(self.repo_root), *args]
        try:
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=_GIT_TIMEOUT_SECONDS
            )
        except FileNotFoundError as e:
            raise RuntimeError("git executable not found on PATH") from e
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"git command timed out after {_GIT_TIMEOUT_SECONDS}s: {' '.join(args)}") from e
        if res.returncode != 0:
            raise FileNotFoundError(res.stderr.strip() or on_error)
        return res.stdout

    def mtime_ns(self, rel_path: str) -> int:
        """Modification time (ns) of a worktree file, for cache invalidation."""
        return self._safe_abspath(rel_path.lstrip("/")).stat().st_mtime_ns

    def read_text(self, rel_path: str, ref: Optional[str] = None) -> str:
        normalized = rel_path.lstrip("/")
        if ref is None:
            return self._safe_abspath(normalized).read_text(encoding="utf-8")
        return self._run_git(
            ["show", f"{ref}:{normalized}"],
            on_error=f"Could not read {normalized} at ref {ref}",
        )

    def resolve_ref(self, ref: str) -> str:
        try:
            out = self._run_git(["rev-parse", ref], on_error=f"Could not resolve ref {ref}")
        except FileNotFoundError as e:
            raise ValueError(str(e)) from e
        return out.strip()
