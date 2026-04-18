from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.mock_data import get_scenario_data


def main() -> None:
    scenario = get_scenario_data("margin_q3")
    output_path = BACKEND_ROOT / "sample_data" / "generated_demo_seed.json"
    payload = {
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "request": scenario["seed_request"],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Demo seed written to {output_path}")


if __name__ == "__main__":
    main()
