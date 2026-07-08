"""Regression tests for correctness + safety hardening (Phases 0 and 1)."""
from __future__ import annotations

from pathlib import Path

import pytest

from instructvault.io import load_prompt_spec
from instructvault.render import _scan_for_secrets, check_required_vars, render_messages
from instructvault.spec import PromptSpec
from instructvault.store import PromptStore

_NO_TESTS_YAML = """
spec_version: "1.0"
name: no_tests
variables:
  required: [name]
messages:
  - role: user
    content: "Hello {{ name }}"
"""


def test_allow_no_tests_context_is_honored() -> None:
    """Regression: allow_no_tests was silently ignored via a bad context read."""
    spec = load_prompt_spec(_NO_TESTS_YAML, allow_no_tests=True)
    assert spec.name == "no_tests"


def test_tests_required_when_not_allowed() -> None:
    with pytest.raises(ValueError, match="at least one test"):
        load_prompt_spec(_NO_TESTS_YAML, allow_no_tests=False)


def test_model_validate_context_direct() -> None:
    data = {"name": "x", "messages": [{"role": "user", "content": "hi"}]}
    spec = PromptSpec.model_validate(data, context={"allow_no_tests": True})
    assert spec.tests == []


@pytest.mark.parametrize(
    "text",
    [
        "api_key sk-abcdef0123456789abcdef",
        "token: ghp_abcdefghijklmnopqrstuvwxyz012345",
        "secret=abcdefghijklmnop123456",
        "sk-ant-abcdefghijklmnopqrstuvwxyz",
        "-----BEGIN RSA PRIVATE KEY-----",
    ],
)
def test_secret_patterns_detect(text: str) -> None:
    assert _scan_for_secrets(text)


def test_whitespace_separated_secret_now_caught() -> None:
    """Regression: `\\\\s` in a raw string never matched whitespace."""
    assert _scan_for_secrets("api secret abcdef0123456789abcd")


def test_render_safe_blocks_and_redacts() -> None:
    spec = load_prompt_spec(_NO_TESTS_YAML, allow_no_tests=True)
    secret = "sk-abcdefghijklmnopqrstuvwxyz"
    with pytest.raises(ValueError, match="secret"):
        render_messages(spec, {"name": secret}, safe=True)
    msgs = render_messages(spec, {"name": secret}, safe=True, redact=True)
    assert "[REDACTED]" in msgs[-1].content
    assert secret not in msgs[-1].content


def test_check_required_vars_secret_guard() -> None:
    spec = load_prompt_spec(_NO_TESTS_YAML, allow_no_tests=True)
    with pytest.raises(ValueError, match="secret"):
        check_required_vars(spec, {"name": "sk-abcdefghijklmnopqrstuvwxyz"}, safe=True)


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "outside.txt").write_text("secret", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    store = PromptStore(repo)
    with pytest.raises(ValueError, match="escapes repository root"):
        store.read_text("../outside.txt")


def test_read_text_within_repo_ok(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "prompts").mkdir(parents=True)
    (repo / "prompts" / "p.txt").write_text("ok", encoding="utf-8")
    store = PromptStore(repo)
    assert store.read_text("prompts/p.txt") == "ok"
