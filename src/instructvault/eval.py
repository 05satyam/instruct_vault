from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .judge import judge_output
from .policy import run_render_policy
from .providers import Provider
from .render import check_required_vars, render_joined_text, render_messages
from .spec import AssertSpec, DatasetRow, PromptSpec


@dataclass(frozen=True)
class TestResult:
    name: str
    passed: bool
    error: str | None = None
    skipped: bool = False

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

def _evaluate(
    assert_spec: AssertSpec, output: str, judge_provider: Provider | None
) -> tuple[bool, bool, str | None]:
    """Return (passed, skipped, error) combining deterministic + judge checks."""
    deterministic_ok = _match_assert(assert_spec, output)
    if assert_spec.judge is None:
        return deterministic_ok, False, None if deterministic_ok else "assertion failed"

    if judge_provider is None:
        # Judge portion cannot run without a provider.
        if not assert_spec.has_deterministic():
            return True, True, None  # nothing evaluated -> skipped, not failed
        return deterministic_ok, False, None if deterministic_ok else "assertion failed"

    judged_ok, score = judge_output(output, assert_spec.judge, judge_provider)
    passed = deterministic_ok and judged_ok
    if passed:
        return True, False, None
    if not judged_ok:
        return False, False, f"judge score {score:.2f} < threshold {assert_spec.judge.threshold}"
    return False, False, "assertion failed"


def _produce_output(spec: PromptSpec, vars: dict[str, Any], *, safe: bool, strict_vars: bool, redact: bool, provider: Provider | None) -> str:
    """Rendered prompt text by default; the model's reply when a provider is given."""
    if provider is None:
        return render_joined_text(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
    msgs = render_messages(spec, vars, safe=safe, strict_vars=strict_vars, redact=redact)
    payload = [{"role": m.role, "content": m.content} for m in msgs]
    params = spec.model_defaults.model_dump(exclude_none=True)
    return provider(payload, params)

def run_inline_tests(spec: PromptSpec, *, safe: bool = False, strict_vars: bool = False, redact: bool = False, policy: object | None = None, provider: Provider | None = None, judge_provider: Provider | None = None) -> tuple[bool, list[TestResult]]:
    results: list[TestResult] = []
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
            passed, skipped, error = _evaluate(t.assert_, out, judge_provider)
            results.append(TestResult(t.name, passed, error, skipped))
            all_ok = all_ok and passed
        except Exception as e:
            results.append(TestResult(t.name, False, str(e)))
            all_ok = False
    return all_ok, results

def run_dataset(spec: PromptSpec, rows: list[DatasetRow], *, safe: bool = False, strict_vars: bool = False, redact: bool = False, policy: object | None = None, provider: Provider | None = None, judge_provider: Provider | None = None) -> tuple[bool, list[TestResult]]:
    results: list[TestResult] = []
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
            passed, skipped, error = _evaluate(row.assert_, out, judge_provider)
            results.append(TestResult(name, passed, error, skipped))
            all_ok = all_ok and passed
        except Exception as e:
            results.append(TestResult(name, False, str(e)))
            all_ok = False
    return all_ok, results
