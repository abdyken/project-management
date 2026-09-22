"""T3.6 dependency — document checklist lookup.

Talks to the real checklist endpoint (T4.2/T4.3, Nurmek) once it is
deployed; until then, falls back to a local sample fixture — including the
T4.3 "missing data" warning shape — so T3.6 can be developed and tested
independently.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import httpx
from pydantic import BaseModel

from app.config import Settings


class DocumentRequirement(BaseModel):
    name: str
    format: str
    translation: bool
    notarisation: bool
    deadline: str


class ChecklistResult(BaseModel):
    items: list[DocumentRequirement]
    warning: str | None = None


class ChecklistClient(ABC):
    @abstractmethod
    def get_checklist(self, program_id: str, applicant_type: str) -> ChecklistResult: ...


class FileChecklistClient(ChecklistClient):
    """Stand-in for T4.2/T4.3 until the real checklist API is deployed."""

    def __init__(self, path: str | Path):
        self._data = json.loads(Path(path).read_text(encoding="utf-8"))

    def get_checklist(self, program_id: str, applicant_type: str) -> ChecklistResult:
        program_entry = self._data.get(program_id)
        if program_entry is None or applicant_type not in program_entry:
            return ChecklistResult(
                items=[],
                warning="No document requirements have been recorded for this program yet.",
            )
        entry = program_entry[applicant_type]
        return ChecklistResult(
            items=[
                DocumentRequirement(
                    name=document["name"],
                    format=document["original_or_copy"],
                    translation=document["translation_required"],
                    notarisation=document["notarisation_required"],
                    deadline=document["deadline"],
                )
                for document in entry["documents"]
            ],
            warning=entry.get("warning"),
        )


class HttpChecklistClient(ChecklistClient):
    """Real client for T4.2's GET /api/programs/{id}/checklist."""

    def __init__(self, base_url: str, timeout: float = 4.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def get_checklist(self, program_id: str, applicant_type: str) -> ChecklistResult:
        response = httpx.get(
            f"{self._base_url}/api/programs/{program_id}/checklist",
            params={"applicant_type": applicant_type},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return ChecklistResult(**response.json())


class DbChecklistClient(ChecklistClient):
    """Reads the same document requirements the checklist API serves."""

    def __init__(self, settings: Settings):
        self._settings = settings

    def get_checklist(self, program_id: str, applicant_type: str) -> ChecklistResult:
        from app.checklist.router import MISSING_REQUIREMENTS_WARNING
        from app.checklist.service import get_requirements
        from app.db import get_session

        with get_session(self._settings) as session:
            requirements = get_requirements(session, program_id, applicant_type)

        if not requirements:
            return ChecklistResult(items=[], warning=MISSING_REQUIREMENTS_WARNING)

        return ChecklistResult(
            items=[
                DocumentRequirement(
                    name=requirement.name,
                    format=requirement.document_format,
                    translation=requirement.translation_required,
                    notarisation=requirement.notarisation_required,
                    deadline=requirement.deadline,
                )
                for requirement in requirements
            ]
        )


def get_checklist_client(settings: Settings) -> ChecklistClient:
    url = settings.checklist_api_url.strip()
    if url.lower() in {"db", "database", "internal"}:
        return DbChecklistClient(settings)
    if url:
        return HttpChecklistClient(url, timeout=settings.assistant_timeout_seconds)
    return FileChecklistClient(Path(settings.faq_data_path).parent / "checklist_sample.json")
