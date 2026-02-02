from __future__ import annotations
from typing import Any, Dict, List
import re
from jinja2 import Environment, StrictUndefined
from .spec import PromptMessage, PromptSpec

_env = Environment(undefined=StrictUndefined, autoescape=False)

_SECRET_PATTERNS = [
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("pypi_token", re.compile(r"pypi-[A-Za-z0-9]{20,}")),
    ("generic_token", re.compile(r"(?:api|token|secret)[=_:\\s-]{1,}[A-Za-z0-9\\-]{16,}", re.IGNORECASE)),
]

def _scan_for_secrets(text: str) -> List[str]:
    hits: List[str] = []
    for name, pat in _SECRET_PATTERNS:
        if pat.search(text):
            hits.append(name)
    return hits

def check_required_vars(spec: PromptSpec, vars: Dict[str, Any], *, safe: bool = False, strict_vars: bool = False, redact: bool = False) -> None:
    missing = [k for k in spec.variables.required if k not in vars]
    if missing:
        raise ValueError(f"Missing required vars: {missing}")
    if strict_vars:
        allowed = set(spec.variables.required + spec.variables.optional)
        extra = [k for k in vars.keys() if k not in allowed]
        if extra:
            raise ValueError(f"Unexpected vars: {extra}")
    if safe and not redact:
        for v in vars.values():
            if isinstance(v, str):
                hits = _scan_for_secrets(v)
                if hits:
                    raise ValueError(f"Potential secret detected in vars: {hits}")

def render_messages(spec: PromptSpec, vars: Dict[str, Any], *, safe: bool = False, strict_vars: bool = False, redact: bool = False) -> List[PromptMessage]:
    rendered: List[PromptMessage] = []
    for m in spec.messages:
        tmpl = _env.from_string(m.content)
        content = tmpl.render(**vars)
        if safe:
            hits = _scan_for_secrets(content)
            if hits:
                if redact:
                    for _, pat in _SECRET_PATTERNS:
                        content = pat.sub("[REDACTED]", content)
                else:
                    raise ValueError(f"Potential secret detected in rendered output: {hits}")
        rendered.append(PromptMessage(role=m.role, content=content))
    return rendered

def render_joined_text(spec: PromptSpec, vars: Dict[str, Any], *, safe: bool = False, strict_vars: bool = False, redact: bool = False) -> str:
    msgs = render_messages(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
    return "\n\n".join([f"{m.role}: {m.content}" for m in msgs])
