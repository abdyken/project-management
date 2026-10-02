from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import DATABASE_UNAVAILABLE_RESPONSE, INVALID_REQUEST_RESPONSE, ErrorResponse
from app.assistant.feedback import AnswerFeedback
from app.assistant.schemas import AskRequest, AskResponse, FeedbackRequest, FeedbackResponse, SessionId, SuggestionsResponse
from app.assistant.service import AssistantService
from app.assistant.streaming import STREAM_HEADERS, answer_events
from app.assistant.suggestions import suggest
from app.catalogue.service import search_programs
from app.conversation.context import standalone_question
from app.conversation.models import ASSISTANT, USER, ChatTurn
from app.conversation.service import recent_turns, record_answer, record_question
from app.config import Settings, get_settings
from app.db import get_session_factory

router = APIRouter(prefix="/assistant", tags=["assistant"])

ASSISTANT_TIMEOUT = "ASSISTANT_TIMEOUT"
ANSWER_NOT_FOUND = "ANSWER_NOT_FOUND"
ALREADY_RATED = "ALREADY_RATED"

SessionFactory = Callable[[], AbstractContextManager[Session]]


def _answer(open_session: SessionFactory, settings: Settings, body: AskRequest) -> AskResponse:
    """The one answer path behind /ask and /ask/stream: same context, fallbacks and storage."""
    with open_session() as session:
        # US11: answer follow-ups ("and as an international applicant?") in the
        # context of the last turns of this session only.
        history = recent_turns(session, body.session_id)
        question = standalone_question(body.question, history, search_programs(session)) if history else body.question
        answer = AssistantService(session, settings).answer(question, body.session_id)
        sources = [source.model_dump() for source in answer.sources] or None
        record_question(session, body.session_id, body.question)
        answer_turn = record_answer(session, body.session_id, answer.answer, sources)
        return AskResponse(**answer.model_dump(), answer_id=str(answer_turn.id))


async def _answer_in_time(open_session: SessionFactory, settings: Settings, body: AskRequest) -> AskResponse | None:
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


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Answer id is unknown."},
        409: {"model": ErrorResponse, "description": "This answer has already been rated."},
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Rate a stored assistant answer once",
)
def feedback(
    body: FeedbackRequest, open_session: Annotated[SessionFactory, Depends(get_session_factory)]
) -> FeedbackResponse | JSONResponse:
    with open_session() as session:
        answer = session.get(ChatTurn, int(body.answer_id))
        if answer is None or answer.role != ASSISTANT:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(error_code=ANSWER_NOT_FOUND, message="Answer not found.").model_dump(),
            )
        question = session.scalar(
            select(ChatTurn.text)
            .where(ChatTurn.session_id == answer.session_id, ChatTurn.role == USER, ChatTurn.id < answer.id)
            .order_by(ChatTurn.id.desc())
            .limit(1)
        )
        if question is None:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(error_code=ANSWER_NOT_FOUND, message="Answer not found.").model_dump(),
            )
        session.add(
            AnswerFeedback(
                answer_id=answer.id,
                rating=body.rating,
                reason=body.reason,
                session_id=answer.session_id,
                question=question,
                answer=answer.text,
                sources=answer.sources,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return JSONResponse(
                status_code=409,
                content=ErrorResponse(error_code=ALREADY_RATED, message="This answer has already been rated.").model_dump(),
            )
    return FeedbackResponse(answer_id=body.answer_id, rating=body.rating, reason=body.reason)


@router.get(
    "/suggestions",
    response_model=SuggestionsResponse,
    responses={**INVALID_REQUEST_RESPONSE, **DATABASE_UNAVAILABLE_RESPONSE},
    summary="Suggested questions for the chat widget",
)
def suggestions(
    open_session: Annotated[SessionFactory, Depends(get_session_factory)],
    session_id: Annotated[SessionId, Query(description="The chat session id")],
) -> SuggestionsResponse:
    """Four starter questions, or up to three follow-ups once the session has a turn."""
    with open_session() as session:
        return SuggestionsResponse(suggestions=suggest(session, session_id))


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
    return _timeout_response() if answered is None else answered


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
        answer_events(answered, settings.stream_chunk_delay_seconds),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )
