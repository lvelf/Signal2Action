from __future__ import annotations

import json
import os
from datetime import UTC, datetime

from openai import OpenAI
from primfunctions.events import StartEvent, TextEvent, TextToSpeechEvent


SYSTEM_PROMPT = """You are a senior consulting business analyst.
Transform the user's spoken consulting requirement into a clear requirement document.

Rules:
- Preserve uncertain points as open questions instead of inventing facts.
- Write in crisp professional English unless the input is primarily Chinese; then write Chinese.
- Prefer business outcomes, users, workflows, integrations, data, constraints, and acceptance signals.
- Return only valid JSON matching the requested schema.
"""


def requirement_schema() -> dict:
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
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


async def handler(event, context):
    if isinstance(event, StartEvent):
        yield TextToSpeechEvent(
            text=(
                "Hi. Please describe the consulting requirement. "
                "I will turn your spoken notes into a requirement document."
            ),
            voice="nova",
        )
        return

    if isinstance(event, TextEvent):
        user_text = event.data.get("text", "").strip()
        if not user_text:
            yield TextToSpeechEvent(text="I did not catch that. Please say it again.", voice="nova")
            return

        document = generate_requirement_document(user_text, context)
        markdown = render_markdown(document)
        context.set_data("latest_requirement_document", markdown)
        context.set_data("latest_user_text", user_text)

        summary = (
            f"I created a requirement document titled {document['title']}. "
            f"I found {len(document['open_questions'])} open questions and "
            f"{len(document['next_steps'])} next steps."
        )
        yield TextToSpeechEvent(text=summary, voice="nova")


def generate_requirement_document(user_text: str, context) -> dict:
    api_key = context.variables.get("BASETEN_API_KEY") or os.getenv("BASETEN_API_KEY")
    base_url = (
        context.variables.get("BASETEN_BASE_URL")
        or os.getenv("BASETEN_BASE_URL")
        or "https://inference.baseten.co/v1"
    )
    model = (
        context.variables.get("BASETEN_MODEL")
        or os.getenv("BASETEN_MODEL")
        or "deepseek-ai/DeepSeek-V3.1"
    )
    if not api_key:
        raise RuntimeError("BASETEN_API_KEY is missing in VoiceRun environment variables.")

    client = OpenAI(base_url=base_url, api_key=api_key)
    schema = requirement_schema()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Create a consulting requirement document from this spoken input.\n\n"
                    "Return a single valid JSON object matching this JSON schema exactly. "
                    "Do not wrap it in markdown.\n\n"
                    f"JSON schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
                    f"Spoken input:\n{user_text}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(clean_json_text(content))


def render_markdown(document: dict) -> str:
    sections = [
        f"# {document['title']}",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "## Executive Summary",
        document["executive_summary"],
        "## Background",
        document["background"],
        render_list("Objectives", document["objectives"]),
        render_list("Stakeholders", document["stakeholders"]),
        render_list("Functional Requirements", document["functional_requirements"]),
        render_list("Non-Functional Requirements", document["non_functional_requirements"]),
        render_list("Assumptions", document["assumptions"]),
        render_list("Constraints", document["constraints"]),
        render_list("Risks", document["risks"]),
        render_list("Open Questions", document["open_questions"]),
        render_list("Success Metrics", document["success_metrics"]),
        render_list("Next Steps", document["next_steps"]),
    ]
    return "\n\n".join(section for section in sections if section).strip()


def render_list(title: str, values: list[str]) -> str:
    if not values:
        return f"## {title}\n\nNone identified."
    return f"## {title}\n\n" + "\n".join(f"- {value}" for value in values)


def clean_json_text(value: str) -> str:
    text = value.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()
    return text
