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

_SCORE_RE = re.compile(r"(?:0(?:\.\d+)?|1(?:\.0+)?|\.\d+)")
_FRACTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*/\s*10\s*$")
_PERCENT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")


def _parse_score(text: str) -> float:
    text = text.strip()

    # Handle "8/10"
    match = _FRACTION_RE.match(text)
    if match:
        score = float(match.group(1)) / 10
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Could not parse a 0.0-1.0 score from judge output: {text!r}"
            )
        return score

    # Handle "80%"
    match = _PERCENT_RE.match(text)
    if match:
        score = float(match.group(1)) / 100
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Could not parse a 0.0-1.0 score from judge output: {text!r}"
            )
        return score

    # Existing float parsing
    match = _SCORE_RE.search(text)
    if match:
        score = float(match.group(0))
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Could not parse a 0.0-1.0 score from judge output: {text!r}"
            )
        return score

    raise ValueError(
        f"Could not parse a 0.0-1.0 score from judge output: {text!r}"
)
    

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
