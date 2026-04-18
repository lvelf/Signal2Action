from __future__ import annotations

from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from reqANA.agent import RequirementAgent, render_markdown, save_markdown
from reqANA.delivery import build_delivery_response
from reqANA.file_loader import read_requirement_file
from reqANA.google_drive_loader import read_google_drive_inputs
from reqANA.models import (
    DeliveryGenerateRequest,
    DeliveryGenerateResponse,
    FunctionDecompositionRequest,
    FunctionDecompositionResponse,
    IntakeSource,
    RequirementDocument,
    RequirementInput,
)
from reqANA.transcription import AudioTranscriber

load_dotenv(override=True)

app = FastAPI(title="Signal2Action Requirement Intake API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class GoogleConfigResponse(BaseModel):
    client_id: str
    api_key: str
    app_id: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/config")
def debug_config() -> dict[str, str | int | bool | None]:
    """Show non-secret runtime config loaded by the API process."""
    baseten_key = os.getenv("BASETEN_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    return {
        "model_provider": os.getenv("MODEL_PROVIDER"),
        "openai_model": os.getenv("OPENAI_MODEL"),
        "openai_api_key_present": bool(openai_key),
        "openai_api_key_length": len(openai_key),
        "openai_api_key_masked": _mask_secret(openai_key),
        "baseten_base_url": os.getenv("BASETEN_BASE_URL"),
        "baseten_model": os.getenv("BASETEN_MODEL"),
        "baseten_api_key_present": bool(baseten_key),
        "baseten_api_key_length": len(baseten_key),
        "baseten_api_key_masked": _mask_secret(baseten_key),
    }


@app.get("/config/google", response_model=GoogleConfigResponse)
def google_config() -> GoogleConfigResponse:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    app_id = os.getenv("GOOGLE_APP_ID", "").strip()
    if not client_id or not api_key or not app_id:
        raise HTTPException(
            status_code=500,
            detail="Google Drive config is missing. Set GOOGLE_CLIENT_ID, GOOGLE_API_KEY, and GOOGLE_APP_ID in .env.",
        )
    return GoogleConfigResponse(client_id=client_id, api_key=api_key, app_id=app_id)


@app.post("/requirements/from-text", response_model=RequirementResponse)
def requirements_from_text(payload: TextRequirementRequest) -> RequirementResponse:
    requirement_input = RequirementInput(
        source=payload.source,
        content=payload.content,
        metadata=payload.metadata,
    )
    return _generate_response([requirement_input])


@app.post("/functions/decompose", response_model=FunctionDecompositionResponse)
def functions_decompose(payload: FunctionDecompositionRequest) -> FunctionDecompositionResponse:
    try:
        return RequirementAgent().decompose_functions(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Function decomposition failed: {exc}") from exc


@app.post("/delivery/generate", response_model=DeliveryGenerateResponse)
def delivery_generate(payload: DeliveryGenerateRequest) -> DeliveryGenerateResponse:
    try:
        plan = RequirementAgent().generate_delivery_plan(payload)
        return build_delivery_response(payload, plan)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Delivery generation failed: {exc}") from exc


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
async def requirements_from_file(files: list[UploadFile] = File(...)) -> RequirementResponse:
    inputs = await _read_uploads(files)
    if not inputs:
        raise HTTPException(status_code=400, detail="Provide at least one requirement file.")
    return _generate_response(inputs)


@app.post("/requirements/from-files", response_model=RequirementResponse)
async def requirements_from_files(files: list[UploadFile] = File(...)) -> RequirementResponse:
    inputs = await _read_uploads(files)
    if not inputs:
        raise HTTPException(status_code=400, detail="Provide at least one requirement file.")
    return _generate_response(inputs)


@app.post("/requirements/from-voice", response_model=RequirementResponse)
async def requirements_from_voice(
    audio: UploadFile = File(...),
    context: str | None = Form(default=None),
) -> RequirementResponse:
    try:
        transcript = await AudioTranscriber().transcribe_upload(audio)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Audio transcription failed: {exc}") from exc
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
    audio_files: list[UploadFile] | None = File(default=None),
    text: str | None = Form(default=None),
    google_access_token: str | None = Form(default=None),
    google_file_ids: list[str] | None = Form(default=None),
    google_folder_ids: list[str] | None = Form(default=None),
    google_recursive: bool = Form(default=False),
) -> RequirementResponse:
    """Generate requirements from browser FormData.

    Expected frontend fields:
    - text: optional plain text
    - files: zero or more requirement files; append this key once per file
    - audio: optional single recorded audio blob/file
    - audio_files: optional repeated recorded audio blobs/files
    - google_access_token: optional Google OAuth access token with Drive read scope
    - google_file_ids: optional repeated Google Drive file IDs
    - google_folder_ids: optional repeated Google Drive folder IDs
    - google_recursive: whether to read folders recursively
    """
    inputs: list[RequirementInput] = []
    if text:
        inputs.append(RequirementInput(source=IntakeSource.TEXT, content=text))

    inputs.extend(await _read_uploads(files or []))
    inputs.extend(
        _read_google_drive_uploads(
            google_access_token=google_access_token,
            google_file_ids=google_file_ids or [],
            google_folder_ids=google_folder_ids or [],
            google_recursive=google_recursive,
        )
    )

    audio_uploads = []
    if _has_upload(audio):
        audio_uploads.append(audio)
    audio_uploads.extend([item for item in audio_files or [] if _has_upload(item)])

    for audio_upload in audio_uploads:
        try:
            transcript = await AudioTranscriber().transcribe_upload(audio_upload)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Audio transcription failed: {exc}") from exc
        inputs.append(
            RequirementInput(
                source=IntakeSource.VOICE,
                content=transcript,
                filename=audio_upload.filename,
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

    saved_path = save_markdown(document, Path("Req_outputs"))
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


def _has_upload(file: UploadFile | None) -> bool:
    return bool(file and file.filename)


async def _read_uploads(files: list[UploadFile]) -> list[RequirementInput]:
    inputs: list[RequirementInput] = []
    for file in files:
        if not _has_upload(file):
            continue
        try:
            content = await read_requirement_file(file)
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"{file.filename}: file must be UTF-8 text.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{file.filename}: {exc}") from exc
        inputs.append(RequirementInput(source=IntakeSource.FILE, content=content, filename=file.filename))
    return inputs


def _read_google_drive_uploads(
    google_access_token: str | None,
    google_file_ids: list[str],
    google_folder_ids: list[str],
    google_recursive: bool,
) -> list[RequirementInput]:
    if not google_access_token or (not google_file_ids and not google_folder_ids):
        return []
    try:
        return read_google_drive_inputs(
            access_token=google_access_token,
            file_ids=google_file_ids,
            folder_ids=google_folder_ids,
            recursive=google_recursive,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Google Drive file error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Drive import failed: {exc}") from exc
