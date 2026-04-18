from __future__ import annotations

import asyncio
from dataclasses import dataclass
import shutil

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

        if (
            not self.settings.veris_api_key
            or not self.settings.veris_environment_id
            or not self.settings.veris_scenario_set_id
        ):
            raise RuntimeError(
                "Veris live mode requires VERIS_API_KEY, VERIS_ENVIRONMENT_ID, and VERIS_SCENARIO_SET_ID."
            )

        if shutil.which("veris") is None:
            return VerisSimulationResult(
                payload={
                    "simulation_mode": "live-cli-not-installed",
                    "status": "warning",
                    "checks": [
                        "Veris live configuration is present.",
                        f"Environment ID: {self.settings.veris_environment_id}",
                        f"Scenario set ID: {self.settings.veris_scenario_set_id}",
                    ],
                    "risks": [
                        "The `veris` CLI is not installed on this machine, so no live run was submitted.",
                        "Install the CLI and authenticate it before retrying the QA step.",
                    ],
                },
                tool_usage=SponsorToolUsage(
                    tool="Veris",
                    mode="disabled",
                    detail="Veris live configuration found, but the local Veris CLI is not installed.",
                ),
            )

        command = [
            "veris",
            "simulations",
            "create",
            "--scenario-set-id",
            self.settings.veris_scenario_set_id,
            "--env-id",
            self.settings.veris_environment_id,
            "--simulation-timeout",
            str(self.settings.veris_simulation_timeout),
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode != 0:
            return VerisSimulationResult(
                payload={
                    "simulation_mode": "live-cli-error",
                    "status": "failed",
                    "checks": [
                        "Veris CLI was found and invoked.",
                        f"Environment ID: {self.settings.veris_environment_id}",
                        f"Scenario set ID: {self.settings.veris_scenario_set_id}",
                    ],
                    "risks": [
                        "Veris simulation submission failed.",
                        stderr_text or stdout_text or "The Veris CLI returned a non-zero exit code.",
                    ],
                },
                tool_usage=SponsorToolUsage(
                    tool="Veris",
                    mode="live",
                    detail="Veris CLI was invoked but the simulation run did not submit successfully.",
                ),
            )

        return VerisSimulationResult(
            payload={
                "simulation_mode": "live-cli-submitted",
                "status": "warning",
                "checks": [
                    "Veris simulation run submitted from the final QA step.",
                    f"Environment ID: {self.settings.veris_environment_id}",
                    f"Scenario set ID: {self.settings.veris_scenario_set_id}",
                    stdout_text or "Check the Veris console or CLI for the submitted run details.",
                ],
                "risks": [
                    "The current MVP submits the simulation run but does not yet poll Veris for final evaluation results.",
                    "Live grading details still need a follow-up integration pass.",
                ],
            },
            tool_usage=SponsorToolUsage(
                tool="Veris",
                mode="live",
                detail="QA simulation submitted through the Veris CLI using the configured environment and scenario set.",
            ),
        )

    def _use_mock(self) -> bool:
        return self.settings.mock_all_services or self.settings.mock_veris
