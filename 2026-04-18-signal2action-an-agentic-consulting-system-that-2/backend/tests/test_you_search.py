import pytest

from app.config import Settings
from app.mock_data import get_scenario_data
from app.services.you_search import YouSearchAdapter


@pytest.mark.asyncio
async def test_you_search_returns_mock_context() -> None:
    adapter = YouSearchAdapter(Settings())
    scenario = get_scenario_data("margin_q3")
    result = await adapter.search("margin compression", scenario_context=scenario)

    assert result.items
    assert result.tool_usage
    assert result.tool_usage.tool == "You.com"
