"""Tests for lockfile, runtime cache, judge evals, and schema generation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from instructvault import InstructVault
from instructvault.eval import run_inline_tests
from instructvault.io import load_prompt_spec
from instructvault.lock import build_lock, canonical_spec_hash, verify_lock, write_lock
from instructvault.schema import prompt_json_schema

_YAML = """
spec_version: "1.0"
name: greet
variables:
  required: [name]
messages:
  - role: system
    content: "You are helpful."
  - role: user
    content: "Say hi to {{ name }}"
tests:
  - name: t
    vars: { name: "Ava" }
    assert: { contains_any: ["hi"] }
"""

_JSON_EQUIVALENT = json.dumps(
    {
        "spec_version": "1.0",
        "name": "greet",
        "variables": {"required": ["name"]},
        "messages": [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Say hi to {{ name }}"},
        ],
        "tests": [{"name": "t", "vars": {"name": "Ava"}, "assert": {"contains_any": ["hi"]}}],
    }
)


def _write_prompts(repo: Path) -> Path:
    prompts = repo / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "greet.prompt.yml").write_text(_YAML, encoding="utf-8")
    return prompts


# ----------------------------- lockfile ------------------------------------

def test_canonical_hash_format_independent() -> None:
    yaml_spec = load_prompt_spec(_YAML)
    json_spec = load_prompt_spec(_JSON_EQUIVALENT)
    assert canonical_spec_hash(yaml_spec) == canonical_spec_hash(json_spec)


def test_lock_is_deterministic_and_verifies(tmp_path: Path) -> None:
    prompts = _write_prompts(tmp_path)
    out = tmp_path / "ivault.lock.json"
    lock1 = write_lock(out, repo_root=tmp_path, prompts_dir=prompts, ref=None)
    first_bytes = out.read_bytes()
    lock2 = build_lock(tmp_path, prompts, ref=None)
    assert lock1 == lock2
    # Rewriting produces byte-identical output (deterministic).
    write_lock(out, repo_root=tmp_path, prompts_dir=prompts, ref=None)
    assert out.read_bytes() == first_bytes

    ok, diffs = verify_lock(json.loads(out.read_text()), repo_root=tmp_path, prompts_dir=prompts, ref=None)
    assert ok and diffs == []


def test_verify_detects_semantic_change(tmp_path: Path) -> None:
    prompts = _write_prompts(tmp_path)
    out = tmp_path / "ivault.lock.json"
    write_lock(out, repo_root=tmp_path, prompts_dir=prompts, ref=None)
    p = prompts / "greet.prompt.yml"
    p.write_text(_YAML.replace("You are helpful.", "You are rude."), encoding="utf-8")
    ok, diffs = verify_lock(json.loads(out.read_text()), repo_root=tmp_path, prompts_dir=prompts, ref=None)
    assert not ok
    assert any("changed" in d for d in diffs)


def test_verify_ignores_comment_only_change(tmp_path: Path) -> None:
    prompts = _write_prompts(tmp_path)
    out = tmp_path / "ivault.lock.json"
    write_lock(out, repo_root=tmp_path, prompts_dir=prompts, ref=None)
    p = prompts / "greet.prompt.yml"
    p.write_text(_YAML + "\n# a trailing comment\n", encoding="utf-8")
    ok, _ = verify_lock(json.loads(out.read_text()), repo_root=tmp_path, prompts_dir=prompts, ref=None)
    assert ok


# ----------------------------- runtime cache -------------------------------

def test_worktree_cache_invalidates_on_mtime(tmp_path: Path) -> None:
    _write_prompts(tmp_path)
    vault = InstructVault(repo_root=tmp_path)
    first = vault.load_prompt("prompts/greet.prompt.yml")
    assert first is vault.load_prompt("prompts/greet.prompt.yml")  # cached identity

    p = tmp_path / "prompts" / "greet.prompt.yml"
    import os
    p.write_text(_YAML.replace("You are helpful.", "You are super helpful."), encoding="utf-8")
    os.utime(p, ns=(1, 2))  # force a distinct mtime
    reloaded = vault.load_prompt("prompts/greet.prompt.yml")
    assert reloaded is not first
    assert "super helpful" in reloaded.messages[0].content


def test_cache_disabled_reloads(tmp_path: Path) -> None:
    _write_prompts(tmp_path)
    vault = InstructVault(repo_root=tmp_path, cache=False)
    a = vault.load_prompt("prompts/greet.prompt.yml")
    b = vault.load_prompt("prompts/greet.prompt.yml")
    assert a is not b


def test_clear_cache(tmp_path: Path) -> None:
    _write_prompts(tmp_path)
    vault = InstructVault(repo_root=tmp_path)
    a = vault.load_prompt("prompts/greet.prompt.yml")
    vault.clear_cache()
    b = vault.load_prompt("prompts/greet.prompt.yml")
    assert a is not b


# ----------------------------- judge evals ---------------------------------

_JUDGE_YAML = """
spec_version: "1.0"
name: judged
variables:
  required: [topic]
