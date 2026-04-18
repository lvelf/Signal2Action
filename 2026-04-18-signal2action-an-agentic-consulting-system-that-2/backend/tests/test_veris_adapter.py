import pytest

from app.config import Settings
from app.mock_data import get_scenario_data
from app.services.veris_adapter import VerisAdapter


@pytest.mark.asyncio
async def test_veris_adapter_returns_mock_simulation() -> None:
    adapter = VerisAdapter(Settings())
    scenario = get_scenario_data("margin_q3")
    result = await adapter.simulate("full_workflow", {}, scenario)

    assert result.payload["status"] == "passed"
    assert result.tool_usage.tool == "Veris"
