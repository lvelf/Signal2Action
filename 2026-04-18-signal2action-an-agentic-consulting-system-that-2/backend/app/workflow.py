from __future__ import annotations

from app.mock_data import get_scenario_data
from app.schemas import (
    ActionItem,
    AssessmentRequest,
    AssessmentResponse,
    ClarifyRequest,
    ClarifyResponse,
    FunctionalModule,
    IntakeRequest,
    IntakeResponse,
    PlanRequest,
    PlanResponse,
    Recommendation,
    ReviewRequest,
    ReviewResponse,
    RunDemoRequest,
    RunDemoResponse,
    SearchContextItem,
    SimulationRequest,
    SimulationResponse,
    SponsorToolUsage,
    StageMetadata,
    SuccessMetric,
    Tradeoff,
)
from app.services.baseten_inference import BasetenInferenceAdapter
from app.services.veris_adapter import VerisAdapter
from app.services.voicerun_adapter import VoiceRunAdapter
from app.services.you_search import YouSearchAdapter


def _merge_tool_usages(*items: SponsorToolUsage | None) -> list[SponsorToolUsage]:
    return [item for item in items if item is not None]


async def run_intake(request: IntakeRequest, voice_adapter: VoiceRunAdapter) -> IntakeResponse:
    voice_result = await voice_adapter.transcribe(request.voice_transcript, request.audio_reference)
    source_text = " ".join(part for part in [request.text_input, voice_result.transcript, request.context_notes] if part)
    scenario = get_scenario_data(hint_text=source_text)
    intake = scenario["intake"]

    normalized_input = " ".join(
        segment.strip()
        for segment in [request.text_input or "", voice_result.transcript or "", request.context_notes or ""]
        if segment and segment.strip()
    ).strip()

    if not normalized_input:
        normalized_input = scenario["seed_request"]["text_input"]

    return IntakeResponse(
        normalized_input=normalized_input,
        extracted_signals=intake["extracted_signals"],
        assumptions=intake["assumptions"],
        missing_information=intake["missing_information"],
        problem_statement=intake["problem_statement"],
        clarifying_questions=intake["clarifying_questions"],
        metadata=StageMetadata(
            stage="intake",
            tool_usages=_merge_tool_usages(voice_result.tool_usage),
        ),
    )


async def run_clarify(request: ClarifyRequest) -> ClarifyResponse:
    scenario = get_scenario_data(hint_text=request.normalized_input)
    clarify = scenario["clarify"]
    return ClarifyResponse(
        problem_statement=clarify["problem_statement"],
        clarified_scope=clarify["clarified_scope"],
        assumptions=request.assumptions or clarify["assumptions"],
        missing_information=request.missing_information or clarify["missing_information"],
        clarifying_questions=clarify["clarifying_questions"],
        metadata=StageMetadata(
            stage="clarify",
            tool_usages=[],
        ),
    )


async def run_review(request: ReviewRequest) -> ReviewResponse:
    approved_scope = request.reviewer_edits.strip() if request.reviewer_edits else request.clarified_scope
    notes = [
        "Human reviewer confirmed scope before downstream analysis."
        if request.approved
        else "Human reviewer requested additional clarification before analysis."
    ]
    if request.reviewer_notes:
        notes.append(request.reviewer_notes)

    return ReviewResponse(
        problem_statement=request.problem_statement,
        approved_scope=approved_scope,
        review_notes=notes,
        assumptions=request.assumptions,
        missing_information=request.missing_information,
        metadata=StageMetadata(stage="review", tool_usages=[]),
    )


async def run_assess(request: AssessmentRequest, you_adapter: YouSearchAdapter) -> AssessmentResponse:
    scenario = get_scenario_data(hint_text=request.approved_scope)
    assessment = scenario["assessment"]
    search_result = await you_adapter.search(request.approved_scope, scenario_context=scenario)

    return AssessmentResponse(
        problem_statement=request.problem_statement,
        current_state=assessment["current_state"],
        constraints=assessment["constraints"],
        dependencies=assessment["dependencies"],
        gaps=assessment["gaps"],
        modules=[FunctionalModule(**item) for item in assessment["modules"]],
        external_context=search_result.items if request.include_external_context else [],
        metadata=StageMetadata(
            stage="assess",
            tool_usages=_merge_tool_usages(search_result.tool_usage),
        ),
    )


