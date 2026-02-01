from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Optional

class PromptStore:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()

    def read_text(self, rel_path: str, ref: Optional[str] = None) -> str:
        rel_path = rel_path.lstrip("/")
        if ref is None:
            return (self.repo_root / rel_path).read_text(encoding="utf-8")
        cmd = ["git", "-C", str(self.repo_root), "show", f"{ref}:{rel_path}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise FileNotFoundError(res.stderr.strip() or f"Could not read {rel_path} at ref {ref}")
        return res.stdout

    def resolve_ref(self, ref: str) -> str:
        cmd = ["git", "-C", str(self.repo_root), "rev-parse", ref]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise ValueError(res.stderr.strip() or f"Could not resolve ref {ref}")
        return res.stdout.strip()
