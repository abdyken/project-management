from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.catalogue.schemas import ProgramOut
from app.checklist.schemas import ApplicantType, DocumentFormat

Language = Literal["en", "ru", "kk"]
Status = Literal["draft", "submitted", "in_review", "needs_changes", "accepted", "rejected"]
EducationLevel = Literal["school", "college", "bachelor", "master"]


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.split())
    return value or None


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    program_id: str = Field(min_length=1, max_length=64)
    applicant_type: ApplicantType
    language: Language = "en"


class ApplicationFields(BaseModel):
    """The form (ADR 0001). Every field may stay empty in a draft; submit checks completeness."""

    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, max_length=200)
    date_of_birth: date | None = None
    citizenship: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30, pattern=r"^\+?[0-9 ()-]{6,30}$")
    education_level: EducationLevel | None = None
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    exam_total: int | None = Field(default=None, ge=0, le=150)
    consent: bool = False
    language: Language | None = None

    @field_validator("full_name", "citizenship", "phone")
    @classmethod
    def clean(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("date_of_birth")
    @classmethod
    def plausible_birth_date(cls, value: date | None) -> date | None:
        if value is not None and not date(1900, 1, 1) <= value <= date.today():
            raise ValueError("Enter a real date of birth")
        return value


class RequirementOut(BaseModel):
    id: int
    name: str
    format: DocumentFormat
    translation: bool
    notarisation: bool
    deadline: str
    uploaded: bool


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    requirement_id: int | None
    original_name: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime


class ApplicationSummary(BaseModel):
    id: int
    program: ProgramOut
    applicant_type: ApplicantType
    status: Status
    updated_at: datetime
    submitted_at: datetime | None
    documents: int


class ApplicationsOut(BaseModel):
    items: list[ApplicationSummary]
    total: int


class ApplicationOut(BaseModel):
    id: int
    program: ProgramOut
    applicant_type: ApplicantType
    status: Status
    language: Language
    full_name: str | None
    date_of_birth: date | None
    citizenship: str | None
    phone: str | None
    education_level: EducationLevel | None
    graduation_year: int | None
    exam_total: int | None
    consent: bool
    staff_note: str | None
    editable: bool
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    status_changed_at: datetime | None
    requirements: list[RequirementOut]
    documents: list[DocumentOut]
    bytes_used: int
    bytes_limit: int
    # Fields and documents still needed before it can be submitted.
    missing: list[str]


class StaffApplicationSummary(ApplicationSummary):
    applicant_email: str
    full_name: str | None


class StaffApplicationsOut(BaseModel):
    items: list[StaffApplicationSummary]
    total: int


class StaffApplicationOut(ApplicationOut):
    applicant_email: str


class StatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["in_review", "needs_changes", "accepted", "rejected"]
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        return value or None


class StatusLine(BaseModel):
    id: int
    program_id: str
    status: Status
    stage: str
    next_step: str


class StatusAnswerOut(BaseModel):
    answer: str
    items: list[StatusLine]
