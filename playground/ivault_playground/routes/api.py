from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from instructvault import InstructVault
from instructvault.io import load_prompt_spec, load_dataset_jsonl
from instructvault.store import PromptStore
from instructvault.eval import run_dataset, run_inline_tests

router = APIRouter()

class RenderRequest(BaseModel):
    prompt_path: str
    vars: Dict[str, Any]
    ref: Optional[str] = None

class EvalRequest(BaseModel):
    prompt_path: str
    dataset_path: Optional[str] = None
    ref: Optional[str] = None

def _repo_root() -> Path:
    return Path(os.getenv("IVAULT_REPO_ROOT", ".")).resolve()

@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@router.get("/prompts")
def list_prompts(ref: Optional[str] = None) -> List[str]:
    repo = _repo_root()
    prompts_dir = repo / "prompts"
    if ref:
        cmd = ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref, "prompts"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return []
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return [p for p in files if p.endswith((".prompt.yml", ".prompt.yaml", ".prompt.json"))]
    if not prompts_dir.exists():
        return []
    files = sorted(prompts_dir.rglob("*.prompt.y*ml")) + sorted(prompts_dir.rglob("*.prompt.json"))
    return [p.relative_to(repo).as_posix() for p in files]

@router.get("/refs")
def list_refs() -> List[str]:
    repo = _repo_root()
    cmd = ["git", "-C", str(repo), "tag", "--list", "prompts/*"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return []
    return [r.strip() for r in res.stdout.splitlines() if r.strip()]

@router.get("/prompt")
def get_prompt(prompt_path: str, ref: Optional[str] = None) -> Dict[str, Any]:
    repo = _repo_root()
    if ref:
        store = PromptStore(repo)
        try:
            spec = load_prompt_spec(store.read_text(prompt_path, ref=ref))
        except Exception:
            raise HTTPException(status_code=404, detail="Prompt not found at ref")
    else:
        p = repo / prompt_path
        if not p.exists():
            raise HTTPException(status_code=404, detail="Prompt not found")
        spec = load_prompt_spec(p.read_text(encoding="utf-8"))
    return spec.model_dump(by_alias=True)

@router.post("/render")
def render(req: RenderRequest) -> List[Dict[str, str]]:
    repo = _repo_root()
    vault = InstructVault(repo_root=repo)
    msgs = vault.render(req.prompt_path, vars=req.vars, ref=req.ref)
    return [{"role": m.role, "content": m.content} for m in msgs]

@router.post("/eval")
def eval_prompt(req: EvalRequest) -> Dict[str, Any]:
    repo = _repo_root()
    store = PromptStore(repo)
    spec = load_prompt_spec(store.read_text(req.prompt_path, ref=req.ref))

    ok1, r1 = run_inline_tests(spec)
    results = list(r1)
    ok = ok1

    if req.dataset_path:
        rows = load_dataset_jsonl((repo / req.dataset_path).read_text(encoding="utf-8"))
        ok2, r2 = run_dataset(spec, rows)
        ok = ok and ok2
        results.extend(r2)

    return {
        "prompt": spec.name,
        "ref": req.ref or "WORKTREE",
        "pass": ok,
        "results": [{"test": r.name, "pass": r.passed, "error": r.error} for r in results],
    }
