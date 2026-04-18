from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from reqANA.voicerun_handler import generate_requirement_from_voicerun_text


DEFAULT_TEXT = (
    "The client wants a 90-day CRM rollout roadmap. Sales leads are tracked in spreadsheets. "
    "Sales managers need pipeline visibility by region. Marketing handoff is inconsistent. "
    "The solution must integrate with finance reporting."
)


def main() -> int:
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(
        description="Local VoiceRun TextEvent simulation for reqANA requirement generation."
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=DEFAULT_TEXT,
        help="Text that simulates event.data['text'] from VoiceRun.",
    )
    args = parser.parse_args()

    print("Simulating VoiceRun TextEvent...")
    print(f"user_text: {args.text}")
    summary, markdown = generate_requirement_from_voicerun_text(args.text, source="speech")
    print("\nVoiceRun spoken summary:")
    print(summary)
    print("\nGenerated Markdown preview:")
    print(markdown[:1200])
    if len(markdown) > 1200:
        print("...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
