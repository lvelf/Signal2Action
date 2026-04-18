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


class Recommendation(BaseModel):
    title: str
    rationale: str
    priority: str


class Tradeoff(BaseModel):
    option: str
    upside: str
    downside: str
    recommendation_bias: str


class ActionItem(BaseModel):
    phase: str
    timeline: str
    owner: str
    action: str
    outcome: str


class SuccessMetric(BaseModel):
    name: str
    target: str
    timeframe: str


class DeliveryPlan(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    tradeoffs: list[Tradeoff]
    action_plan: list[ActionItem]
    success_metrics: list[SuccessMetric]


class DeliverySlide(BaseModel):
    type: str
    tag: str = ""
    title: str
    subtitle: str | None = None
    bullets: list[str] = Field(default_factory=list)
    modules: list[dict[str, Any]] = Field(default_factory=list)
    timeline: dict[str, list[str]] = Field(default_factory=dict)


class DeliverySummaryCard(BaseModel):
    headline: str
    scope: str
    modules: list[str] = Field(default_factory=list)
    key_actions: list[str] = Field(default_factory=list)
    timeline: str = "30-60-90 day execution path"


class DeliveryGenerateRequest(BaseModel):
    analysis: dict[str, Any] = Field(default_factory=dict)
    requirement_document: RequirementDocument | None = None
    functions: FunctionDecompositionResponse
    context: dict[str, Any] = Field(default_factory=dict)


class DeliveryGenerateResponse(BaseModel):
    plan: DeliveryPlan
    slides: list[DeliverySlide]
    summary_card: DeliverySummaryCard
