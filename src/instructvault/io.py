from __future__ import annotations
from typing import Any, Dict, List
import json
import yaml
from .spec import DatasetRow, PromptSpec

def load_prompt_spec(yaml_text: str, *, allow_no_tests: bool = True) -> PromptSpec:
    text = yaml_text.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            data: Dict[str, Any] = json.loads(text) if text else {}
        except Exception:
            data = yaml.safe_load(yaml_text) or {}
    else:
        data = yaml.safe_load(yaml_text) or {}
    return PromptSpec.model_validate(data, context={"allow_no_tests": allow_no_tests})

def load_prompt_dict(text: str) -> Dict[str, Any]:
    raw = text.strip()
    if raw.startswith("{") or raw.startswith("["):
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return yaml.safe_load(text) or {}
    return yaml.safe_load(text) or {}

def load_dataset_jsonl(text: str) -> List[DatasetRow]:
    rows: List[DatasetRow] = []
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception as e:
            raise ValueError(f"Invalid JSON on line {i}: {e}") from e
        rows.append(DatasetRow.model_validate(obj))
    return rows
