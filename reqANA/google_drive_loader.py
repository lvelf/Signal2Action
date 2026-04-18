from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from reqANA.file_loader import read_requirement_bytes
from reqANA.models import IntakeSource, RequirementInput

log = logging.getLogger("reqANA.google_drive")


DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDE_MIME = "application/vnd.google-apps.presentation"


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    mime_type: str


def read_google_drive_inputs(
    access_token: str,
    file_ids: list[str] | None = None,
    folder_ids: list[str] | None = None,
    recursive: bool = False,
) -> list[RequirementInput]:
    clean_file_ids = [file_id for file_id in file_ids or [] if file_id]
    clean_folder_ids = [folder_id for folder_id in folder_ids or [] if folder_id]

    if not access_token or (not clean_file_ids and not clean_folder_ids):
        return []

    files: list[DriveFile] = []
    seen_ids: set[str] = set()

    for file_id in clean_file_ids:
        item = _get_metadata(access_token, file_id)
        if item.mime_type == GOOGLE_FOLDER_MIME:
            clean_folder_ids.append(item.id)
            continue
        if item.id not in seen_ids:
            seen_ids.add(item.id)
            files.append(item)

    for folder_id in clean_folder_ids:
        for item in _list_folder_files(access_token, folder_id, recursive=recursive):
            if item.id not in seen_ids and item.mime_type != GOOGLE_FOLDER_MIME:
                seen_ids.add(item.id)
                files.append(item)

    inputs: list[RequirementInput] = []
    for item in files:
        log.info("downloading drive file: %s (%s)", item.name, item.mime_type)
        try:
            filename, raw = _download_or_export(access_token, item)
            content = read_requirement_bytes(filename, raw)
        except ValueError as exc:
            log.warning("skipping unsupported drive file %r: %s", item.name, exc)
            continue
        except Exception as exc:
            log.error("failed to download drive file %r: %s: %s", item.name, type(exc).__name__, exc)
            raise
        inputs.append(
            RequirementInput(
                source=IntakeSource.FILE,
                content=content,
                filename=filename,
                metadata={
                    "source": "google_drive",
                    "drive_file_id": item.id,
                    "drive_mime_type": item.mime_type,
                },
            )
        )
    log.info("drive: %d/%d file(s) loaded successfully", len(inputs), len(files))
    return inputs


def _get_metadata(access_token: str, file_id: str) -> DriveFile:
    fields = "id,name,mimeType"
    data = _drive_get_json(access_token, f"/files/{file_id}", {"fields": fields, "supportsAllDrives": "true"})
    return DriveFile(id=data["id"], name=data["name"], mime_type=data["mimeType"])


def _list_folder_files(access_token: str, folder_id: str, recursive: bool) -> list[DriveFile]:
    collected: list[DriveFile] = []
    page_token: str | None = None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": "nextPageToken, files(id,name,mimeType)",
            "pageSize": "100",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        data = _drive_get_json(access_token, "/files", params)
        for raw in data.get("files", []):
            item = DriveFile(id=raw["id"], name=raw["name"], mime_type=raw["mimeType"])
            if item.mime_type == GOOGLE_FOLDER_MIME and recursive:
                collected.extend(_list_folder_files(access_token, item.id, recursive=True))
            else:
                collected.append(item)
        page_token = data.get("nextPageToken")
        if not page_token:
            return collected


def _download_or_export(access_token: str, item: DriveFile) -> tuple[str, bytes]:
    if item.mime_type == GOOGLE_DOC_MIME:
        return _ensure_suffix(item.name, ".txt"), _drive_export(access_token, item.id, "text/plain")
    if item.mime_type == GOOGLE_SHEET_MIME:
        return _ensure_suffix(item.name, ".xlsx"), _drive_export(
            access_token,
            item.id,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    if item.mime_type == GOOGLE_SLIDE_MIME:
        return _ensure_suffix(item.name, ".txt"), _drive_export(access_token, item.id, "text/plain")
    return item.name, _drive_download(access_token, item.id)


def _drive_download(access_token: str, file_id: str) -> bytes:
    query = urlencode({"alt": "media", "supportsAllDrives": "true"})
    return _request_bytes(access_token, f"{DRIVE_API_BASE}/files/{file_id}?{query}")


def _drive_export(access_token: str, file_id: str, mime_type: str) -> bytes:
    query = urlencode({"mimeType": mime_type})
    return _request_bytes(access_token, f"{DRIVE_API_BASE}/files/{file_id}/export?{query}")


def _drive_get_json(access_token: str, path: str, params: dict[str, str]) -> dict:
    query = urlencode(params)
    raw = _request_bytes(access_token, f"{DRIVE_API_BASE}{path}?{query}")
    return json.loads(raw.decode("utf-8"))


def _request_bytes(access_token: str, url: str) -> bytes:
    request = Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def _ensure_suffix(filename: str, suffix: str) -> str:
    return filename if filename.lower().endswith(suffix) else f"{filename}{suffix}"
