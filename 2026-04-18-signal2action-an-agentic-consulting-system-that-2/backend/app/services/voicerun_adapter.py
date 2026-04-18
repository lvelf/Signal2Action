from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings
from app.schemas import SponsorToolUsage


@dataclass
class VoiceRunResult:
    transcript: str
    tool_usage: SponsorToolUsage


class VoiceRunAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def transcribe(
        self,
        voice_transcript: str | None = None,
        audio_reference: str | None = None,
    ) -> VoiceRunResult:
        if voice_transcript:
            return VoiceRunResult(
                transcript=voice_transcript.strip(),
                tool_usage=SponsorToolUsage(
                    tool="VoiceRun",
                    mode="mock" if self._use_mock() else "live",
                    detail="Using supplied voice transcript as the VoiceRun entry point.",
                ),
            )

        if self._use_mock():
            mocked = (
                "Our margins are down in Q3. We need a clear recommendation on where to act first."
            )
            return VoiceRunResult(
                transcript=mocked,
                tool_usage=SponsorToolUsage(
                    tool="VoiceRun",
                    mode="mock",
                    detail="No VoiceRun credentials configured, returning mock transcript.",
                ),
            )

        if not self.settings.voicerun_api_key or not self.settings.voicerun_endpoint:
            raise RuntimeError("VoiceRun live mode requires VOICERUN_API_KEY and VOICERUN_ENDPOINT.")

        # TODO: Replace payload shape with the official VoiceRun API contract when available.
        payload = {"audio_reference": audio_reference}
        headers = {"Authorization": f"Bearer {self.settings.voicerun_api_key}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(self.settings.voicerun_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        transcript = data.get("transcript") or data.get("text")
        if not transcript:
            raise RuntimeError("VoiceRun response did not contain a transcript field.")

        return VoiceRunResult(
            transcript=transcript.strip(),
            tool_usage=SponsorToolUsage(
                tool="VoiceRun",
                mode="live",
                detail="Voice transcript sourced from VoiceRun live adapter.",
            ),
        )

    def _use_mock(self) -> bool:
        return self.settings.mock_all_services or self.settings.mock_voicerun
