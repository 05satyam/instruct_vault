from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_policy_module(path: Optional[str]) -> Optional[object]:
    if not path:
        return None
    p = Path(path)
    spec = importlib.util.spec_from_file_location("ivault_policy", p)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load policy module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_spec_policy(mod: Optional[object], spec_dict: Dict[str, Any]) -> List[str]:
    if mod is None:
        return []
    fn = getattr(mod, "check_spec", None)
    if fn is None:
        return []
    res = fn(spec_dict)
    return list(res) if res else []

def run_render_policy(mod: Optional[object], text: str, context: Dict[str, Any]) -> List[str]:
    if mod is None:
        return []
    fn = getattr(mod, "check_render", None)
    if fn is None:
        return []
    res = fn(text, context)
    return list(res) if res else []
