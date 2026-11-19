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
import shutil
import time
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


def download_name(name: str | None, content_type: str) -> str:
    """The name staff and the applicant download: always the detected type's extension, so a
    PDF named "Diploma.bat" cannot be started by a double click (ADR 0003)."""
    stem = safe_name(name)
    extension = next(ext for _, kind, ext in SIGNATURES if kind == content_type)
    if "." in stem:
        stem = stem.rsplit(".", 1)[0].rstrip(" .") or "document"
    return f"{stem[: 255 - len(extension)]}{extension}"


def ensure_free_space(settings: Settings) -> None:
    """Refuse uploads before they can fill the disk the database shares."""
    free = shutil.disk_usage(upload_dir(settings)).free
    if free < settings.upload_min_free_bytes:
        logger.error("Uploads paused: %d MB free on the uploads volume.", free // (1024 * 1024))
        raise ApiProblem(507, "UPLOADS_PAUSED", "Uploads are paused. Please try again later.")


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


def sweep_orphans(settings: Settings, known_keys: set[str], older_than_seconds: int = 3600) -> int:
    """Delete files no document refers to (crash between write and commit, failed deletes,
    leftover .part files). Recent files are skipped: their upload may still be committing."""
    directory = upload_dir(settings)
    cutoff = time.time() - older_than_seconds
    removed = 0
    for path in directory.iterdir():
        key = path.name.removeprefix(".").removesuffix(".part")
        if path.name in known_keys or not path.is_file() or path.stat().st_mtime > cutoff:
            continue
        if path.name.endswith(".part") or re.fullmatch(r"[0-9a-f]{32}", key):
            path.unlink(missing_ok=True)
            removed += 1
    if removed:
        logger.warning("Removed %d orphaned upload file(s).", removed)
    return removed
