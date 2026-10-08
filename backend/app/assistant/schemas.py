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


Language = Literal["en", "ru", "kk"]
TRANSLATED = ("ru", "kk")


class FaqItem(BaseModel):
    faq_id: str
    question: str
    answer: str
    category: str
    source_link: str
    last_update: str
    degrees: list[str] = []
    applicant_types: list[str] = []
    question_ru: str | None = None
    answer_ru: str | None = None
    source_link_ru: str | None = None
    question_kk: str | None = None
    answer_kk: str | None = None
    source_link_kk: str | None = None

    def has(self, language: str) -> bool:
        return language == "en" or bool(getattr(self, f"answer_{language}", None))

    def localized(self, language: str) -> FaqItem:
        if language == "en" or not self.has(language):
            return self
        return self.model_copy(
            update={
                "question": getattr(self, f"question_{language}"),
                "answer": getattr(self, f"answer_{language}"),
                "source_link": getattr(self, f"source_link_{language}"),
            }
        )

    def translations(self) -> dict[str, dict[str, str]]:
        return {
            language: {key: getattr(self, f"{key}_{language}") for key in ("question", "answer", "source_link")}
            for language in TRANSLATED
            if self.has(language)
        }

    def texts(self) -> dict[str, str]:
        texts = {}
        for language in ("en", *TRANSLATED):
            if self.has(language):
                item = self.localized(language)
                texts[language] = f"{item.question} {item.answer}"
        return texts


class AskRequest(BaseModel):
    question: Question
    session_id: SessionId


class AnswerSource(BaseModel):
    faq_id: str | None
    question: str | None
    link: str
    title: str | None = None

    @classmethod
    def from_faq(cls, item: FaqItem) -> "AnswerSource":
        return cls(faq_id=item.faq_id, question=item.question, link=item.source_link, title=item.question)


class Answer(BaseModel):
    answer: str
    sources: list[AnswerSource] = []
    source_link: str | None
    faq_id: str | None
    similarity_score: float | None


class AskResponse(BaseModel):
    answer: str
    sources: list[AnswerSource]
    answer_id: str


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class FeedbackRequest(BaseModel):
    answer_id: Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{0,17}$")]
    session_id: SessionId
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
