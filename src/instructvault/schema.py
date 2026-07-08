"""JSON Schema generation for prompt specs.

The schema is generated from the Pydantic model so it never drifts from the
runtime validation rules. Editors (e.g. the VS Code YAML extension) can point
at the published schema for autocompletion and inline validation via::

    # yaml-language-server: $schema=https://raw.githubusercontent.com/05satyam/instruct_vault/main/schemas/prompt.schema.json
"""
from __future__ import annotations

from typing import Any, Dict

from .spec import PromptSpec

SCHEMA_ID = "https://raw.githubusercontent.com/05satyam/instruct_vault/main/schemas/prompt.schema.json"


def prompt_json_schema() -> Dict[str, Any]:
    schema = PromptSpec.model_json_schema(by_alias=True)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = SCHEMA_ID
    schema.setdefault("title", "InstructVault Prompt Spec")
    return schema
