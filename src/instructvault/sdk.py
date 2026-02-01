from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
from .io import load_prompt_spec
from .render import check_required_vars, render_messages
from .spec import PromptMessage, PromptSpec
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
            if prompt_path not in self.bundle:
                raise FileNotFoundError(f"Prompt not found in bundle: {prompt_path}")
            return self.bundle[prompt_path]
        if self.store is None:
            raise ValueError("No repo_root configured")
        return load_prompt_spec(self.store.read_text(prompt_path, ref=ref))
    def render(self, prompt_path: str, vars: Dict[str, Any], ref: Optional[str] = None) -> List[PromptMessage]:
        spec = self.load_prompt(prompt_path, ref=ref)
        check_required_vars(spec, vars)
        return render_messages(spec, vars)
