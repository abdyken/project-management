from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.errors import DATABASE_UNAVAILABLE_RESPONSE, INVALID_REQUEST_RESPONSE, ErrorResponse
from app.assistant.schemas import AskRequest, AskResponse
from app.assistant.service import AssistantService
from app.assistant.streaming import STREAM_HEADERS, answer_events
from app.catalogue.service import search_programs
from app.conversation.context import standalone_question
from app.conversation.service import recent_turns, record_answer, record_question
from app.config import Settings, get_settings
from app.db import get_session_factory

router = APIRouter(prefix="/assistant", tags=["assistant"])

ASSISTANT_TIMEOUT = "ASSISTANT_TIMEOUT"

SessionFactory = Callable[[], AbstractContextManager[Session]]


@dataclass(frozen=True)
class _Answered:
    response: AskResponse
    answer_id: str
    sources: list[dict[str, Any]] | None


def _answer(open_session: SessionFactory, settings: Settings, body: AskRequest) -> _Answered:
    """The one answer path behind /ask and /ask/stream: same context, fallbacks and storage."""
    with open_session() as session:
        # US11: answer follow-ups ("and as an international applicant?") in the
        # context of the last turns of this session only.
        history = recent_turns(session, body.session_id)
        question = standalone_question(body.question, history, search_programs(session)) if history else body.question
        response = AssistantService(session, settings).answer(question, body.session_id)
        sources = _sources(response)
        record_question(session, body.session_id, body.question)
        answer_turn = record_answer(session, body.session_id, response.answer, sources)
        return _Answered(response, str(answer_turn.id), sources)


async def _answer_in_time(open_session: SessionFactory, settings: Settings, body: AskRequest) -> _Answered | None:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_answer, open_session, settings, body),
            timeout=settings.assistant_timeout_seconds,
        )
    except TimeoutError:
        return None


def _timeout_response() -> JSONResponse:
    return JSONResponse(
        status_code=504,
        content=ErrorResponse(
            error_code=ASSISTANT_TIMEOUT, message="The assistant did not answer in time. Please try again."
        ).model_dump(),
    )


def _sources(response: AskResponse) -> list[dict[str, str]] | None:
    if response.faq_id is None and response.source_link is None:
        return None
    return [{"faq_id": response.faq_id, "link": response.source_link}]


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
    answered = await _answer_in_time(open_session, get_settings(), body)
    return _timeout_response() if answered is None else answered.response


@router.post(
    "/ask/stream",
    response_class=StreamingResponse,
    response_model=None,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-sent events: `chunk` events with the answer text, then one `done` event "
            "with answer_id and sources. See docs/api/assistant-stream.md.",
        },
        504: {"model": ErrorResponse, "description": "No answer within the time budget."},
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Answer an applicant question as a stream of server-sent events",
)
async def ask_stream(
    body: AskRequest, open_session: Annotated[SessionFactory, Depends(get_session_factory)]
) -> StreamingResponse | JSONResponse:
    settings = get_settings()
    answered = await _answer_in_time(open_session, settings, body)
    if answered is None:
        return _timeout_response()
    return StreamingResponse(
        answer_events(answered.response, answered.answer_id, answered.sources, settings.stream_chunk_delay_seconds),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )
