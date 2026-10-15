from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.analytics.service import MAX_DAYS, build_report
from app.api.errors import INVALID_REQUEST_RESPONSE
from app.db import get_db_session
from app.staff.models import StaffUser
from app.staff.router import STAFF_RESPONSES, require_staff


class DayCount(BaseModel):
    date: date
    questions: int
    unanswered: int


class QuestionCount(BaseModel):
    question: str
    count: int


class SourceCount(BaseModel):
    faq_id: str
    question: str | None
    count: int


class AnalyticsResponse(BaseModel):
    days: int
    since: date
    questions: int
    sessions: int
    unanswered: int
    per_day: list[DayCount]
    top_questions: list[QuestionCount]
    top_sources: list[SourceCount]
    languages: dict[str, int]
    ratings: dict[str, int]
    down_reasons: dict[str, int]


router = APIRouter(prefix="/staff/analytics", tags=["staff: analytics"])


@router.get(
    "",
    response_model=AnalyticsResponse,
    responses={**STAFF_RESPONSES, **INVALID_REQUEST_RESPONSE},
    summary="What applicants ask (admissions dashboard)",
    description=f"Counts for the last `days` days (today included, Kazakhstan time), at most {MAX_DAYS}: "
    "chat turns are deleted after 30 days. Question texts are redacted; no session ids are returned.",
)
def analytics(
    _: Annotated[StaffUser, Depends(require_staff())],
    session: Annotated[Session, Depends(get_db_session)],
    days: Annotated[int, Query(ge=1, le=MAX_DAYS)] = 7,
) -> AnalyticsResponse:
    return AnalyticsResponse(**asdict(build_report(session, days)))
