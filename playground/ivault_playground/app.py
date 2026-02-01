from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from instructvault import InstructVault
from instructvault.io import load_prompt_spec

app = FastAPI(title="ivault-playground", version="0.1.0")

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

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>InstructVault Playground</title>
    <style>
      :root {
        --bg: #0f172a;
        --panel: #111827;
        --muted: #94a3b8;
        --text: #e2e8f0;
        --accent: #22c55e;
        --line: #1f2937;
      }
      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        background: radial-gradient(1200px 600px at 10% -10%, #1e293b, #0f172a);
        color: var(--text);
      }
      .wrap { max-width: 980px; margin: 48px auto; padding: 0 24px; }
      .hero {
        background: linear-gradient(140deg, #0b1220, #111827);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
      }
      h1 { margin: 0 0 8px 0; font-size: 32px; letter-spacing: 0.3px; }
      .sub { color: var(--muted); margin: 0 0 24px 0; }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      .card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 16px;
      }
      .card h3 { margin: 0 0 8px 0; font-size: 16px; }
      .card p { margin: 0; color: var(--muted); font-size: 14px; }
      .links a {
        display: inline-block;
        margin-right: 12px;
        color: var(--text);
        text-decoration: none;
        border-bottom: 1px solid transparent;
      }
      .links a:hover { border-bottom-color: var(--accent); }
      .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(34,197,94,0.15);
        color: #86efac;
        font-size: 12px;
        margin-left: 8px;
      }
      footer { margin-top: 24px; color: var(--muted); font-size: 12px; }
      @media (max-width: 640px) {
        .wrap { margin: 24px auto; }
        h1 { font-size: 26px; }
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="hero">
        <h1>InstructVault Playground <span class="badge">Individual & Enterprise</span></h1>
        <p class="sub">Prompts as code with deterministic evals and Git-native deployments.</p>
        <div class="links">
          <a href="/docs">API Docs</a>
          <a href="/health">Health</a>
          <a href="/prompts">List Prompts</a>
        </div>
      </div>
      <div class="grid" style="margin-top: 20px;">
        <div class="card">
          <h3>Fast, Local Runtime</h3>
          <p>No network calls during inference. Prompts are loaded locally or from a bundle.</p>
        </div>
        <div class="card">
          <h3>Governed Changes</h3>
          <p>Prompts are versioned in Git and changes flow through PRs and CI.</p>
        </div>
        <div class="card">
          <h3>Deterministic Evals</h3>
          <p>Tests live alongside prompts and run consistently in CI and locally.</p>
        </div>
        <div class="card">
          <h3>Enterprise & OSS</h3>
          <p>Works for single devs and org-scale teams with the same workflow.</p>
        </div>
      </div>
      <footer>InstructVault Playground is an optional companion to the core OSS library.</footer>
    </div>
  </body>
</html>"""

@app.get("/prompts")
def list_prompts() -> List[str]:
    repo = _repo_root()
    prompts_dir = repo / "prompts"
    if not prompts_dir.exists():
        return []
    files = sorted(prompts_dir.rglob("*.prompt.y*ml")) + sorted(prompts_dir.rglob("*.prompt.json"))
    return [p.relative_to(repo).as_posix() for p in files]

@app.get("/prompt")
def get_prompt(prompt_path: str) -> Dict[str, Any]:
    repo = _repo_root()
    p = repo / prompt_path
    if not p.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    spec = load_prompt_spec(p.read_text(encoding="utf-8"))
    return spec.model_dump(by_alias=True)

@app.post("/render")
def render(req: RenderRequest) -> List[Dict[str, str]]:
    repo = _repo_root()
    vault = InstructVault(repo_root=repo)
    msgs = vault.render(req.prompt_path, vars=req.vars, ref=req.ref)
    return [{"role": m.role, "content": m.content} for m in msgs]

@app.post("/eval")
def eval_prompt(req: EvalRequest) -> Dict[str, Any]:
    repo = _repo_root()
    from instructvault.eval import run_dataset, run_inline_tests
    from instructvault.io import load_dataset_jsonl
    from instructvault.store import PromptStore

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
