from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, StringConstraints


def _no_nul(value: str) -> str:
    if chr(0) in value:
        raise ValueError("must not contain NUL characters")
    return value


Question = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
    AfterValidator(_no_nul),
]
SessionId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class FaqItem(BaseModel):
    faq_id: str
    question: str
    answer: str
    category: str
    source_link: str
    last_update: str
    degrees: list[str] = []
    applicant_types: list[str] = []


class AskRequest(BaseModel):
    question: Question
    session_id: SessionId


class AskResponse(BaseModel):
    answer: str
    source_link: str | None
    faq_id: str | None
    similarity_score: float | None
