from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import DATABASE_UNAVAILABLE_RESPONSE, INVALID_REQUEST_RESPONSE, ErrorResponse
from app.assistant.schemas import AskRequest, AskResponse
from app.assistant.service import AssistantService
from app.config import Settings, get_settings
from app.db import get_session_factory

router = APIRouter(prefix="/assistant", tags=["assistant"])

ASSISTANT_TIMEOUT = "ASSISTANT_TIMEOUT"

SessionFactory = Callable[[], AbstractContextManager[Session]]


def _answer(open_session: SessionFactory, settings: Settings, body: AskRequest) -> AskResponse:
    with open_session() as session:
        return AssistantService(session, settings).answer(body.question, body.session_id)


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        504: {"model": ErrorResponse, "description": "No answer within the time budget."},
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Answer an applicant question from the official FAQ",
)
async def ask(
    body: AskRequest, open_session: Annotated[SessionFactory, Depends(get_session_factory)]
) -> AskResponse | JSONResponse:
    settings = get_settings()
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_answer, open_session, settings, body),
            timeout=settings.assistant_timeout_seconds,
        )
    except TimeoutError:
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                error_code=ASSISTANT_TIMEOUT, message="The assistant did not answer in time. Please try again."
            ).model_dump(),
        )
