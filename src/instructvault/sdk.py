from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
import json
from .io import load_prompt_spec
from .render import check_required_vars, render_messages
from .result import RenderResult
from .spec import PromptSpec
from .store import PromptStore

class InstructVault:
    def __init__(self, repo_root: Optional[Union[str, Path]] = None, bundle_path: Optional[Union[str, Path]] = None):
        if repo_root is None and bundle_path is None:
            raise ValueError("Provide repo_root or bundle_path")
        self.store = PromptStore(Path(repo_root)) if repo_root is not None else None
        self.bundle = None
        if bundle_path is not None:
            data = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
            self.bundle = {p["path"]: PromptSpec.model_validate(p["spec"]) for p in data.get("prompts", [])}

    def load_prompt(self, prompt_path: str, ref: Optional[str] = None) -> PromptSpec:
        if self.bundle is not None:
            if ref is not None:
                raise ValueError("ref is not supported when using bundle_path")
            if prompt_path not in self.bundle:
                raise FileNotFoundError(f"Prompt not found in bundle: {prompt_path}")
            return self.bundle[prompt_path]
        if self.store is None:
            raise ValueError("No repo_root configured")
        return load_prompt_spec(self.store.read_text(prompt_path, ref=ref), allow_no_tests=True)
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
