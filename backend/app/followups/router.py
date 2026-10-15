from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.errors import INVALID_REQUEST_RESPONSE, ErrorResponse
from app.assistant.language import detect_language
from app.db import get_db_session
from app.faq.models import PUBLISHED
from app.faq.service import get_item
from app.followups.inbox import group_unanswered, rows_of_group
from app.followups.models import ANSWERED, DISMISSED
from app.staff.models import StaffUser
from app.staff.router import STAFF_RESPONSES, require_staff

GROUP_NOT_FOUND = "GROUP_NOT_FOUND"
FAQ_NOT_PUBLISHED = "FAQ_NOT_PUBLISHED"
MAX_DAYS = 90

InboxStatus = Literal["new", "answered", "dismissed"]


class InboxGroup(BaseModel):
    key: str = Field(description="Normalized question; send it back to dismiss or answer the group")
    question: str
    count: int
    language: Literal["en", "ru", "kk"]
    best_score: float | None
    first_asked: datetime
    last_asked: datetime
    faq_id: str | None


class InboxResponse(BaseModel):
    items: list[InboxGroup]
    total_asks: int


class GroupRequest(BaseModel):
    key: str = Field(min_length=1, max_length=1000)


class AnswerRequest(GroupRequest):
    faq_id: str = Field(min_length=1, max_length=32)


class HandledResponse(BaseModel):
    key: str
    status: InboxStatus
    updated: int = Field(description="Questions of the group that changed status")


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=ErrorResponse(error_code=code, message=message).model_dump())


GROUP_NOT_FOUND_RESPONSE = {
    404: {
        "model": ErrorResponse,
        "description": "No new question in this group (already handled, or an unknown key).",
        "content": {"application/json": {"example": {"error_code": GROUP_NOT_FOUND, "message": "No new question in this group."}}},
    }
}

router = APIRouter(prefix="/staff/inbox", tags=["staff: inbox"])

Staff = Annotated[StaffUser, Depends(require_staff())]
DbSession = Annotated[Session, Depends(get_db_session)]


@router.get(
    "",
    response_model=InboxResponse,
    responses={**STAFF_RESPONSES, **INVALID_REQUEST_RESPONSE},
    summary="Questions the assistant could not answer, grouped",
    description="Questions that differ only in case, spacing or punctuation are one group, most asked first. "
    "E-mail addresses and phone numbers are redacted; session ids are never returned.",
)
def inbox(
    _: Staff,
    session: DbSession,
    status: InboxStatus = "new",
    days: Annotated[int, Query(ge=1, le=MAX_DAYS)] = 30,
) -> InboxResponse:
    groups = group_unanswered(session, days, status=status)
    return InboxResponse(
        items=[
            InboxGroup(
                key=group.key,
                question=group.question,
                count=group.count,
                language=detect_language(group.question),
                best_score=group.best_score,
                first_asked=group.first_asked,
                last_asked=group.last_asked,
                faq_id=group.faq_id,
            )
            for group in groups
        ],
        total_asks=sum(group.count for group in groups),
    )


def _handle(session: Session, key: str, status: str, user: StaffUser, faq_id: str | None = None) -> int:
    rows = rows_of_group(session, key)
    now = datetime.now(timezone.utc)
    for row in rows:
        row.status = status
        row.faq_id = faq_id
        row.handled_by_id = user.id
        row.handled_at = now
    session.commit()
    return len(rows)


@router.post(
    "/dismiss",
    response_model=HandledResponse,
    responses={**STAFF_RESPONSES, **GROUP_NOT_FOUND_RESPONSE, **INVALID_REQUEST_RESPONSE},
    summary="Dismiss a group (not an admissions question, spam, already answered elsewhere)",
)
def dismiss(body: GroupRequest, user: Staff, session: DbSession) -> HandledResponse | JSONResponse:
    updated = _handle(session, body.key, DISMISSED, user)
    if not updated:
        return _error(404, GROUP_NOT_FOUND, "No new question in this group.")
    return HandledResponse(key=body.key, status=DISMISSED, updated=updated)


@router.post(
    "/answer",
    response_model=HandledResponse,
    responses={
        **STAFF_RESPONSES,
        **GROUP_NOT_FOUND_RESPONSE,
        **INVALID_REQUEST_RESPONSE,
        409: {
            "model": ErrorResponse,
            "description": "The FAQ item does not exist or is not published yet.",
            "content": {"application/json": {"example": {"error_code": FAQ_NOT_PUBLISHED, "message": "Publish the FAQ item first."}}},
        },
    },
    summary="Mark a group as answered by a published FAQ item",
)
def answer(body: AnswerRequest, user: Staff, session: DbSession) -> HandledResponse | JSONResponse:
    item = get_item(session, body.faq_id)
    if item is None or item.status != PUBLISHED:
        return _error(409, FAQ_NOT_PUBLISHED, "Publish the FAQ item first.")
    updated = _handle(session, body.key, ANSWERED, user, faq_id=body.faq_id)
    if not updated:
        return _error(404, GROUP_NOT_FOUND, "No new question in this group.")
    return HandledResponse(key=body.key, status=ANSWERED, updated=updated)

