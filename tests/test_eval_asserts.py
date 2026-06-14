from __future__ import annotations
from instructvault.spec import PromptSpec
from instructvault.eval import run_inline_tests
from instructvault.providers import get_provider

def _spec_with_assert(assert_block: dict) -> PromptSpec:
    data = {
        "spec_version": "1.0",
        "name": "t",
        "variables": {"required": []},
        "messages": [{"role": "user", "content": "hello 123"}],
        "tests": [{"name": "t1", "vars": {}, "assert": assert_block}],
    }
    return PromptSpec.model_validate(data)

def test_regex_matches() -> None:
    spec = _spec_with_assert({"matches": [r"hello\s+\d+"]})
    ok, _ = run_inline_tests(spec)
    assert ok is True

def test_regex_not_matches() -> None:
    spec = _spec_with_assert({"not_matches": [r"goodbye"]})
    ok, _ = run_inline_tests(spec)
    assert ok is True

def test_json_schema_assertion_requires_json() -> None:
    spec = _spec_with_assert({"json_schema": {"type": "object"}})
    ok, _ = run_inline_tests(spec)
    assert ok is False

def test_provider_asserts_on_model_reply() -> None:
    # mock provider echoes the user message, so the assert runs on the "reply".
    spec = _spec_with_assert({"contains_all": ["hello 123"]})
    ok, _ = run_inline_tests(spec, provider=get_provider("mock"))
    assert ok is True

def test_unknown_provider_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        get_provider("nope")
