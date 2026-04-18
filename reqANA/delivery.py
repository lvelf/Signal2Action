from __future__ import annotations

from reqANA.models import (
    DeliveryGenerateRequest,
    DeliveryGenerateResponse,
    DeliveryPlan,
    DeliverySlide,
    DeliverySummaryCard,
    FunctionModule,
)


def build_delivery_response(
    request: DeliveryGenerateRequest,
    plan: DeliveryPlan,
) -> DeliveryGenerateResponse:
    """Turn Agent 3's plan into the slide/card shape consumed by front_end.html."""
    doc = request.requirement_document
    analysis = request.analysis or {}
    modules = request.functions.modules

    title = _first_text(
        doc.title if doc else None,
        _sentence(analysis.get("clarified_problem")),
        "Consulting Requirement",
    )
    scope = _first_text(
        analysis.get("scope"),
        doc.background if doc else None,
        plan.summary,
    )

    executive_bullets = [
        _first_text(plan.summary, doc.executive_summary if doc else None),
        *(_as_list(doc.objectives) if doc else []),
    ]
    situation_bullets = [
        *(_as_list(doc.risks) if doc else []),
        *(_as_list(doc.constraints) if doc else []),
        *(_as_list(analysis.get("assumptions"))),
    ]
    recommendation_bullets = [
        f"{item.title}: {item.rationale}" for item in plan.recommendations
    ] or _as_list(doc.next_steps if doc else [])
    metric_bullets = [
        f"{item.name}: {item.target} ({item.timeframe})" for item in plan.success_metrics
    ]

    slides = [
        DeliverySlide(
            type="title",
            tag="Client Discussion Draft",
            title=title,
            subtitle=scope,
        ),
        DeliverySlide(
            type="problem",
            tag="Executive Summary",
            title="What needs to be solved",
            bullets=_limit(executive_bullets, 5),
        ),
        DeliverySlide(
            type="problem",
            tag="Situation & Implications",
            title="Current state creates execution risk",
            bullets=_limit(situation_bullets, 5),
        ),
        DeliverySlide(
            type="modules",
            tag="Workstream Architecture",
            title="Functional modules required to deliver",
            modules=[_module_to_slide_item(module) for module in modules[:6]],
        ),
        DeliverySlide(
            type="solution",
            tag="Recommendations",
            title="Recommended path forward",
            bullets=_limit(recommendation_bullets, 5),
        ),
        DeliverySlide(
            type="timeline",
            tag="Implementation Roadmap",
            title="30 / 60 / 90 day action plan",
            timeline=_build_timeline(plan, modules),
        ),
    ]
    if metric_bullets:
        slides.append(
            DeliverySlide(
                type="solution",
                tag="Success Metrics",
                title="How progress will be measured",
                bullets=_limit(metric_bullets, 5),
            )
        )

    return DeliveryGenerateResponse(
        plan=plan,
        slides=slides,
        summary_card=DeliverySummaryCard(
            headline=title,
            scope=scope,
            modules=[module.name for module in modules],
            key_actions=_limit([item.action for item in plan.action_plan], 4)
            or _limit([item.title for item in plan.recommendations], 4),
            timeline="30-60-90 day execution path",
        ),
    )


def _build_timeline(plan: DeliveryPlan, modules: list[FunctionModule]) -> dict[str, list[str]]:
    timeline = {"30 days": [], "60 days": [], "90 days": []}
    phase_map = {
        "30": "30 days",
        "60": "60 days",
        "90": "90 days",
        "phase 1": "30 days",
        "phase 2": "60 days",
        "phase 3": "90 days",
    }

    for item in plan.action_plan:
        key_text = f"{item.phase} {item.timeline}".lower()
        bucket = next((value for key, value in phase_map.items() if key in key_text), None)
        if not bucket:
            bucket = min(timeline, key=lambda name: len(timeline[name]))
        timeline[bucket].append(item.action)

    module_names = [module.name for module in modules]
    defaults = {
        "30 days": [
            f"Launch {module_names[0]}" if module_names else "Confirm scope and decision criteria",
            "Validate current-state baseline and key assumptions",
            "Align stakeholder owners and governance cadence",
        ],
        "60 days": [
            f"Complete {module_names[1]}" if len(module_names) > 1 else "Complete detailed solution design",
            f"Stand up {module_names[2]}" if len(module_names) > 2 else "Prioritize workstreams and dependencies",
            "Prepare implementation plan and risk controls",
        ],
        "90 days": [
            f"Begin execution of {module_names[3]}" if len(module_names) > 3 else "Launch prioritized roadmap",
            "Track success metrics and operating cadence",
            "Run executive review and next-wave planning",
        ],
    }
    return {key: _limit(values or defaults[key], 3) for key, values in timeline.items()}


def _module_to_slide_item(module: FunctionModule) -> dict[str, str]:
    return {
        "name": module.name,
        "description": module.description,
        "priority": module.priority,
        "complexity": module.complexity,
    }


def _as_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(value)]


def _first_text(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _sentence(value: object) -> str:
    text = _first_text(value)
    if not text:
        return ""
    return text.split(".")[0].strip()


def _limit(values: list[str], count: int) -> list[str]:
    return [value for value in values if value][:count]
