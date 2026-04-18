from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


def main() -> int:
    load_dotenv(override=True)

    api_key = os.getenv("BASETEN_API_KEY", "").strip()
    base_url = os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1").strip()
    model = os.getenv("BASETEN_MODEL", "openai/gpt-oss-120b").strip()

    print("Baseten OpenAI-compatible model test")
    print(f"BASETEN_BASE_URL: {base_url}")
    print(f"BASETEN_MODEL: {model or '<missing>'}")
    print(f"BASETEN_API_KEY: {_mask(api_key)}")

    if not api_key:
        print("ERROR: BASETEN_API_KEY is missing in .env")
        return 1
    if not model:
        print("ERROR: BASETEN_MODEL is missing in .env")
        return 1

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a connectivity test."},
                {"role": "user", "content": "Reply with exactly: OK"},
            ],
            stream=True,
            stream_options={
                "include_usage": True,
                "continuous_usage_stats": True,
            },
            top_p=1,
            max_tokens=32,
            temperature=0,
            presence_penalty=0,
            frequency_penalty=0,
        )

        print("SUCCESS: streaming response:")
        streamed_text = []
        usage = None
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                streamed_text.append(chunk.choices[0].delta.content)
                print(chunk.choices[0].delta.content, end="", flush=True)
            if getattr(chunk, "usage", None):
                usage = chunk.usage
        print()
        if usage:
            print(f"Usage: {usage}")
        if not "".join(streamed_text).strip():
            print("Streaming content was empty; trying a non-stream request with the same client.")
            fallback = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a connectivity test. Answer with plain text only."},
                    {"role": "user", "content": "Reply with exactly: OK"},
                ],
                max_tokens=128,
                temperature=0,
            )
            message = fallback.choices[0].message.content or ""
            print(f"Non-stream response: {message!r}")
        return 0
    except Exception as exc:
        print(f"ERROR: Baseten OpenAI-compatible request failed: {exc}")
        return 1


def _mask(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "<present but too short to mask safely>"
    return f"{value[:4]}...{value[-4:]} ({len(value)} chars)"


if __name__ == "__main__":
    sys.exit(main())
