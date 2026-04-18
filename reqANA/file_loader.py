from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}


async def read_requirement_file(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(
            f"Unsupported requirement file type '{suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_TEXT_EXTENSIONS))}."
        )

    raw = await file.read()
    return raw.decode("utf-8")

