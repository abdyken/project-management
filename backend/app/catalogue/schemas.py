from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

DegreeLevel = Literal["bachelor", "master", "phd"]


class ProgramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program_id: str
    title: str
    faculty: str
    degree_level: DegreeLevel
    language: str
    tuition_per_ects_kzt: int | None
    tuition_per_ects_usd: int | None
    deadline_local: date | None
    deadline_international: date | None
    source_url: str | None
    is_active: bool


class ProgramListResponse(BaseModel):
    total: int
    programs: list[ProgramOut]
