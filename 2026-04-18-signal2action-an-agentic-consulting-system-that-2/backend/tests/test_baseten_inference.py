import pytest

from app.config import Settings
from app.mock_data import get_scenario_data
from app.services.baseten_inference import BasetenInferenceAdapter


@pytest.mark.asyncio
async def test_baseten_inference_returns_mock_plan() -> None:
    adapter = BasetenInferenceAdapter(Settings())
    scenario = get_scenario_data("margin_q3")
    result = await adapter.generate_plan("plan prompt", scenario)

    assert "recommendations" in result.payload
    assert result.tool_usage.tool == "Baseten"
