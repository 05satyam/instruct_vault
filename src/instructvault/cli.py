from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import typer
from rich import print as rprint

from .bundle import write_bundle
from .diff import unified_diff
from .eval import run_dataset, run_inline_tests
from .io import load_dataset_jsonl, load_prompt_spec, load_prompt_dict
from .policy import load_policy_module, run_spec_policy
from .junit import write_junit_xml
import yaml
from .render import check_required_vars, render_messages
from .scaffold import init_repo
from .store import PromptStore

app = typer.Typer(help="InstructVault: git-first prompt registry + CI evals + runtime SDK")

def _gather_prompt_files(base: Path) -> list[Path]:
    if base.is_file():
        return [base]
    files = sorted(base.rglob("*.prompt.y*ml")) + sorted(base.rglob("*.prompt.json"))
    return files

@app.command()
def init(repo: Path = typer.Option(Path("."), "--repo")):
    init_repo(repo)
    rprint("[green]Initialized prompts/, datasets/, and .github/workflows/ivault.yml[/green]")

@app.command()
def validate(path: Path = typer.Argument(...),
             repo: Path = typer.Option(Path("."), "--repo"),
             json_out: bool = typer.Option(False, "--json"),
             policy: Optional[str] = typer.Option(None, "--policy")):
    base = path if path.is_absolute() else repo / path
    files = _gather_prompt_files(base)
    if not files:
        raise typer.BadParameter("No prompt files found")
    ok = True
    results = []
    pol = load_policy_module(policy)
    for f in files:
        try:
            spec = load_prompt_spec(f.read_text(encoding="utf-8"), allow_no_tests=False)
            errors = run_spec_policy(pol, load_prompt_dict(f.read_text(encoding="utf-8")))
            if errors:
                ok = False
                results.append({"path": str(f), "ok": False, "error": "; ".join(errors)})
                if not json_out:
                    rprint(f"[red]FAIL[/red] {f}  {errors}")
                continue
            try:
                rel_path = f.relative_to(repo).as_posix()
            except ValueError:
                rel_path = str(f)
            results.append({"path": rel_path, "ok": True, "name": spec.name})
            if not json_out:
                rprint(f"[green]OK[/green] {rel_path}  ({spec.name})")
        except Exception as e:
            ok = False
            try:
                rel_path = f.relative_to(repo).as_posix()
            except ValueError:
                rel_path = str(f)
            results.append({"path": rel_path, "ok": False, "error": str(e)})
            if not json_out:
                rprint(f"[red]FAIL[/red] {rel_path}  {e}")
    if json_out:
        rprint(json.dumps({"ok": ok, "results": results}))
    raise typer.Exit(code=0 if ok else 1)

@app.command()
def render(prompt_path: str = typer.Argument(...),
           vars_json: str = typer.Option("{}", "--vars"),
           ref: Optional[str] = typer.Option(None, "--ref"),
           repo: Path = typer.Option(Path("."), "--repo"),
           json_out: bool = typer.Option(False, "--json"),
           allow_no_tests: bool = typer.Option(False, "--allow-no-tests"),
           safe: bool = typer.Option(False, "--safe"),
           strict_vars: bool = typer.Option(False, "--strict-vars"),
           redact: bool = typer.Option(False, "--redact")):
    store = PromptStore(repo_root=repo)
    spec = load_prompt_spec(store.read_text(prompt_path, ref=ref), allow_no_tests=allow_no_tests)
    try:
        vars_dict = json.loads(vars_json)
    except Exception:
        raise typer.BadParameter("Invalid JSON for --vars")
    check_required_vars(spec, vars_dict, safe=safe, strict_vars=strict_vars, redact=redact)
    msgs = render_messages(spec, vars_dict, safe=safe, strict_vars=strict_vars, redact=redact)
    if json_out:
        rprint(json.dumps([{"role": m.role, "content": m.content} for m in msgs]))
    else:
        for m in msgs:
            rprint(f"[bold]{m.role}[/bold]\n{m.content}\n")

