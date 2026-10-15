from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import INVALID_REQUEST_RESPONSE, ErrorResponse
from app.db import get_db_session
from app.faq.models import DRAFT, PUBLISHED, RETIRED, FaqRecord
from app.faq.schemas import FaqItemIn, FaqItemOut, FaqListItem, FaqListResponse, FaqStatus
from app.faq.service import (
    categories,
    create_item,
    editor_names,
    get_item,
    languages_of,
    list_items,
    set_status,
    update_item,
)
from app.staff.models import StaffUser
from app.staff.router import STAFF_RESPONSES, require_staff

FAQ_NOT_FOUND = "FAQ_NOT_FOUND"

NOT_FOUND_RESPONSE = {
    404: {
        "model": ErrorResponse,
        "description": "No FAQ item with this id.",
        "content": {"application/json": {"example": {"error_code": FAQ_NOT_FOUND, "message": "FAQ item not found."}}},
    }
}

router = APIRouter(prefix="/staff/faq", tags=["staff: FAQ"])

Staff = Annotated[StaffUser, Depends(require_staff())]
DbSession = Annotated[Session, Depends(get_db_session)]
FaqId = Annotated[str, Path(max_length=32)]


def _not_found() -> JSONResponse:
    return JSONResponse(
        status_code=404, content=ErrorResponse(error_code=FAQ_NOT_FOUND, message="FAQ item not found.").model_dump()
    )


def _out(record: FaqRecord, names: dict[int, str]) -> FaqItemOut:
    return FaqItemOut(
        **FaqItemIn.model_validate(record, from_attributes=True).model_dump(),
        faq_id=record.faq_id,
        status=record.status,
        last_update=record.last_update,
        updated_at=record.updated_at,
        updated_by=names.get(record.updated_by_id) if record.updated_by_id else None,
    )


@router.get("", response_model=FaqListResponse, responses={**STAFF_RESPONSES, **INVALID_REQUEST_RESPONSE}, summary="List FAQ items")
def list_faq(
    _: Staff,
    session: DbSession,
    q: Annotated[str | None, Query(max_length=100, description="Text in the id, question or answer")] = None,
    status: FaqStatus | None = None,
    category: Annotated[str | None, Query(max_length=40)] = None,
) -> FaqListResponse:
    records = list_items(session, q, status, category)
    names = editor_names(session, records)
    return FaqListResponse(
        items=[
            FaqListItem(
                faq_id=record.faq_id,
                status=record.status,
                category=record.category,
                question=record.question,
                languages=languages_of(record),
                last_update=record.last_update,
                updated_at=record.updated_at,
                updated_by=names.get(record.updated_by_id) if record.updated_by_id else None,
            )
            for record in records
        ],
        categories=categories(session),
    )


@router.get("/{faq_id}", response_model=FaqItemOut, responses={**STAFF_RESPONSES, **NOT_FOUND_RESPONSE}, summary="One FAQ item")
def get_faq(faq_id: FaqId, _: Staff, session: DbSession) -> FaqItemOut | JSONResponse:
    record = get_item(session, faq_id)
    if record is None:
        return _not_found()
    return _out(record, editor_names(session, [record]))


@router.post(
    "",
    status_code=201,
    response_model=FaqItemOut,
    responses={**STAFF_RESPONSES, **INVALID_REQUEST_RESPONSE},
    summary="Create an FAQ item as a draft",
    description="The new item gets the next `faq-NNN` id and status `draft`; the assistant uses it only after it is published.",
)
def create_faq(body: FaqItemIn, user: Staff, session: DbSession) -> FaqItemOut:
    record = create_item(session, body, user)
    return _out(record, {user.id: user.name})


@router.put(
    "/{faq_id}",
    response_model=FaqItemOut,
    responses={**STAFF_RESPONSES, **NOT_FOUND_RESPONSE, **INVALID_REQUEST_RESPONSE},
    summary="Change an FAQ item",
    description="A published item is re-indexed at once, so the assistant answers with the new text on the next question.",
)
def update_faq(faq_id: FaqId, body: FaqItemIn, user: Staff, session: DbSession) -> FaqItemOut | JSONResponse:
    record = get_item(session, faq_id)
    if record is None:
        return _not_found()
    return _out(update_item(session, record, body, user), {user.id: user.name})


def _status_endpoint(action: str, status: str, summary: str, description: str):
    @router.post(
        f"/{{faq_id}}/{action}",
        response_model=FaqItemOut,
        responses={**STAFF_RESPONSES, **NOT_FOUND_RESPONSE},
        summary=summary,
        description=description,
        name=f"set_faq_{status}",
    )
    def endpoint(faq_id: FaqId, user: Staff, session: DbSession) -> FaqItemOut | JSONResponse:
        record = get_item(session, faq_id)
        if record is None:
            return _not_found()
        return _out(set_status(session, record, status, user), {user.id: user.name})

    return endpoint


publish_faq = _status_endpoint("publish", PUBLISHED, "Publish an FAQ item", "The assistant starts using the item at once.")
retire_faq = _status_endpoint("retire", RETIRED, "Retire an FAQ item", "The assistant stops using the item at once; it stays in the list as `retired`.")
unpublish_faq = _status_endpoint("unpublish", DRAFT, "Move an FAQ item back to draft", "The assistant stops using the item until it is published again.")
