from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from instructvault.scaffold import init_repo
_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(_ROOT / "playground"))
from ivault_playground.app import app  # type: ignore  # noqa: E402

def _setup_repo(tmp_path: Path) -> Path:
    _git_init(tmp_path)
    init_repo(tmp_path)
    return tmp_path

def _git_init(repo: Path) -> None:
    subprocess.check_call(["git", "-C", str(repo), "init"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "test@example.com"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "Test User"])

def test_playground_health(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    os.environ["IVAULT_REPO_ROOT"] = str(repo)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_playground_prompts_and_prompt(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    os.environ["IVAULT_REPO_ROOT"] = str(repo)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/prompts")
    assert res.status_code == 200
    data = res.json()
    assert any(p.endswith("hello_world.prompt.yml") for p in data)
    res2 = client.get("/prompt", params={"prompt_path": "prompts/hello_world.prompt.yml"})
    assert res2.status_code == 200
    assert res2.json()["name"] == "hello_world"

def test_playground_render(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    os.environ["IVAULT_REPO_ROOT"] = str(repo)
    client = TestClient(app, raise_server_exceptions=False)
    payload = {"prompt_path": "prompts/hello_world.prompt.yml", "vars": {"name": "Ava"}}
    res = client.post("/render", json=payload)
    assert res.status_code == 200
    assert any("Ava" in m["content"] for m in res.json())

def test_playground_prompts_and_prompt_by_ref(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    os.environ["IVAULT_REPO_ROOT"] = str(repo)
    subprocess.check_call(["git", "-C", str(repo), "add", "prompts", ".github"])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-m", "init prompts"])
    subprocess.check_call(["git", "-C", str(repo), "tag", "prompts/v1.0.0"])
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/prompts", params={"ref": "prompts/v1.0.0"})
    assert res.status_code == 200
    data = res.json()
    assert any(p.endswith("hello_world.prompt.yml") for p in data)
    res2 = client.get("/prompt", params={"prompt_path": "prompts/hello_world.prompt.yml", "ref": "prompts/v1.0.0"})
    assert res2.status_code == 200
    assert res2.json()["name"] == "hello_world"

def test_playground_render_missing_vars(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    os.environ["IVAULT_REPO_ROOT"] = str(repo)
    client = TestClient(app, raise_server_exceptions=False)
    payload = {"prompt_path": "prompts/hello_world.prompt.yml", "vars": {}}
    res = client.post("/render", json=payload)
    assert res.status_code == 500

def test_playground_refs_empty(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    os.environ["IVAULT_REPO_ROOT"] = str(repo)
    client = TestClient(app)
    res = client.get("/refs")
    assert res.status_code == 200
    assert res.json() == []
