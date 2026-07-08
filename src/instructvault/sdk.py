from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from .io import load_prompt_spec
from .render import check_required_vars, render_messages
from .result import RenderResult
from .spec import PromptSpec
from .store import PromptStore


class InstructVault:
    """Runtime loader for prompt specs from a git repo or a build-time bundle.

    Specs are cached for speed (safe for use in web servers): immutable git
    refs are cached for the lifetime of the instance, and worktree reads are
    revalidated by file mtime. Pass ``cache=False`` to disable, or call
    :meth:`clear_cache` to reset.
    """

    def __init__(
        self,
        repo_root: Optional[Union[str, Path]] = None,
        bundle_path: Optional[Union[str, Path]] = None,
        *,
        cache: bool = True,
    ):
        if repo_root is None and bundle_path is None:
            raise ValueError("Provide repo_root or bundle_path")
        self.store = PromptStore(Path(repo_root)) if repo_root is not None else None
        self.bundle = None
        if bundle_path is not None:
            data = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
            self.bundle = {p["path"]: PromptSpec.model_validate(p["spec"]) for p in data.get("prompts", [])}
        self._cache_enabled = cache
        # key -> (spec, worktree_mtime_ns or None for pinned refs)
        self._cache: Dict[Tuple[str, Optional[str]], Tuple[PromptSpec, Optional[int]]] = {}
        self._lock = threading.Lock()

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def _load_uncached(self, prompt_path: str, ref: Optional[str]) -> PromptSpec:
        if self.store is None:
            raise ValueError("No repo_root configured")
        return load_prompt_spec(self.store.read_text(prompt_path, ref=ref), allow_no_tests=True)

    def load_prompt(self, prompt_path: str, ref: Optional[str] = None) -> PromptSpec:
        if self.bundle is not None:
            if ref is not None:
                raise ValueError("ref is not supported when using bundle_path")
            if prompt_path not in self.bundle:
                raise FileNotFoundError(f"Prompt not found in bundle: {prompt_path}")
            return self.bundle[prompt_path]
        if self.store is None:
            raise ValueError("No repo_root configured")
        if not self._cache_enabled:
            return self._load_uncached(prompt_path, ref)

        key = (prompt_path, ref)
        with self._lock:
            cached = self._cache.get(key)
        if cached is not None:
            spec, stamp = cached
            if ref is not None:
                return spec  # pinned ref is immutable for this process
            if stamp is not None and self.store.mtime_ns(prompt_path) == stamp:
                return spec

        spec = self._load_uncached(prompt_path, ref)
        stamp = None if ref is not None else self.store.mtime_ns(prompt_path)
        with self._lock:
            self._cache[key] = (spec, stamp)
        return spec
    def render(self, prompt_path: str, vars: Dict[str, Any], ref: Optional[str] = None, *, safe: bool = False, strict_vars: bool = False, redact: bool = False) -> RenderResult:
        spec = self.load_prompt(prompt_path, ref=ref)
        check_required_vars(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
        msgs = render_messages(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
        md = spec.model_defaults.model_dump()
        return RenderResult(
            msgs,
            model=md.get("model"),
            provider=md.get("provider"),
            temperature=md.get("temperature"),
            top_p=md.get("top_p"),
            max_tokens=md.get("max_tokens"),
            prompt_name=spec.name,
            prompt_path=prompt_path,
            ref=ref,
        )
