from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent.parent / "sample_data" / "mock_scenarios.json"


@lru_cache
def load_mock_scenarios() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_scenario_data(scenario_id: str | None = None, hint_text: str | None = None) -> dict:
    scenarios = load_mock_scenarios()

    if scenario_id and scenario_id in scenarios:
        return scenarios[scenario_id]

    normalized = (hint_text or "").lower()
    if "margin" in normalized or "q3" in normalized:
        return scenarios["margin_q3"]
    if "southeast asia" in normalized or "apac" in normalized:
        return scenarios["apac_expansion"]
    if "onboarding" in normalized or "time-to-value" in normalized:
        return scenarios["ops_onboarding"]

    return scenarios["margin_q3"]
