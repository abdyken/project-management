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
    tuition_fee: float | None
    application_deadline: date | None
    is_active: bool


class ProgramListResponse(BaseModel):
    total: int
    programs: list[ProgramOut]
