from __future__ import annotations

import subprocess
from pathlib import Path

from instructvault import InstructVault, RenderResult


def _init(tmp_path: Path) -> None:
    subprocess.check_call(["git", "-C", str(tmp_path), "init"])
    from typer.testing import CliRunner

    from instructvault.cli import app
    CliRunner().invoke(app, ["init", "--repo", str(tmp_path)])


def test_render_returns_render_result(tmp_path: Path) -> None:
    _init(tmp_path)
    vault = InstructVault(repo_root=tmp_path)
    result = vault.render("prompts/hello_world.prompt.yml", vars={"name": "Ava"})
    assert isinstance(result, RenderResult)
    assert result.prompt_name == "hello_world"


def test_render_result_is_list_backward_compatible(tmp_path: Path) -> None:
    _init(tmp_path)
    vault = InstructVault(repo_root=tmp_path)
    result = vault.render("prompts/hello_world.prompt.yml", vars={"name": "Ava"})
    # existing usage patterns must keep working
    assert isinstance(result, list)
    assert result[0].role == "system"
    assert any("Ava" in m.content for m in result)


def test_to_openai_adapter(tmp_path: Path) -> None:
    _init(tmp_path)
    vault = InstructVault(repo_root=tmp_path)
    result = vault.render("prompts/hello_world.prompt.yml", vars={"name": "Ava"})
    kwargs = result.to_openai()
    assert kwargs["messages"][0]["role"] == "system"
    assert all(set(m) == {"role", "content"} for m in kwargs["messages"])


def test_provider_flows_to_litellm(tmp_path: Path) -> None:
    _init(tmp_path)
    p = tmp_path / "prompts" / "with_provider.prompt.yml"
    p.write_text(
        'spec_version: "1.0"\n'
        "name: with_provider\n"
        "modelParameters: { model: claude-3-5-sonnet, provider: anthropic }\n"
        "variables: { required: [name] }\n"
        'messages:\n  - role: user\n    content: "Hi {{ name }}"\n'
        'tests:\n  - name: t\n    vars: { name: Ava }\n    assert: { contains_any: [Ava] }\n',
        encoding="utf-8",
    )
    vault = InstructVault(repo_root=tmp_path)
    result = vault.render("prompts/with_provider.prompt.yml", vars={"name": "Ava"})
    assert result.provider == "anthropic"
    assert result.to_litellm()["model"] == "anthropic/claude-3-5-sonnet"