messages:
  - role: user
    content: "Explain {{ topic }}"
tests:
  - name: quality
    vars: { topic: "gravity" }
    assert:
      judge:
        rubric: "The answer clearly explains the topic."
        threshold: 0.7
"""


def test_judge_skipped_without_provider() -> None:
    spec = load_prompt_spec(_JUDGE_YAML)
    ok, results = run_inline_tests(spec)
    assert ok is True
    assert results[0].skipped is True
    assert results[0].passed is True


def test_judge_passes_with_high_score() -> None:
    spec = load_prompt_spec(_JUDGE_YAML)
    judge = lambda messages, params: "0.9"  # noqa: E731
    ok, results = run_inline_tests(spec, judge_provider=judge)
    assert ok is True
    assert results[0].skipped is False
    assert results[0].passed is True


def test_judge_fails_with_low_score() -> None:
    spec = load_prompt_spec(_JUDGE_YAML)
    judge = lambda messages, params: "0.2"  # noqa: E731
    ok, results = run_inline_tests(spec, judge_provider=judge)
    assert ok is False
    assert results[0].passed is False
    assert "judge score" in (results[0].error or "")


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("0.8", 0.8),
        ("80%", 0.8),
        ("8/10", 0.8),
        ("I rate this 8 out of 10", 0.8),
        ("9.5/10", 0.95),
        ("1", 1.0),
        ("10/10", 1.0),
        ("150%", 1.0),  # clamped
    ],
)
def test_judge_score_formats(reply: str, expected: float) -> None:
    from instructvault.judge import _parse_score

    assert abs(_parse_score(reply) - expected) < 1e-9


def test_judge_score_unparseable_raises() -> None:
    from instructvault.judge import _parse_score

    with pytest.raises(ValueError, match="Could not parse"):
        _parse_score("no number here")


_JSON_SCHEMA_YAML = """
spec_version: "1.0"
name: schema_check
variables:
  required: [payload]
messages:
  - role: user
    content: "{{ payload }}"
tests:
  - name: valid
    vars: { payload: '{"n": 5}' }
    assert:
      json_schema:
        type: object
        properties: { n: { type: integer } }
        required: [n]
  - name: invalid
    vars: { payload: '{"n": "not-an-int"}' }
    assert:
      json_schema:
        type: object
        properties: { n: { type: integer } }
        required: [n]
"""


def test_json_schema_failure_is_clean_not_raised() -> None:
    from instructvault.providers import _mock_provider

    spec = load_prompt_spec(_JSON_SCHEMA_YAML)
    # The mock provider echoes the user message (pure JSON) so the schema applies.
    ok, results = run_inline_tests(spec, provider=_mock_provider)
    by_name = {r.name: r for r in results}
    assert by_name["valid"].passed is True
    # A schema mismatch is a normal failure, not a raised exception.
    assert by_name["invalid"].passed is False
    assert by_name["invalid"].error == "assertion failed"
    assert ok is False


# ----------------------------- schema --------------------------------------

def test_schema_shape() -> None:
    schema = prompt_json_schema()
    assert schema["$schema"].startswith("https://json-schema.org/")
    assert "$id" in schema
    assert "messages" in schema["properties"]
    assert "name" in schema["properties"]


def test_schema_is_deterministic() -> None:
    assert prompt_json_schema() == prompt_json_schema()


# ----------------------------- multi-path validate -------------------------

def test_init_generates_verifiable_lockfile(tmp_path: Path) -> None:
    from instructvault.scaffold import init_repo

    init_repo(tmp_path)
    lockfile = tmp_path / "ivault.lock.json"
    assert lockfile.exists()
    ok, diffs = verify_lock(
        json.loads(lockfile.read_text()),
        repo_root=tmp_path,
        prompts_dir=tmp_path / "prompts",
        ref=None,
    )
    assert ok and diffs == []


def test_judge_example_prompt_is_valid_and_deterministic() -> None:
    example = Path(__file__).resolve().parent.parent / "examples" / "prompts" / "judged_summary.prompt.yml"
    spec = load_prompt_spec(example.read_text(encoding="utf-8"), allow_no_tests=False)
    ok, results = run_inline_tests(spec)  # no judge provider -> deterministic only
    assert ok is True
    assert results[0].skipped is False  # the contains_any check still ran


def test_validate_accepts_multiple_paths(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from instructvault.cli import app

    prompts = _write_prompts(tmp_path)
    (prompts / "second.prompt.yml").write_text(_YAML.replace("name: greet", "name: greet2"), encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "validate",
            str(prompts / "greet.prompt.yml"),
            str(prompts / "second.prompt.yml"),
            "--repo",
            str(tmp_path),
        ],
    )
    assert res.exit_code == 0
