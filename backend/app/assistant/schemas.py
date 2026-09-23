from __future__ import annotations

from pydantic import BaseModel, Field


class FaqItem(BaseModel):
    faq_id: str
    question: str
    answer: str
    category: str
    source_link: str
    last_update: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    session_id: str = Field(min_length=1)


class AskResponse(BaseModel):
    answer: str
    source_link: str | None
    faq_id: str | None
    similarity_score: float

