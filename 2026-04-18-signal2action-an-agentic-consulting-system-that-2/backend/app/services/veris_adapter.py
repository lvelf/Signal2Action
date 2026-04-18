from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings
from app.schemas import SponsorToolUsage


@dataclass
class VerisSimulationResult:
    payload: dict
    tool_usage: SponsorToolUsage


class VerisAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def simulate(self, stage: str, payload: dict, scenario_context: dict) -> VerisSimulationResult:
        if self._use_mock():
            return VerisSimulationResult(
                payload=scenario_context.get("simulation", {}),
                tool_usage=SponsorToolUsage(
                    tool="Veris",
                    mode="mock",
                    detail="Mock simulation output generated from local QA templates.",
                ),
            )

        if not self.settings.veris_api_key or not self.settings.veris_endpoint:
            raise RuntimeError("Veris live mode requires VERIS_API_KEY and VERIS_ENDPOINT.")

        headers = {"Authorization": f"Bearer {self.settings.veris_api_key}"}
        body = {"stage": stage, "payload": payload}
        # TODO: Replace request/response fields with the official Veris API contract when available.
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.settings.veris_endpoint, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        return VerisSimulationResult(
            payload=data,
            tool_usage=SponsorToolUsage(
                tool="Veris",
                mode="live",
                detail="QA simulation executed through Veris live adapter.",
            ),
        )

    def _use_mock(self) -> bool:
        return self.settings.mock_all_services or self.settings.mock_veris
