from __future__ import annotations
from typing import Any, Dict, List
from jinja2 import Environment, StrictUndefined
from .spec import PromptMessage, PromptSpec

_env = Environment(undefined=StrictUndefined, autoescape=False)

def check_required_vars(spec: PromptSpec, vars: Dict[str, Any]) -> None:
    missing = [k for k in spec.variables.required if k not in vars]
    if missing:
        raise ValueError(f"Missing required vars: {missing}")

def render_messages(spec: PromptSpec, vars: Dict[str, Any]) -> List[PromptMessage]:
    rendered: List[PromptMessage] = []
    for m in spec.messages:
        tmpl = _env.from_string(m.content)
        rendered.append(PromptMessage(role=m.role, content=tmpl.render(**vars)))
    return rendered

def render_joined_text(spec: PromptSpec, vars: Dict[str, Any]) -> str:
    msgs = render_messages(spec, vars)
    return "\n\n".join([f"{m.role}: {m.content}" for m in msgs])
