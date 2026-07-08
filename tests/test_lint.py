from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from instructvault.cli import app
from instructvault.io import load_prompt_spec
from instructvault.lint import count_by_severity, gate, run_lint

runner = CliRunner()

_CLEAN = """
name: greeter
description: Greets a user by name.
messages:
  - role: system
    content: "You are friendly."
  - role: user
    content: "Say hi to {{ name }}."
"""

_NO_DESC = """
name: greeter
messages:
  - role: user
    content: "Say hi to {{ name }}."
"""

_SECRET = """
name: leaky
description: Has a hardcoded key.
messages:
  - role: system
    content: "Use key sk-ant-abcdefghijklmnopqrstuvwxyz012345 to authenticate."
"""


def _spec(text: str):
    return load_prompt_spec(text, allow_no_tests=True)


def test_clean_prompt_has_no_findings() -> None:
    findings = run_lint([("greeter.prompt.yml", _spec(_CLEAN))])
    assert findings == []


def test_missing_description_is_a_warning() -> None:
    findings = run_lint([("greeter.prompt.yml", _spec(_NO_DESC))])
    assert len(findings) == 1
    assert findings[0].rule_id == "IV002"
    assert findings[0].severity == "warning"


def test_secret_in_template_is_an_error() -> None:
    findings = run_lint([("leaky.prompt.yml", _spec(_SECRET))])
    ids = {f.rule_id for f in findings}
    assert "IV001" in ids
    iv001 = next(f for f in findings if f.rule_id == "IV001")
    assert iv001.severity == "error"
    assert iv001.location == "system"


def test_gate_thresholds() -> None:
    warn_only = run_lint([("g.prompt.yml", _spec(_NO_DESC))])
    assert gate(warn_only, None) is True
    assert gate(warn_only, "error") is True   # only a warning present
    assert gate(warn_only, "warning") is False
    err = run_lint([("l.prompt.yml", _spec(_SECRET))])
    assert gate(err, "error") is False


def test_count_by_severity() -> None:
    findings = run_lint(
        [("g.prompt.yml", _spec(_NO_DESC)), ("l.prompt.yml", _spec(_SECRET))]
    )
    counts = count_by_severity(findings)
    assert counts["error"] >= 1
    assert counts["warning"] >= 1


def _write(tmp_path: Path, name: str, text: str) -> None:
    (tmp_path / name).write_text(text, encoding="utf-8")


def test_cli_json_and_gate(tmp_path: Path) -> None:
    _write(tmp_path, "leaky.prompt.yml", _SECRET)
    res = runner.invoke(
        app,
        ["lint", "leaky.prompt.yml", "--repo", str(tmp_path), "--format", "json",
         "--fail-under", "error"],
    )
    assert res.exit_code == 1
    payload = json.loads(res.stdout)
    assert payload["ok"] is False
    assert any(f["rule_id"] == "IV001" for f in payload["findings"])


def test_cli_md_scorecard(tmp_path: Path) -> None:
    _write(tmp_path, "greeter.prompt.yml", _NO_DESC)
    res = runner.invoke(
        app, ["lint", "greeter.prompt.yml", "--repo", str(tmp_path), "--format", "md"]
    )
    assert res.exit_code == 0  # no --fail-under => never fails
    assert "InstructVault Prompt Lint" in res.stdout
    assert "IV002" in res.stdout


def test_cli_unparseable_prompt_reports_iv000(tmp_path: Path) -> None:
    _write(tmp_path, "broken.prompt.yml", "name: [unclosed\n")
    res = runner.invoke(
        app,
        ["lint", "broken.prompt.yml", "--repo", str(tmp_path), "--format", "json",
         "--fail-under", "error"],
    )
    assert res.exit_code == 1
    payload = json.loads(res.stdout)
    assert any(f["rule_id"] == "IV000" for f in payload["findings"])


def test_cli_rejects_bad_flags(tmp_path: Path) -> None:
    _write(tmp_path, "greeter.prompt.yml", _CLEAN)
    bad_fmt = runner.invoke(app, ["lint", "greeter.prompt.yml", "--repo", str(tmp_path), "--format", "xml"])
    assert bad_fmt.exit_code != 0
    bad_sev = runner.invoke(app, ["lint", "greeter.prompt.yml", "--repo", str(tmp_path), "--fail-under", "critical"])
    assert bad_sev.exit_code != 0
