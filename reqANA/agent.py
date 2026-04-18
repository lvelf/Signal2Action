from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from reqANA.models import FunctionDecompositionRequest, FunctionDecompositionResponse, RequirementDocument, RequirementInput


REQUIREMENT_SYSTEM_PROMPT = """You are a senior consulting business analyst.
Transform rough client notes, uploaded requirement files, or voice transcripts into a clear
consulting requirement document.

Rules:
- Preserve uncertain points as open questions instead of inventing facts.
- Write in crisp professional English unless the input is primarily Chinese; then write Chinese.
- Prefer business outcomes, users, workflows, integrations, data, constraints, and acceptance signals.
- Return only valid JSON matching the requested schema.
"""

FUNCTION_SYSTEM_PROMPT = """You are Agent 2 in a consulting workflow: Assessment and Function Decomposition.
Given a clarified consulting requirement, break the work into functional modules that can be handed
to delivery teams or downstream solution planning.

Rules:
- Produce practical consulting workstreams, not software-only components.
- Each module must have a clear input, output, recommended approach, priority, and complexity.
- Include 4 to 7 modules.
- Critical path must contain module names from the modules list in execution order.
- Return only valid JSON matching the requested schema.
"""


def _json_schema() -> dict:
    string_list = {"type": "array", "items": {"type": "string"}}
    properties = {
        "title": {"type": "string"},
        "executive_summary": {"type": "string"},
        "background": {"type": "string"},
        "objectives": string_list,
        "stakeholders": string_list,
        "functional_requirements": string_list,
        "non_functional_requirements": string_list,
        "assumptions": string_list,
        "constraints": string_list,
        "risks": string_list,
        "open_questions": string_list,
        "success_metrics": string_list,
        "next_steps": string_list,
    }


def _function_schema() -> dict:
    module_properties = {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "input": {"type": "string"},
        "output": {"type": "string"},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "complexity": {"type": "string", "enum": ["high", "medium", "low"]},
        "approach": {"type": "string"},
    }
    properties = {
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": module_properties,
                "required": list(module_properties.keys()),
                "additionalProperties": False,
            },
        },
        "critical_path": {"type": "array", "items": {"type": "string"}},
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


class RequirementAgent:
    def __init__(self, model: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The installed openai package is too old. Run `pip install -U openai` "
                "or reinstall this project with `pip install -e .`."
            ) from exc

        self.provider = os.getenv("MODEL_PROVIDER", "openai").lower()
        if self.provider == "baseten":
            self.model = model or os.getenv("BASETEN_MODEL", "deepseek-ai/DeepSeek-V3.1")
            self.client = OpenAI(
                base_url=os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1"),
                api_key=os.environ["BASETEN_API_KEY"],
            )
            return

        if self.provider == "openai":
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
            self.client = OpenAI()
            return

        raise ValueError("MODEL_PROVIDER must be either 'openai' or 'baseten'.")

    def generate(self, inputs: list[RequirementInput]) -> RequirementDocument:
        if not inputs:
            raise ValueError("At least one input is required.")

        packed_inputs = [
            {
                "source": item.source,
                "filename": item.filename,
                "metadata": item.metadata,
                "content": item.content,
            }
            for item in inputs
        ]

        if self.provider == "baseten":
            return self._generate_with_chat_completions(packed_inputs)

        return self._generate_with_openai_responses(packed_inputs)

    def decompose_functions(
        self,
        request: FunctionDecompositionRequest,
    ) -> FunctionDecompositionResponse:
        payload = request.model_dump(mode="json")
        if self.provider == "baseten":
            return self._decompose_with_chat_completions(payload)
        return self._decompose_with_openai_responses(payload)

    def _generate_with_openai_responses(self, packed_inputs: list[dict[str, Any]]) -> RequirementDocument:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": REQUIREMENT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create a consulting requirement document from these inputs:\n"
                        f"{json.dumps(packed_inputs, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "requirement_document",
                    "schema": _json_schema(),
                    "strict": True,
                }
            },
        )

        return RequirementDocument.model_validate_json(response.output_text)

    def _decompose_with_openai_responses(
        self,
        payload: dict[str, Any],
    ) -> FunctionDecompositionResponse:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": FUNCTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Decompose this consulting requirement into functional modules:\n"
                        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "function_decomposition",
                    "schema": _function_schema(),
                    "strict": True,
                }
            },
        )
        return FunctionDecompositionResponse.model_validate_json(response.output_text)

    def _generate_with_chat_completions(self, packed_inputs: list[dict[str, Any]]) -> RequirementDocument:
        schema = _json_schema()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": REQUIREMENT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create a consulting requirement document from these inputs.\n\n"
                        "Return a single valid JSON object matching this JSON schema exactly. "
                        "Do not wrap it in markdown.\n\n"
                        f"JSON schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
                        f"Inputs:\n{json.dumps(packed_inputs, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        return RequirementDocument.model_validate_json(_clean_json_text(content))

    def _decompose_with_chat_completions(
        self,
        payload: dict[str, Any],
    ) -> FunctionDecompositionResponse:
        schema = _function_schema()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": FUNCTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Decompose this consulting requirement into functional modules.\n\n"
                        "Return a single valid JSON object matching this JSON schema exactly. "
                        "Do not wrap it in markdown.\n\n"
                        f"JSON schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
                        f"Requirement context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        return FunctionDecompositionResponse.model_validate_json(_clean_json_text(content))


def render_markdown(document: RequirementDocument) -> str:
    sections = [
        f"# {document.title}",
        f"Generated at: {document.generated_at.isoformat()}",
        "## Executive Summary",
        document.executive_summary,
        "## Background",
        document.background,
        _render_list("Objectives", document.objectives),
        _render_list("Stakeholders", document.stakeholders),
        _render_list("Functional Requirements", document.functional_requirements),
        _render_list("Non-Functional Requirements", document.non_functional_requirements),
        _render_list("Assumptions", document.assumptions),
        _render_list("Constraints", document.constraints),
        _render_list("Risks", document.risks),
        _render_list("Open Questions", document.open_questions),
        _render_list("Success Metrics", document.success_metrics),
        _render_list("Next Steps", document.next_steps),
    ]
    return "\n\n".join(section for section in sections if section).strip() + "\n"


def save_markdown(document: RequirementDocument, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(ch.lower() if ch.isalnum() else "-" for ch in document.title).strip("-")
    safe_title = "-".join(part for part in safe_title.split("-") if part)[:80] or "requirements"
    output_path = output_dir / f"{safe_title}.md"
    output_path.write_text(render_markdown(document), encoding="utf-8")
    return output_path


def _render_list(title: str, values: list[str]) -> str:
    if not values:
        return f"## {title}\n\nNone identified."
    items = "\n".join(f"- {value}" for value in values)
    return f"## {title}\n\n{items}"


def _clean_json_text(value: str) -> str:
    text = value.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()
    return text
