"""LLM-as-judge scoring for semantic assertions.

Judging is inherently non-deterministic, so it is strictly opt-in: it only runs
when the caller supplies a judge :class:`~instructvault.providers.Provider`.
The judge reuses the same provider abstraction as output evals, keeping the core
free of any hard LLM-SDK dependency.
"""
from __future__ import annotations

import re

from .providers import Provider
from .spec import JudgeSpec

_JUDGE_SYSTEM = (
    "You are a strict evaluator. Given a RUBRIC and a RESPONSE, score how well "
    "the RESPONSE satisfies the RUBRIC on a scale from 0.0 to 1.0. "
    "Reply with ONLY the number, e.g. 0.8."
)

_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_FRACTION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _parse_score(text: str) -> float:
    """Normalize a judge reply to a 0.0-1.0 score.

    Accepts floats (``0.8``), percentages (``80%``), fractions (``8/10``), and
    bare integers on a 0-10 scale (``8`` -> ``0.8``).
    """
    s = text.strip()

    m = _PERCENT_RE.search(s)
    if m:
        return _clamp(float(m.group(1)) / 100.0)

    m = _FRACTION_RE.search(s)
    if m:
        denominator = float(m.group(2))
        if denominator == 0:
            raise ValueError(f"Judge returned a zero-denominator fraction: {text!r}")
        return _clamp(float(m.group(1)) / denominator)

    m = _NUMBER_RE.search(s)
    if m:
        value = float(m.group(0))
        if value > 1.0:
            # Treat values above 1 as a 0-10 scale (e.g. "8" -> 0.8).
            value = value / 10.0 if value <= 10.0 else 1.0
        return _clamp(value)

    raise ValueError(f"Could not parse a 0.0-1.0 score from judge output: {text!r}")


def judge_output(output: str, judge: JudgeSpec, provider: Provider) -> tuple[bool, float]:
    """Return (passed, score). ``passed`` is ``score >= judge.threshold``."""
    messages = [
        {"role": "system", "content": _JUDGE_SYSTEM},
        {
            "role": "user",
            "content": f"RUBRIC:\n{judge.rubric}\n\nRESPONSE:\n{output}\n\nScore (0.0-1.0):",
        },
    ]
    params: dict[str, object] = {"model": judge.model} if judge.model else {}
    raw = provider(messages, params)
    score = _parse_score(raw)
    return (score >= judge.threshold, score)
