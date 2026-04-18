import pytest

from app.config import Settings
from app.services.voicerun_adapter import VoiceRunAdapter


@pytest.mark.asyncio
async def test_voicerun_adapter_returns_supplied_transcript() -> None:
    adapter = VoiceRunAdapter(Settings())
    result = await adapter.transcribe("hello from voice")

    assert result.transcript == "hello from voice"
    assert result.tool_usage.tool == "VoiceRun"
