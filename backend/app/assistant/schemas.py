from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, StringConstraints, model_validator


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


class AnswerSource(BaseModel):
    """One official source of an answer (contract v2, US10).

    FAQ answers cite FAQ items; catalogue answers cite the program page, with
    `faq_id` and `question` null.
    """

    faq_id: str | None
    question: str | None
    link: str


class Answer(BaseModel):
    """What the answer service returns, before the answer is stored."""

    answer: str
    sources: list[AnswerSource] = []
    # Contract v1 fields, kept for one sprint (Sprint 2) next to `sources`.
    source_link: str | None
    faq_id: str | None
    similarity_score: float | None


class AskResponse(Answer):
    answer_id: str


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class FeedbackRequest(BaseModel):
    answer_id: Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{0,17}$")]
    rating: Literal["up", "down"]
    reason: Literal["outdated", "incorrect", "incomplete", "unclear", "wrong", "other"] | None = None

    @model_validator(mode="after")
    def reason_requires_thumbs_down(self) -> "FeedbackRequest":
        if self.rating == "up" and self.reason is not None:
            raise ValueError("reason is only allowed for thumbs down")
        return self


class FeedbackResponse(BaseModel):
    answer_id: str
    rating: Literal["up", "down"]
    reason: str | None
