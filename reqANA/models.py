from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IntakeSource(StrEnum):
    TEXT = "text"
    FILE = "file"
    VOICE = "voice"
    VOICERUN = "voicerun"


class RequirementInput(BaseModel):
    source: IntakeSource
    content: str = Field(min_length=1)
    filename: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequirementDocument(BaseModel):
    title: str
    executive_summary: str
    background: str
    objectives: list[str]
    stakeholders: list[str]
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    assumptions: list[str]
    constraints: list[str]
    risks: list[str]
    open_questions: list[str]
    success_metrics: list[str]
    next_steps: list[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FunctionModule(BaseModel):
    id: int
    name: str
    description: str
    input: str
    output: str
    priority: str
    complexity: str
    approach: str


class FunctionDecompositionRequest(BaseModel):
    clarified_problem: str
    scope: str
    assumptions: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    requirement_document: RequirementDocument | None = None


class FunctionDecompositionResponse(BaseModel):
    modules: list[FunctionModule]
    critical_path: list[str] = Field(default_factory=list)
