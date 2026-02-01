from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from instructvault.cli import app

runner = CliRunner()

def _git_init(repo: Path) -> None:
    subprocess.check_call(["git", "-C", str(repo), "init"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "test@example.com"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "Test User"])

def test_init_scaffolds(tmp_path: Path) -> None:
    _git_init(tmp_path)
    res = runner.invoke(app, ["init", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "prompts" / "hello_world.prompt.yml").exists()
    assert (tmp_path / ".github" / "workflows" / "ivault.yml").exists()

def test_validate_render_eval(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"

    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path)])
    assert res.exit_code == 0

    res = runner.invoke(app, ["render", prompt_rel, "--repo", str(tmp_path), "--vars", '{"name":"Ava"}'])
    assert res.exit_code == 0
    assert "Ava" in res.stdout

    out_report = tmp_path / "out" / "report.json"
    res = runner.invoke(app, ["eval", prompt_rel, "--repo", str(tmp_path), "--report", str(out_report)])
    assert res.exit_code == 0
    payload = json.loads(out_report.read_text())
    assert payload["pass"] is True

def test_git_ref_diff_and_resolve(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"

    subprocess.check_call(["git", "-C", str(tmp_path), "add", "prompts", ".github"])
    subprocess.check_call(["git", "-C", str(tmp_path), "commit", "-m", "init prompts"])
    subprocess.check_call(["git", "-C", str(tmp_path), "tag", "prompts/v1.0.0"])

    p = tmp_path / prompt_rel
    p.write_text(p.read_text().replace("Say hello to {{ name }}.", "Say hello (hi) to {{ name }}."), encoding="utf-8")
    subprocess.check_call(["git", "-C", str(tmp_path), "add", prompt_rel])
    subprocess.check_call(["git", "-C", str(tmp_path), "commit", "-m", "edit prompt"])

    res = runner.invoke(app, ["resolve", "prompts/v1.0.0", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert len(res.stdout.strip()) >= 7

    res = runner.invoke(app, ["diff", prompt_rel, "--ref1", "prompts/v1.0.0", "--ref2", "HEAD", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert "---" in res.stdout or "+++" in res.stdout

def test_bundle_and_json_outputs(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"

    out_bundle = tmp_path / "out" / "ivault.bundle.json"
    res = runner.invoke(app, ["bundle", "--repo", str(tmp_path), "--out", str(out_bundle)])
    assert res.exit_code == 0
    payload = json.loads(out_bundle.read_text())
    assert payload["bundle_version"] == "1.0"
    assert any(p["path"] == prompt_rel for p in payload["prompts"])

    res = runner.invoke(app, ["render", prompt_rel, "--repo", str(tmp_path), "--vars", '{"name":"Ava"}', "--json"])
    assert res.exit_code == 0
    msgs = json.loads(res.stdout)
    assert msgs[0]["role"] == "system"

def test_json_prompt_file(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    p = tmp_path / "prompts" / "json_example.prompt.json"
    p.write_text('{"spec_version":"1.0","name":"json_example","variables":{"required":["name"]},"messages":[{"role":"system","content":"Hi"},{"role":"user","content":"Hello {{ name }}"}]}', encoding="utf-8")
    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path), "--json"])
    assert res.exit_code == 0
