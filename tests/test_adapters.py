"""Tests for RenderResult provider adapters and the JUnit writer."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from instructvault.eval import TestResult
from instructvault.junit import write_junit_xml
from instructvault.result import RenderResult
from instructvault.spec import PromptMessage


def _result() -> RenderResult:
    msgs = [
        PromptMessage(role="system", content="You are helpful."),
        PromptMessage(role="user", content="Hi"),
    ]
    return RenderResult(
        msgs,
        model="claude-3-5-sonnet",
        provider="anthropic",
        temperature=0.3,
        max_tokens=256,
        prompt_name="greet",
        prompt_path="prompts/greet.prompt.yml",
        ref="prompts/v1.0.0",
    )


def test_render_result_is_list_like() -> None:
    r = _result()
    assert isinstance(r, list)
    assert len(r) == 2
    assert r[0].role == "system"
    assert [m.role for m in r] == ["system", "user"]
    assert r.messages == list(r)
    assert "greet" in repr(r)


def test_to_openai_only_sets_declared_keys() -> None:
    kwargs = _result().to_openai()
    assert kwargs["model"] == "claude-3-5-sonnet"
    assert kwargs["temperature"] == 0.3
    assert kwargs["max_tokens"] == 256
    assert "top_p" not in kwargs  # not declared
    assert kwargs["messages"][0] == {"role": "system", "content": "You are helpful."}


def test_to_anthropic_hoists_system() -> None:
    kwargs = _result().to_anthropic()
    assert kwargs["system"] == "You are helpful."
    assert all(m["role"] != "system" for m in kwargs["messages"])
    assert kwargs["model"] == "claude-3-5-sonnet"


def test_to_litellm_prefixes_provider() -> None:
    kwargs = _result().to_litellm()
    assert kwargs["model"] == "anthropic/claude-3-5-sonnet"


def test_to_litellm_keeps_slash_model() -> None:
    msgs = [PromptMessage(role="user", content="Hi")]
    r = RenderResult(msgs, model="openai/gpt-4o", provider="openai")
    assert r.to_litellm()["model"] == "openai/gpt-4o"


def test_to_dict_roundtrip() -> None:
    d = _result().to_dict()
    assert d["prompt_name"] == "greet"
    assert d["ref"] == "prompts/v1.0.0"
    assert d["messages"][1] == {"role": "user", "content": "Hi"}


def test_junit_counts_pass_fail_skip(tmp_path: Path) -> None:
    out = tmp_path / "junit.xml"
    results = [
        TestResult("ok", True),
        TestResult("bad", False, "assertion failed"),
        TestResult("judged", True, None, skipped=True),
    ]
    write_junit_xml(suite_name="ivault:demo", results=results, out_path=str(out))
    tree = ET.parse(out)
    suite = tree.getroot()
    assert suite.get("tests") == "3"
    assert suite.get("failures") == "1"
    assert suite.get("skipped") == "1"
    cases = {c.get("name"): c for c in suite.findall("testcase")}
    assert cases["bad"].find("failure") is not None
    assert cases["judged"].find("skipped") is not None
    assert cases["ok"].find("failure") is None
