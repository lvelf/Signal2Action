from __future__ import annotations

from dataclasses import dataclass

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

        headers = {"Authorization": f"Api-Key {self.settings.baseten_api_key}"}
        endpoint = self.settings.baseten_endpoint or (
            f"https://model-{self.settings.baseten_model_id}.api.baseten.co/"
            f"environments/{self.settings.baseten_environment}/predict"
        )
        body = {
            "prompt": prompt,
            "context": scenario_context,
        }
        # TODO: Align this JSON body with the deployed model or chain input contract in Baseten.
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        payload = data.get("output") if isinstance(data.get("output"), dict) else data
        return InferenceResult(
            payload=payload,
            tool_usage=SponsorToolUsage(
                tool="Baseten",
                mode="live",
                detail="Recommendations generated through Baseten live inference.",
            ),
        )

    def _use_mock(self) -> bool:
        return self.settings.mock_all_services or self.settings.mock_baseten
