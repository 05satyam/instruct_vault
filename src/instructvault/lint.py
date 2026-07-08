"""Prompt linting: a deterministic quality gate for prompt specs.

Where ``validate`` enforces hard schema correctness, ``lint`` reports *quality
smells* — issues that are worth flagging but are not necessarily fatal. Rules
are small, self-contained, and register in ``_RULES``; each new rule is an
isolated addition, so the finding contract below is intentionally stable.

The output is designed to feed CI: a machine-readable JSON shape, a Markdown
scorecard for job summaries, and severity-based exit gating.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .render import _scan_for_secrets
from .spec import PromptSpec

# Ordering matters for gating and sorting: higher is more severe.
_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}
SEVERITIES = tuple(_SEVERITY_ORDER)
_DOCS_BASE = "https://github.com/05satyam/instruct_vault/blob/main/docs/lint.md"


@dataclass(frozen=True)
class Finding:
    """A single lint result. This shape is a stable contract: JSON output and
    future reporters (e.g. SARIF) depend on it, so fields are additive-only."""

    rule_id: str
    severity: str
    message: str
    prompt_path: str
    location: str | None = None

    @property
    def help_url(self) -> str:
        return f"{_DOCS_BASE}#{self.rule_id.lower()}"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "prompt_path": self.prompt_path,
            "location": self.location,
            "help_url": self.help_url,
        }


class Rule:
    """Base class for lint rules. Subclass, set ``id``/``severity``/``summary``,
    and implement :meth:`check`. Register the instance in ``_RULES``."""

    id: str = ""
    severity: str = "warning"
    summary: str = ""

    def check(self, spec: PromptSpec, path: str) -> list[Finding]:  # pragma: no cover
        raise NotImplementedError

    def finding(self, message: str, path: str, location: str | None = None) -> Finding:
        return Finding(self.id, self.severity, message, path, location)


class SecretInTemplate(Rule):
    id = "IV001"
    severity = "error"
    summary = "A hardcoded secret was detected in the prompt template text."

    def check(self, spec: PromptSpec, path: str) -> list[Finding]:
        out: list[Finding] = []
        for msg in spec.messages:
            hits = _scan_for_secrets(msg.content)
            if hits:
                out.append(
                    self.finding(
                        f"Potential hardcoded secret ({', '.join(sorted(set(hits)))}) "
                        f"in {msg.role} message; move it to a variable or secret store",
                        path,
                        location=msg.role,
                    )
                )
        return out


class MissingDescription(Rule):
    id = "IV002"
    severity = "warning"
    summary = "The prompt has no description, hurting discoverability and ownership."

    def check(self, spec: PromptSpec, path: str) -> list[Finding]:
        if not (spec.description and spec.description.strip()):
            return [
                self.finding(
                    "Prompt has no description; add one so reviewers and consumers "
                    "know its purpose",
                    path,
                )
            ]
        return []


_RULES: list[Rule] = [SecretInTemplate(), MissingDescription()]


def all_rules() -> list[Rule]:
    return list(_RULES)


def run_lint(
    items: Iterable[tuple[str, PromptSpec]], rules: list[Rule] | None = None
) -> list[Finding]:
    """Run ``rules`` over ``(path, spec)`` pairs and return sorted findings."""
    active = rules if rules is not None else _RULES
    findings: list[Finding] = []
    for path, spec in items:
        for rule in active:
            findings.extend(rule.check(spec, path))
    return sorted(
        findings,
        key=lambda f: (f.prompt_path, -_SEVERITY_ORDER[f.severity], f.rule_id),
    )


def count_by_severity(findings: Iterable[Finding]) -> dict[str, int]:
    counts = {sev: 0 for sev in SEVERITIES}
    for f in findings:
        counts[f.severity] += 1
    return counts


def gate(findings: Iterable[Finding], fail_under: str | None) -> bool:
    """Return True if the run passes. ``fail_under`` is the minimum severity that
    should fail the build (``error``/``warning``/``info``); ``None`` never fails."""
    if not fail_under:
        return True
    threshold = _SEVERITY_ORDER[fail_under]
    return not any(_SEVERITY_ORDER[f.severity] >= threshold for f in findings)


def to_markdown(findings: list[Finding], *, title: str = "InstructVault Prompt Lint") -> str:
    """Render a scorecard suitable for a GitHub Actions job summary."""
    counts = count_by_severity(findings)
    header = f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['info']} info"
    lines = [f"## {title}", "", f"**{header}**"]
    if not findings:
        lines.append("")
        lines.append("No findings.")
        return "\n".join(lines) + "\n"
    lines += ["", "| Severity | Rule | Prompt | Message |", "| --- | --- | --- | --- |"]
    for f in findings:
        loc = f" ({f.location})" if f.location else ""
        lines.append(
            f"| {f.severity} | [{f.rule_id}]({f.help_url}) "
            f"| `{f.prompt_path}`{loc} | {f.message} |"
        )
    return "\n".join(lines) + "\n"
