from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


def main() -> int:
    load_dotenv()

    api_key = os.getenv("BASETEN_API_KEY", "").strip()
    base_url = os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1").rstrip("/")
    model = os.getenv("BASETEN_MODEL", "deepseek-ai/DeepSeek-V3.1").strip()

    print("Baseten connection test")
    print(f"BASETEN_BASE_URL: {base_url}")
    print(f"BASETEN_MODEL: {model or '<missing>'}")
    print(f"BASETEN_API_KEY: {_mask(api_key)}")

    if not api_key:
        print("ERROR: BASETEN_API_KEY is missing in .env")
        return 1
    if not model:
        print("ERROR: BASETEN_MODEL is missing in .env")
        return 1

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a connectivity test."},
            {"role": "user", "content": "Reply with exactly: OK"},
        ],
        "max_tokens": 8,
        "temperature": 0,
    }

    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"ERROR: Baseten returned HTTP {exc.code}")
        print(_safe_error(detail))
        return 1
    except URLError as exc:
        print(f"ERROR: Could not connect to Baseten: {exc}")
        return 1

    message = body["choices"][0]["message"]["content"]
    print(f"SUCCESS: Baseten responded: {message!r}")
    return 0


def _mask(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "<present but too short to mask safely>"
    return f"{value[:4]}...{value[-4:]} ({len(value)} chars)"


def _safe_error(value: str) -> str:
    text = value.strip()
    if len(text) > 1000:
        return text[:1000] + "..."
    return text


if __name__ == "__main__":
    sys.exit(main())
