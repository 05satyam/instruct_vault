from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

Role = Literal["system", "user", "assistant", "tool"]

class PromptMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
    content: str

class VariableSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    required: List[str] = Field(default_factory=list)
    optional: List[str] = Field(default_factory=list)

class ModelDefaults(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

class JudgeSpec(BaseModel):
    """LLM-as-judge assertion. Opt-in and only evaluated when a judge provider
    is supplied; otherwise the check is skipped so default CI stays deterministic."""
    model_config = ConfigDict(extra="forbid")
    rubric: str
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model: Optional[str] = None


class AssertSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contains_any: Optional[List[str]] = None
    contains_all: Optional[List[str]] = None
    not_contains: Optional[List[str]] = None
    matches: Optional[List[str]] = None
    not_matches: Optional[List[str]] = None
    json_schema: Optional[Dict[str, Any]] = None
    judge: Optional[JudgeSpec] = None

    def has_deterministic(self) -> bool:
        return bool(
            self.contains_any or self.contains_all or self.not_contains
            or self.matches or self.not_matches or self.json_schema
        )

    @model_validator(mode="after")
    def _require_one(self) -> "AssertSpec":
        if not (self.has_deterministic() or self.judge):
            raise ValueError(
                "assert must include at least one of contains_any, contains_all, "
                "not_contains, matches, not_matches, json_schema, judge"
            )
        return self

class PromptTest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    vars: Dict[str, Any] = Field(default_factory=dict)
    assert_: AssertSpec = Field(alias="assert")

class PromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    spec_version: str = Field(default="1.0", alias="spec_version")
    name: str
    description: Optional[str] = None
    model_defaults: ModelDefaults = Field(default_factory=ModelDefaults, alias="modelParameters")
    variables: VariableSpec = Field(default_factory=VariableSpec)
    messages: List[PromptMessage]
    tests: List[PromptTest] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_tests(self, info: ValidationInfo) -> "PromptSpec":
        context = info.context or {}
        allow_no_tests = bool(context.get("allow_no_tests"))
        if not self.tests and not allow_no_tests:
            raise ValueError("prompt must include at least one test")
        return self

class DatasetRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vars: Dict[str, Any] = Field(default_factory=dict)
    assert_: AssertSpec = Field(alias="assert")
