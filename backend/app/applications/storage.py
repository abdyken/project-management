"""US32: uploaded documents on the uploads volume (ADR 0003).

Files are written in chunks under a random name, recognised by their first bytes and
never held whole in memory. The database keeps everything else.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.api.errors import ApiProblem
from app.config import Settings

logger = logging.getLogger(__name__)

CHUNK = 64 * 1024
# First bytes of the accepted formats: the browser's type and the file name are not trusted.
SIGNATURES = (
    (b"%PDF-", "application/pdf", ".pdf"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
)


@dataclass(frozen=True)
class StoredFile:
    storage_key: str
    size_bytes: int
    sha256: str
    content_type: str


def upload_dir(settings: Settings) -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_path(settings: Settings, storage_key: str) -> Path:
    # Keys are generated here (hex only), so the path cannot leave the uploads directory.
    if not re.fullmatch(r"[0-9a-f]{32}", storage_key):
        raise ValueError("invalid storage key")
    return upload_dir(settings) / storage_key


def safe_name(name: str | None) -> str:
    """The original name for display and download: no folders, control characters or quotes."""
    name = unicodedata.normalize("NFC", (name or "").replace("\\", "/").rsplit("/", 1)[-1])
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C" and ch not in '"<>|*?:')
    name = name.strip(" .")[:255]
    return name or "document"


def _content_type(head: bytes) -> str:
    for signature, content_type, _ in SIGNATURES:
        if head.startswith(signature):
            return content_type
    raise ApiProblem(415, "UNSUPPORTED_FILE_TYPE", "Upload a PDF, JPEG or PNG file.")


def save_upload(source: BinaryIO, settings: Settings, limit_bytes: int) -> StoredFile:
    """Stream `source` to the uploads volume; reject unknown types and files over `limit_bytes`."""
    directory = upload_dir(settings)
    storage_key = secrets.token_hex(16)
    temporary = directory / f".{storage_key}.part"
    digest, size, content_type = hashlib.sha256(), 0, None
    try:
        with temporary.open("xb") as target:
            while chunk := source.read(CHUNK):
                if content_type is None:
                    content_type = _content_type(chunk)
                size += len(chunk)
                if size > limit_bytes:
                    raise ApiProblem(413, "FILE_TOO_LARGE", "The file is too large.")
                digest.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if content_type is None:
            raise ApiProblem(422, "EMPTY_FILE", "The file is empty.")
        temporary.rename(directory / storage_key)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return StoredFile(storage_key, size, digest.hexdigest(), content_type)


def delete_files(settings: Settings, storage_keys: list[str]) -> None:
    """Remove files after their rows are gone; a missing file is not an error."""
    for key in storage_keys:
        try:
            file_path(settings, key).unlink(missing_ok=True)
        except (OSError, ValueError):
            logger.exception("Could not delete an uploaded file; it is no longer referenced.")
