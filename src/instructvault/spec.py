from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

Role = Literal["system", "user", "assistant", "tool"]

class PromptMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
    content: str

class VariableSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    required: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)

class ModelDefaults(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str | None = None
    provider: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None

class JudgeSpec(BaseModel):
    """LLM-as-judge assertion. Opt-in and only evaluated when a judge provider
    is supplied; otherwise the check is skipped so default CI stays deterministic."""
    model_config = ConfigDict(extra="forbid")
    rubric: str
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model: str | None = None


class AssertSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contains_any: list[str] | None = None
    contains_all: list[str] | None = None
    not_contains: list[str] | None = None
    matches: list[str] | None = None
    not_matches: list[str] | None = None
    json_schema: dict[str, Any] | None = None
    judge: JudgeSpec | None = None

    def has_deterministic(self) -> bool:
        return bool(
            self.contains_any or self.contains_all or self.not_contains
            or self.matches or self.not_matches or self.json_schema
        )

    @model_validator(mode="after")
    def _require_one(self) -> AssertSpec:
        if not (self.has_deterministic() or self.judge):
            raise ValueError(
                "assert must include at least one of contains_any, contains_all, "
                "not_contains, matches, not_matches, json_schema, judge"
            )
        return self

class PromptTest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    vars: dict[str, Any] = Field(default_factory=dict)
    assert_: AssertSpec = Field(alias="assert")

class PromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    spec_version: str = Field(default="1.0", alias="spec_version")
    name: str
    description: str | None = None
    model_defaults: ModelDefaults = Field(default_factory=ModelDefaults, alias="modelParameters")
    variables: VariableSpec = Field(default_factory=VariableSpec)
    messages: list[PromptMessage]
    tests: list[PromptTest] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_tests(self, info: ValidationInfo) -> PromptSpec:
        context = info.context or {}
        allow_no_tests = bool(context.get("allow_no_tests"))
        if not self.tests and not allow_no_tests:
            raise ValueError("prompt must include at least one test")
        return self

class DatasetRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vars: dict[str, Any] = Field(default_factory=dict)
    assert_: AssertSpec = Field(alias="assert")