@app.command()
def diff(prompt_path: str = typer.Argument(...),
         ref1: str = typer.Option(..., "--ref1"),
         ref2: str = typer.Option(..., "--ref2"),
         repo: Path = typer.Option(Path("."), "--repo"),
         json_out: bool = typer.Option(False, "--json")):
    store = PromptStore(repo_root=repo)
    a = store.read_text(prompt_path, ref=ref1)
    b = store.read_text(prompt_path, ref=ref2)
    d = unified_diff(a, b, f"{ref1}:{prompt_path}", f"{ref2}:{prompt_path}")
    if json_out:
        rprint(json.dumps({"same": not d.strip(), "diff": d}))
    else:
        rprint(d if d.strip() else "[yellow]No differences[/yellow]")

@app.command()
def resolve(ref: str = typer.Argument(...),
            repo: Path = typer.Option(Path("."), "--repo"),
            json_out: bool = typer.Option(False, "--json")):
    store = PromptStore(repo_root=repo)
    sha = store.resolve_ref(ref)
    if json_out:
        rprint(json.dumps({"ref": ref, "sha": sha}))
    else:
        rprint(sha)

@app.command()
def migrate(path: Path = typer.Argument(...),
            repo: Path = typer.Option(Path("."), "--repo"),
            apply: bool = typer.Option(False, "--apply")):
    base = path if path.is_absolute() else repo / path
    files = _gather_prompt_files(base)
    if not files:
        raise typer.BadParameter("No prompt files found")
    needs = []
    for f in files:
        data = load_prompt_dict(f.read_text(encoding="utf-8"))
        if "spec_version" not in data:
            needs.append(f)
    if not needs:
        rprint("[green]No migration needed[/green]")
        raise typer.Exit(code=0)
    for f in needs:
        if apply:
            data = load_prompt_dict(f.read_text(encoding="utf-8"))
            data["spec_version"] = "1.0"
            f.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            rprint(f"[green]Updated:[/green] {f}")
        else:
            rprint(f"[yellow]Missing spec_version:[/yellow] {f}")
    raise typer.Exit(code=0 if apply else 1)

@app.command()
def bundle(prompts: Path = typer.Option(Path("prompts"), "--prompts"),
           out: Path = typer.Option(Path("out/ivault.bundle.json"), "--out"),
           ref: Optional[str] = typer.Option(None, "--ref"),
           repo: Path = typer.Option(Path("."), "--repo")):
    prompts_dir = prompts if prompts.is_absolute() else repo / prompts
    write_bundle(out, repo_root=repo, prompts_dir=prompts_dir, ref=ref)
    rprint(f"[green]Wrote bundle[/green] {out}")

@app.command()
def eval(prompt_path: str = typer.Argument(...),
         ref: Optional[str] = typer.Option(None, "--ref"),
         dataset: Optional[Path] = typer.Option(None, "--dataset"),
         report: Optional[Path] = typer.Option(None, "--report"),
         junit: Optional[Path] = typer.Option(None, "--junit"),
         repo: Path = typer.Option(Path("."), "--repo"),
         json_out: bool = typer.Option(False, "--json"),
         safe: bool = typer.Option(False, "--safe"),
         strict_vars: bool = typer.Option(False, "--strict-vars"),
         redact: bool = typer.Option(False, "--redact"),
         policy: Optional[str] = typer.Option(None, "--policy")):
    store = PromptStore(repo_root=repo)
    spec = load_prompt_spec(store.read_text(prompt_path, ref=ref), allow_no_tests=False)
    pol = load_policy_module(policy)

    ok1, r1 = run_inline_tests(spec, safe=safe, strict_vars=strict_vars, redact=redact, policy=pol)
    results = list(r1)
    ok = ok1

    if dataset is not None:
        rows = load_dataset_jsonl(dataset.read_text(encoding="utf-8"))
        ok2, r2 = run_dataset(spec, rows, safe=safe, strict_vars=strict_vars, redact=redact, policy=pol)
        ok = ok and ok2
        results.extend(r2)

    payload = {
        "prompt": spec.name,
        "ref": ref or "WORKTREE",
        "pass": ok,
        "results": [{"test": r.name, "pass": r.passed, "error": r.error} for r in results],
    }
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if junit:
        junit.parent.mkdir(parents=True, exist_ok=True)
        write_junit_xml(suite_name=f"ivault:{spec.name}", results=results, out_path=str(junit))

    if json_out:
        rprint(json.dumps(payload))
    else:
        for r in results:
            if r.passed:
                rprint(f"[green]PASS[/green] {r.name}")
            else:
                rprint(f"[red]FAIL[/red] {r.name}  {r.error or ''}")
    raise typer.Exit(code=0 if ok else 1)
