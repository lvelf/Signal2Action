from __future__ import annotations

import os
from tempfile import NamedTemporaryFile

from fastapi import UploadFile


class AudioTranscriber:
    def __init__(self, model: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The installed openai package is too old. Run `pip install -U openai` "
                "or reinstall this project with `pip install -e .`."
            ) from exc

        self.model = model or os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
        self.client = OpenAI()

    async def transcribe_upload(self, file: UploadFile) -> str:
        suffix = _safe_suffix(file.filename)
        with NamedTemporaryFile(suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp.flush()
            with open(tmp.name, "rb") as audio:
                result = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio,
                )
        return result.text


def _safe_suffix(filename: str | None) -> str:
    suffix = os.path.splitext(filename or "")[1].lower()
    return suffix if suffix in {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"} else ".wav"
