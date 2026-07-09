from __future__ import annotations

from instructvault.eval import run_inline_tests
from instructvault.providers import get_provider
from instructvault.spec import PromptSpec


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

def test_ollama_provider_is_registered() -> None:
    assert get_provider("ollama") is not None

def test_ollama_provider_maps_params(monkeypatch) -> None:
    import sys
    import types
    from unittest.mock import MagicMock

    fake_client = MagicMock()
    fake_client.chat.return_value.message.content = "reply text"
    fake_module = types.ModuleType("ollama")
    fake_module.Client = MagicMock(return_value=fake_client)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ollama", fake_module)

    provider = get_provider("ollama")
    assert provider is not None
    result = provider([{"role": "user", "content": "hi"}], {"max_tokens": 50, "temperature": 0.2})

    assert result == "reply text"
    fake_client.chat.assert_called_once_with(
        model="llama3.2", messages=[{"role": "user", "content": "hi"}], options={"num_predict": 50, "temperature": 0.2}
    )

def test_ollama_provider_live() -> None:
    """Opportunistic smoke test against a real local Ollama server; skips if none is reachable."""
    import pytest

    provider = get_provider("ollama")
    assert provider is not None
    try:
        result = provider([{"role": "user", "content": "Reply with exactly one word: pong"}], {"temperature": 0})
    except Exception as exc:  # no local Ollama server, or default model not pulled
        pytest.skip(f"local Ollama server not available: {exc}")

    assert isinstance(result, str) and result.strip() != ""
