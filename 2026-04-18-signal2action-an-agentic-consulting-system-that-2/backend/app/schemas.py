from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SponsorToolUsage(BaseModel):
    tool: str
    mode: Literal["mock", "live", "disabled"]
    detail: str


class StageMetadata(BaseModel):
    stage: str
    status: Literal["ready", "running", "completed", "error"] = "completed"
    tool_usages: list[SponsorToolUsage] = Field(default_factory=list)


class InputSourcePayload(BaseModel):
    text_input: str | None = None
    voice_transcript: str | None = None
    audio_reference: str | None = None
    attachments: list[str] = Field(default_factory=list)
    context_notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntakeRequest(InputSourcePayload):
    pass


class IntakeResponse(BaseModel):
    normalized_input: str
    extracted_signals: list[str]
    assumptions: list[str]
    missing_information: list[str]
    problem_statement: str
    clarifying_questions: list[str]
    metadata: StageMetadata


class ClarifyRequest(BaseModel):
    normalized_input: str
    extracted_signals: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    context_notes: str | None = None


class ClarifyResponse(BaseModel):
    problem_statement: str
    clarified_scope: str
    assumptions: list[str]
    missing_information: list[str]
    clarifying_questions: list[str]
    metadata: StageMetadata


class ReviewRequest(BaseModel):
    problem_statement: str
    clarified_scope: str
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    approved: bool = True
    reviewer_edits: str | None = None
    reviewer_notes: str | None = None


class ReviewResponse(BaseModel):
    problem_statement: str
    approved_scope: str
    review_notes: list[str]
    assumptions: list[str]
    missing_information: list[str]
    metadata: StageMetadata


class SearchContextItem(BaseModel):
    title: str
    summary: str
    source: str


class FunctionalModule(BaseModel):
    name: str
    objective: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str]
    recommended_approach: str
    priority: Literal["high", "medium", "low"] = "medium"
    complexity: Literal["high", "medium", "low"] = "medium"
    depends_on: list[str] = Field(default_factory=list)
    include_in_deliverable: bool = True
    owner_hint: str


class AssessmentRequest(BaseModel):
    problem_statement: str
    approved_scope: str
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    include_external_context: bool = True


class AssessmentResponse(BaseModel):
    problem_statement: str
    decomposition_summary: str
    current_state: list[str]
    constraints: list[str]
    dependencies: list[str]
    gaps: list[str]
    modules: list[FunctionalModule]
    critical_path: list[str] = Field(default_factory=list)
    parallel_workstreams: list[str] = Field(default_factory=list)
    external_context: list[SearchContextItem] = Field(default_factory=list)
    metadata: StageMetadata


class Recommendation(BaseModel):
    title: str
    rationale: str
    priority: Literal["high", "medium", "low"]


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


class PlanRequest(BaseModel):
    problem_statement: str
    approved_scope: str
    current_state: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    modules: list[FunctionalModule] = Field(default_factory=list)
    external_context: list[SearchContextItem] = Field(default_factory=list)


class PlanResponse(BaseModel):
    recommendations: list[Recommendation]
    tradeoffs: list[Tradeoff]
    action_plan: list[ActionItem]
    success_metrics: list[SuccessMetric]
    summary: str
    metadata: StageMetadata


class SimulationRequest(BaseModel):
    stage: str | None = None
    scenario_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    simulation_mode: str
    status: Literal["passed", "warning", "failed"]
    checks: list[str]
    risks: list[str]
    metadata: StageMetadata


class RunDemoRequest(BaseModel):
    scenario_id: str | None = None
    overrides: InputSourcePayload | None = None


class RunDemoResponse(BaseModel):
    intake: IntakeResponse
    clarify: ClarifyResponse
    review: ReviewResponse
    assess: AssessmentResponse
    plan: PlanResponse
    simulate: SimulationResponse


class DemoSeed(BaseModel):
    scenario_id: str
    title: str
    request: InputSourcePayload
