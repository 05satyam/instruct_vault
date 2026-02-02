from __future__ import annotations
import json
import subprocess
import shutil
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
    p.write_text('{"spec_version":"1.0","name":"json_example","variables":{"required":["name"]},"messages":[{"role":"system","content":"Hi"},{"role":"user","content":"Hello {{ name }}"}],"tests":[{"name":"includes_name","vars":{"name":"Ava"},"assert":{"contains_any":["Ava"]}}]}', encoding="utf-8")
    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path), "--json"])
    assert res.exit_code == 0

def test_validate_requires_assert(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    p = tmp_path / "prompts" / "bad.prompt.yml"
    p.write_text(
        "spec_version: \"1.0\"\n"
        "name: bad\n"
        "variables:\n  required: [name]\n"
        "messages:\n  - role: system\n    content: \"Hi\"\n"
        "tests:\n  - name: missing_assert\n    vars: { name: \"Ava\" }\n",
        encoding="utf-8",
    )
    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path)])
    assert res.exit_code != 0

def test_bundle_empty_dir_fails(tmp_path: Path) -> None:
    _git_init(tmp_path)
    empty_dir = tmp_path / "no_prompts"
    empty_dir.mkdir()
    res = runner.invoke(app, ["bundle", "--repo", str(tmp_path), "--prompts", str(empty_dir), "--out", str(tmp_path / "out.json")])
    assert res.exit_code != 0

def test_validate_requires_tests(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    p = tmp_path / "prompts" / "no_tests.prompt.yml"
    p.write_text(
        "spec_version: \"1.0\"\n"
        "name: no_tests\n"
        "variables:\n  required: [name]\n"
        "messages:\n  - role: system\n    content: \"Hi\"\n",
        encoding="utf-8",
    )
    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path)])
    assert res.exit_code != 0

def test_render_invalid_vars_json(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"
    res = runner.invoke(app, ["render", prompt_rel, "--repo", str(tmp_path), "--vars", "{bad}"])
    assert res.exit_code != 0

def test_bundle_ref_without_prompts_fails(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    subprocess.check_call(["git", "-C", str(tmp_path), "add", "prompts", ".github"])
    subprocess.check_call(["git", "-C", str(tmp_path), "commit", "-m", "init prompts"])
    subprocess.check_call(["git", "-C", str(tmp_path), "tag", "prompts/v1.0.0"])
    shutil.rmtree(tmp_path / "prompts")
    subprocess.check_call(["git", "-C", str(tmp_path), "add", "-u"])
    subprocess.check_call(["git", "-C", str(tmp_path), "commit", "-m", "remove prompts"])
    res = runner.invoke(app, ["bundle", "--repo", str(tmp_path), "--ref", "HEAD", "--out", str(tmp_path / "out.json")])
    assert res.exit_code != 0

def test_yaml_flow_mapping_parses(tmp_path: Path) -> None:
    _git_init(tmp_path)
    p = tmp_path / "prompts"
    p.mkdir()
    flow = '{spec_version: "1.0", name: flow, variables: {required: [name]}, messages: [{role: system, content: "Hi"}], tests: [{name: t, vars: {name: Ava}, assert: {contains_any: [Ava]}}]}'
    (p / "flow.prompt.yml").write_text(flow, encoding="utf-8")
    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path)])
    assert res.exit_code == 0

def test_bundle_ref_param_with_bundle_path_errors(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    out_bundle = tmp_path / "out" / "ivault.bundle.json"
    runner.invoke(app, ["bundle", "--repo", str(tmp_path), "--out", str(out_bundle)])
    from instructvault import InstructVault
    vault = InstructVault(bundle_path=out_bundle)
    try:
        vault.render("prompts/hello_world.prompt.yml", vars={"name": "Ava"}, ref="prompts/v1.0.0")
        assert False, "expected error"
    except Exception:
        assert True

def test_render_strict_vars_blocks_extra(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"
    res = runner.invoke(app, ["render", prompt_rel, "--repo", str(tmp_path), "--vars", '{"name":"Ava","extra":"x"}', "--strict-vars"])
    assert res.exit_code != 0

def test_render_safe_blocks_secret(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"
    res = runner.invoke(app, ["render", prompt_rel, "--repo", str(tmp_path), "--vars", '{"name":"sk-abc12345678901234567890"}', "--safe"])
    assert res.exit_code != 0

def test_render_safe_redact_allows(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    prompt_rel = "prompts/hello_world.prompt.yml"
    res = runner.invoke(app, ["render", prompt_rel, "--repo", str(tmp_path), "--vars", '{"name":"sk-abc12345678901234567890"}', "--safe", "--redact"])
    assert res.exit_code == 0

def test_validate_policy_hook(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runner.invoke(app, ["init", "--repo", str(tmp_path)])
    policy = tmp_path / "policy.py"
    policy.write_text(
        "def check_spec(spec):\n"
        "    if spec.get('name') == 'hello_world':\n"
        "        return ['blocked name']\n"
        "    return []\n"
    )
    res = runner.invoke(app, ["validate", "prompts", "--repo", str(tmp_path), "--policy", str(policy)])
    assert res.exit_code != 0
