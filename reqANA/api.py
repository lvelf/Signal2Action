from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from reqANA.agent import RequirementAgent, render_markdown, save_markdown
from reqANA.file_loader import read_requirement_file
from reqANA.models import IntakeSource, RequirementDocument, RequirementInput
from reqANA.transcription import AudioTranscriber

load_dotenv(override=True)

app = FastAPI(title="Signal2Action Requirement Intake API")


class TextRequirementRequest(BaseModel):
    content: str = Field(min_length=1)
    source: IntakeSource = IntakeSource.TEXT
    metadata: dict = Field(default_factory=dict)


class RequirementResponse(BaseModel):
    document: RequirementDocument
    markdown: str
    saved_path: str | None = None


class VerisRequest(BaseModel):
    message: str = Field(min_length=1)


class VerisResponse(BaseModel):
    response: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/config")
def debug_config() -> dict[str, str | int | bool | None]:
    """Show non-secret runtime config loaded by the API process."""
    import os

    baseten_key = os.getenv("BASETEN_API_KEY", "")
    return {
        "model_provider": os.getenv("MODEL_PROVIDER"),
        "baseten_base_url": os.getenv("BASETEN_BASE_URL"),
        "baseten_model": os.getenv("BASETEN_MODEL"),
        "baseten_api_key_present": bool(baseten_key),
        "baseten_api_key_length": len(baseten_key),
        "baseten_api_key_masked": _mask_secret(baseten_key),
    }


@app.post("/requirements/from-text", response_model=RequirementResponse)
def requirements_from_text(payload: TextRequirementRequest) -> RequirementResponse:
    requirement_input = RequirementInput(
        source=payload.source,
        content=payload.content,
        metadata=payload.metadata,
    )
    return _generate_response([requirement_input])


@app.post("/veris/requirement-agent", response_model=VerisResponse)
def veris_requirement_agent(payload: VerisRequest) -> VerisResponse:
    result = requirements_from_text(
        TextRequirementRequest(
            content=payload.message,
            metadata={"channel": "veris_simulation"},
        )
    )
    return VerisResponse(response=result.markdown)


@app.post("/requirements/from-file", response_model=RequirementResponse)
async def requirements_from_file(file: UploadFile = File(...)) -> RequirementResponse:
    try:
        content = await read_requirement_file(file)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    requirement_input = RequirementInput(
        source=IntakeSource.FILE,
        content=content,
        filename=file.filename,
    )
    return _generate_response([requirement_input])


@app.post("/requirements/from-voice", response_model=RequirementResponse)
async def requirements_from_voice(
    audio: UploadFile = File(...),
    context: str | None = Form(default=None),
) -> RequirementResponse:
    transcript = await AudioTranscriber().transcribe_upload(audio)
    inputs = []
    if context:
        inputs.append(RequirementInput(source=IntakeSource.TEXT, content=context))
    inputs.append(
        RequirementInput(
            source=IntakeSource.VOICE,
            content=transcript,
            filename=audio.filename,
            metadata={"transcript_source": "audio_upload"},
        )
    )
    return _generate_response(inputs)


@app.post("/requirements/from-mixed", response_model=RequirementResponse)
async def requirements_from_mixed(
    files: list[UploadFile] | None = File(default=None),
    audio: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> RequirementResponse:
    inputs: list[RequirementInput] = []
    if text:
        inputs.append(RequirementInput(source=IntakeSource.TEXT, content=text))

    for file in files or []:
        try:
            content = await read_requirement_file(file)
        except (UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"{file.filename}: {exc}") from exc
        inputs.append(RequirementInput(source=IntakeSource.FILE, content=content, filename=file.filename))

    if audio:
        transcript = await AudioTranscriber().transcribe_upload(audio)
        inputs.append(
            RequirementInput(
                source=IntakeSource.VOICE,
                content=transcript,
                filename=audio.filename,
                metadata={"transcript_source": "audio_upload"},
            )
        )

    if not inputs:
        raise HTTPException(status_code=400, detail="Provide at least one text, file, or audio input.")

    return _generate_response(inputs)


def _generate_response(inputs: list[RequirementInput]) -> RequirementResponse:
    try:
        document = RequirementAgent().generate(inputs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Requirement agent failed: {exc}") from exc

    saved_path = save_markdown(document, Path("outputs"))
    return RequirementResponse(
        document=document,
        markdown=render_markdown(document),
        saved_path=str(saved_path),
    )


def _mask_secret(value: str) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "<present but too short to mask safely>"
    return f"{value[:4]}...{value[-4:]}"
