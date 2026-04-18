from __future__ import annotations

from dataclasses import dataclass
import json

import httpx

from app.config import Settings
from app.schemas import SponsorToolUsage


@dataclass
class InferenceResult:
    payload: dict
    tool_usage: SponsorToolUsage


class BasetenInferenceAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_plan(self, prompt: str, scenario_context: dict) -> InferenceResult:
        if self._use_mock():
            return InferenceResult(
                payload=scenario_context.get("plan", {}),
                tool_usage=SponsorToolUsage(
                    tool="Baseten",
                    mode="mock",
                    detail="Mock plan generated from local scenario template.",
                ),
            )

        if not self.settings.baseten_api_key or not self.settings.baseten_model_id:
            raise RuntimeError("Baseten live mode requires BASETEN_API_KEY and BASETEN_MODEL_ID.")

        headers = {
            "Authorization": f"Bearer {self.settings.baseten_api_key}",
            "Content-Type": "application/json",
        }
        endpoint = self.settings.baseten_endpoint or f"{self.settings.baseten_base_url.rstrip('/')}/chat/completions"
        body = {
            "model": self.settings.baseten_model_id,
            "messages": self._build_messages(prompt, scenario_context),
            "temperature": 0.4,
            "top_p": 1,
            "max_tokens": 1400,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        payload = self._parse_chat_completion_payload(data)
        return InferenceResult(
            payload=payload,
            tool_usage=SponsorToolUsage(
                tool="Baseten",
                mode="live",
                detail="Recommendations generated through Baseten OpenAI-compatible chat completions.",
            ),
        )

    def _use_mock(self) -> bool:
        return self.settings.mock_all_services or self.settings.mock_baseten

    def _build_messages(self, prompt: str, scenario_context: dict) -> list[dict[str, str]]:
        plan_schema = {
            "summary": "string",
            "recommendations": [
                {
                    "title": "string",
                    "rationale": "string",
                    "priority": "high | medium | low",
                }
            ],
            "tradeoffs": [
                {
                    "option": "string",
                    "upside": "string",
                    "downside": "string",
                    "recommendation_bias": "string",
                }
            ],
            "action_plan": [
                {
                    "phase": "string",
                    "timeline": "string",
                    "owner": "string",
                    "action": "string",
                    "outcome": "string",
                }
            ],
            "success_metrics": [
                {
                    "name": "string",
                    "target": "string",
                    "timeframe": "string",
                }
            ],
        }

        system_message = (
            "You are Agent 3 inside Signal2Action, an agentic consulting workflow. "
            "Convert the approved scope, assessment, constraints, gaps, modules, and external context into a structured action plan. "
            "Return only valid JSON with no markdown fences and no commentary."
        )

        user_message = (
            f"{prompt}\n\n"
            "Use this context:\n"
            f"{json.dumps(scenario_context, ensure_ascii=True)}\n\n"
            "Return JSON matching this schema exactly:\n"
            f"{json.dumps(plan_schema, ensure_ascii=True)}"
        )

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def _parse_chat_completion_payload(self, data: dict) -> dict:
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Baseten response did not contain any choices.")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content or not isinstance(content, str):
            raise RuntimeError("Baseten response did not contain text content.")

        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Baseten returned non-JSON plan output: {exc}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Baseten returned a JSON payload that is not an object.")

        return parsed
