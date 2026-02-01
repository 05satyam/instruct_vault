from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
from .spec import AssertSpec, DatasetRow, PromptSpec
from .render import check_required_vars, render_joined_text

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
    return ok

def run_inline_tests(spec: PromptSpec) -> Tuple[bool, List[TestResult]]:
    results: List[TestResult] = []
    all_ok = True
    for t in spec.tests:
        try:
            check_required_vars(spec, t.vars)
            out = render_joined_text(spec, t.vars)
            passed = _match_assert(t.assert_, out)
            results.append(TestResult(t.name, passed))
            all_ok = all_ok and passed
        except Exception as e:
            results.append(TestResult(t.name, False, str(e)))
            all_ok = False
    return all_ok, results

def run_dataset(spec: PromptSpec, rows: List[DatasetRow]) -> Tuple[bool, List[TestResult]]:
    results: List[TestResult] = []
    all_ok = True
    for i, row in enumerate(rows, start=1):
        name = f"dataset_row_{i}"
        try:
            check_required_vars(spec, row.vars)
            out = render_joined_text(spec, row.vars)
            passed = _match_assert(row.assert_, out)
            results.append(TestResult(name, passed))
            all_ok = all_ok and passed
        except Exception as e:
            results.append(TestResult(name, False, str(e)))
            all_ok = False
    return all_ok, results
