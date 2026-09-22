"""T3.6 dependency — program catalogue lookup.

Used to resolve "which documents do I need for <program>" questions to a
concrete program_id. Talks to the real ``/api/programs`` endpoint (T1.3,
Dinmukhamed) once it is deployed; until then, falls back to a local sample
fixture so T3.6 can be developed and tested independently.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import httpx
from pydantic import BaseModel

from app.config import Settings


class Program(BaseModel):
    program_id: str
    title: str
    faculty: str
    degree_level: str
    language: str
    is_active: bool


class CatalogClient(ABC):
    @abstractmethod
    def list_programs(self) -> list[Program]: ...


class FileCatalogClient(CatalogClient):
    """Stand-in for T1.3 until the real catalogue API is deployed."""

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def list_programs(self) -> list[Program]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [Program(**item) for item in raw]


class HttpCatalogClient(CatalogClient):
    """Real client for T1.3's GET /api/programs."""

    def __init__(self, base_url: str, timeout: float = 4.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def list_programs(self) -> list[Program]:
        response = httpx.get(f"{self._base_url}/api/programs", timeout=self._timeout)
        response.raise_for_status()
        data = response.json()
        items = data["programs"] if isinstance(data, dict) and "programs" in data else data
        return [Program(**item) for item in items]


def get_catalog_client(settings: Settings) -> CatalogClient:
    if settings.catalog_api_url:
        return HttpCatalogClient(settings.catalog_api_url, timeout=settings.assistant_timeout_seconds)
    return FileCatalogClient(Path(settings.faq_data_path).parent / "programs_sample.json")
