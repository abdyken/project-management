from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

FaqStatus = Literal["draft", "published", "retired"]
DEGREES = ("bachelor", "master", "phd")
APPLICANT_TYPES = ("local", "international")
TRANSLATED = ("ru", "kk")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


class FaqItemIn(BaseModel):
    """An FAQ item as the staff editor sends it. English is required; a Russian or
    Kazakh version is either complete (question, answer and its official page) or empty."""

    category: str = Field(min_length=2, max_length=40, pattern=r"^[a-z][a-z-]*$")
    question: str = Field(min_length=5, max_length=500)
    answer: str = Field(min_length=5, max_length=5000)
    source_link: str = Field(max_length=500, pattern=r"^https://")
    evidence: str | None = Field(default=None, max_length=5000)
    question_ru: str | None = Field(default=None, max_length=500)
    answer_ru: str | None = Field(default=None, max_length=5000)
    source_link_ru: str | None = Field(default=None, max_length=500, pattern=r"^https://")
    evidence_ru: str | None = Field(default=None, max_length=5000)
    question_kk: str | None = Field(default=None, max_length=500)
    answer_kk: str | None = Field(default=None, max_length=5000)
    source_link_kk: str | None = Field(default=None, max_length=500, pattern=r"^https://")
    evidence_kk: str | None = Field(default=None, max_length=5000)
    degrees: list[Literal["bachelor", "master", "phd"]] = []
    applicant_types: list[Literal["local", "international"]] = []

    @field_validator("category", "question", "answer", "source_link", mode="before")
    @classmethod
    def _strip_required(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator(
        "evidence", "question_ru", "answer_ru", "source_link_ru", "evidence_ru",
        "question_kk", "answer_kk", "source_link_kk", "evidence_kk",
        mode="before",
    )
    @classmethod
    def _strip_optional(cls, value: object) -> object:
        return _clean(value) if isinstance(value, str) or value is None else value

    @model_validator(mode="after")
    def _translations_complete(self) -> FaqItemIn:
        for language in TRANSLATED:
            parts = [getattr(self, f"{field}_{language}") for field in ("question", "answer", "source_link")]
            if any(parts) and not all(parts):
                raise ValueError(f"the {language} version needs a question, an answer and a source link, or none of them")
        self.degrees = list(dict.fromkeys(self.degrees))
        self.applicant_types = list(dict.fromkeys(self.applicant_types))
        return self


class FaqItemOut(FaqItemIn):
    faq_id: str
    status: FaqStatus
    last_update: str
    updated_at: datetime
    updated_by: str | None


class FaqListItem(BaseModel):
    faq_id: str
    status: FaqStatus
    category: str
    question: str
    languages: list[Literal["en", "ru", "kk"]]
    last_update: str
    updated_at: datetime
    updated_by: str | None


class FaqListResponse(BaseModel):
    items: list[FaqListItem]
    categories: list[str]
