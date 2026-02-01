from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

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
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

class AssertSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contains_any: Optional[List[str]] = None
    contains_all: Optional[List[str]] = None
    not_contains: Optional[List[str]] = None

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

class DatasetRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vars: Dict[str, Any] = Field(default_factory=dict)
    assert_: AssertSpec = Field(alias="assert")