async def run_plan(request: PlanRequest, baseten_adapter: BasetenInferenceAdapter) -> PlanResponse:
    scenario = get_scenario_data(hint_text=request.approved_scope)
    prompt = (
        f"Generate a solution recommendation and action plan for: {request.problem_statement}. "
        f"Approved scope: {request.approved_scope}."
    )
    inference_result = await baseten_adapter.generate_plan(prompt, scenario_context=scenario)
    plan = inference_result.payload

    return PlanResponse(
        recommendations=[Recommendation(**item) for item in plan["recommendations"]],
        tradeoffs=[Tradeoff(**item) for item in plan["tradeoffs"]],
        action_plan=[ActionItem(**item) for item in plan["action_plan"]],
        success_metrics=[SuccessMetric(**item) for item in plan["success_metrics"]],
        summary=plan["summary"],
        metadata=StageMetadata(
            stage="plan",
            tool_usages=_merge_tool_usages(inference_result.tool_usage),
        ),
    )


async def run_simulation(request: SimulationRequest, veris_adapter: VerisAdapter) -> SimulationResponse:
    scenario = get_scenario_data(scenario_id=request.scenario_id, hint_text=str(request.payload))
    simulation_result = await veris_adapter.simulate(
        stage=request.stage or "full_workflow",
        payload=request.payload,
        scenario_context=scenario,
    )
    payload = simulation_result.payload
    return SimulationResponse(
        simulation_mode=payload.get("simulation_mode", "mock"),
        status=payload.get("status", "passed"),
        checks=payload.get("checks", []),
        risks=payload.get("risks", []),
        metadata=StageMetadata(
            stage="simulate",
            tool_usages=_merge_tool_usages(simulation_result.tool_usage),
        ),
    )


async def run_demo(
    request: RunDemoRequest,
    voice_adapter: VoiceRunAdapter,
    you_adapter: YouSearchAdapter,
    baseten_adapter: BasetenInferenceAdapter,
    veris_adapter: VerisAdapter,
) -> RunDemoResponse:
    scenario = get_scenario_data(scenario_id=request.scenario_id)
    overrides = request.overrides

    intake_request = IntakeRequest(
        text_input=(overrides.text_input if overrides and overrides.text_input else scenario["seed_request"]["text_input"]),
        voice_transcript=(
            overrides.voice_transcript
            if overrides and overrides.voice_transcript
            else scenario["seed_request"]["voice_transcript"]
        ),
        audio_reference=overrides.audio_reference if overrides else None,
        attachments=overrides.attachments if overrides else scenario["seed_request"].get("attachments", []),
        context_notes=overrides.context_notes if overrides else scenario["seed_request"].get("context_notes"),
        metadata=overrides.metadata if overrides else {},
    )
    intake = await run_intake(intake_request, voice_adapter)

    clarify = await run_clarify(
        ClarifyRequest(
            normalized_input=intake.normalized_input,
            extracted_signals=intake.extracted_signals,
            assumptions=intake.assumptions,
            missing_information=intake.missing_information,
        )
    )

    review = await run_review(
        ReviewRequest(
            problem_statement=clarify.problem_statement,
            clarified_scope=clarify.clarified_scope,
            assumptions=clarify.assumptions,
            missing_information=clarify.missing_information,
            approved=True,
            reviewer_edits=scenario["review"]["approved_scope"],
            reviewer_notes=scenario["review"]["review_notes"][0],
        )
    )

    assess = await run_assess(
        AssessmentRequest(
            problem_statement=review.problem_statement,
            approved_scope=review.approved_scope,
            assumptions=review.assumptions,
            missing_information=review.missing_information,
        ),
        you_adapter,
    )

    plan = await run_plan(
        PlanRequest(
            problem_statement=review.problem_statement,
            approved_scope=review.approved_scope,
            current_state=assess.current_state,
            constraints=assess.constraints,
            dependencies=assess.dependencies,
            gaps=assess.gaps,
            modules=assess.modules,
            external_context=assess.external_context,
        ),
        baseten_adapter,
    )

    simulate = await run_simulation(
        SimulationRequest(
            stage="full_workflow",
            scenario_id=request.scenario_id or scenario["id"],
            payload={
                "problem_statement": review.problem_statement,
                "approved_scope": review.approved_scope,
                "recommendation_count": len(plan.recommendations),
            },
        ),
        veris_adapter,
    )

    return RunDemoResponse(
        intake=intake,
        clarify=clarify,
        review=review,
        assess=assess,
        plan=plan,
        simulate=simulate,
    )
