from __future__ import annotations
from typing import Any, Dict, List
import json
import yaml
from .spec import DatasetRow, PromptSpec

def load_prompt_spec(yaml_text: str) -> PromptSpec:
    text = yaml_text.strip()
    if text.startswith("{") or text.startswith("["):
        data: Dict[str, Any] = json.loads(text) if text else {}
    else:
        data = yaml.safe_load(yaml_text) or {}
    return PromptSpec.model_validate(data)

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
