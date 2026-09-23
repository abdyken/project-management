from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, StringConstraints

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
SessionId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class FaqItem(BaseModel):
    faq_id: str
    question: str
    answer: str
    category: str
    source_link: str
    last_update: str


class AskRequest(BaseModel):
    question: Question
    session_id: SessionId


class AskResponse(BaseModel):
    answer: str
    source_link: str | None
    faq_id: str | None
    similarity_score: float | None
