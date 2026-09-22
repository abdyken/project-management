"""Pydantic models mirroring the contract published in
docs/serdar-ai-tasks/T3.5-chat-api-contract.md (T3.5).

Keep this file and that markdown contract in sync — the markdown is what
gets signed off with Daniyar, this is its executable form.
"""
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


class ErrorResponse(BaseModel):
    error_code: str
