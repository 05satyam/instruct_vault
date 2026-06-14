from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import json
import re
from .spec import AssertSpec, DatasetRow, PromptSpec
from .render import check_required_vars, render_joined_text, render_messages
from .policy import run_render_policy
from .providers import Provider

@dataclass(frozen=True)
class TestResult:
    name: str
    passed: bool
    error: Optional[str] = None

def _match_assert(assert_spec: AssertSpec, text: str) -> bool:
    t = text.lower()
    ok = True
    if assert_spec.contains_any:
        ok = ok and any(s.lower() in t for s in assert_spec.contains_any)
    if assert_spec.contains_all:
        ok = ok and all(s.lower() in t for s in assert_spec.contains_all)
    if assert_spec.not_contains:
        ok = ok and all(s.lower() not in t for s in assert_spec.not_contains)
    if assert_spec.matches:
        ok = ok and all(re.search(p, text) for p in assert_spec.matches)
    if assert_spec.not_matches:
        ok = ok and all(not re.search(p, text) for p in assert_spec.not_matches)
    if assert_spec.json_schema:
        try:
            obj = json.loads(text)
        except Exception:
            return False
        try:
            import jsonschema  # type: ignore
        except Exception as e:
            raise ValueError("jsonschema is required for json_schema assertions") from e
        jsonschema.validate(instance=obj, schema=assert_spec.json_schema)
    return ok

def _produce_output(spec: PromptSpec, vars: dict, *, safe: bool, strict_vars: bool, redact: bool, provider: Optional[Provider]) -> str:
    """Rendered prompt text by default; the model's reply when a provider is given."""
    if provider is None:
        return render_joined_text(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
    msgs = render_messages(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
    payload = [{"role": m.role, "content": m.content} for m in msgs]
    params = spec.model_defaults.model_dump(exclude_none=True)
    return provider(payload, params)

def run_inline_tests(spec: PromptSpec, *, safe: bool = False, strict_vars: bool = False, redact: bool = False, policy: Optional[object] = None, provider: Optional[Provider] = None) -> Tuple[bool, List[TestResult]]:
    results: List[TestResult] = []
    all_ok = True
    for t in spec.tests:
        try:
            check_required_vars(spec, t.vars, safe=safe, strict_vars=strict_vars, redact=redact)
            out = _produce_output(spec, t.vars, safe=safe, strict_vars=strict_vars, redact=redact, provider=provider)
            errors = run_render_policy(policy, out, {"prompt": spec.name, "test": t.name, "kind": "inline"})
            if errors:
                results.append(TestResult(t.name, False, "; ".join(errors)))
                all_ok = False
                continue
            passed = _match_assert(t.assert_, out)
            results.append(TestResult(t.name, passed))
            all_ok = all_ok and passed
        except Exception as e:
            results.append(TestResult(t.name, False, str(e)))
            all_ok = False
    return all_ok, results

def run_dataset(spec: PromptSpec, rows: List[DatasetRow], *, safe: bool = False, strict_vars: bool = False, redact: bool = False, policy: Optional[object] = None, provider: Optional[Provider] = None) -> Tuple[bool, List[TestResult]]:
    results: List[TestResult] = []
    all_ok = True
    for i, row in enumerate(rows, start=1):
        name = f"dataset_row_{i}"
        try:
            check_required_vars(spec, row.vars, safe=safe, strict_vars=strict_vars, redact=redact)
            out = _produce_output(spec, row.vars, safe=safe, strict_vars=strict_vars, redact=redact, provider=provider)
            errors = run_render_policy(policy, out, {"prompt": spec.name, "test": name, "kind": "dataset"})
            if errors:
                results.append(TestResult(name, False, "; ".join(errors)))
                all_ok = False
                continue
            passed = _match_assert(row.assert_, out)
            results.append(TestResult(name, passed))
            all_ok = all_ok and passed
        except Exception as e:
            results.append(TestResult(name, False, str(e)))
            all_ok = False
    return all_ok, results
