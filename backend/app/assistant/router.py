from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.assistant.schemas import AskRequest
from app.assistant.service import AssistantService
from app.config import get_settings
from app.db import get_db_session

router = APIRouter()


@router.post("/api/assistant/ask")
async def ask(request: Request, session: Annotated[Session, Depends(get_db_session)]) -> JSONResponse:
    settings = get_settings()

    try:
        body = await request.json()
        ask_request = AskRequest(**body)
    except (ValidationError, ValueError, TypeError) as exc:
        return JSONResponse(status_code=400, content={"error_code": _validation_error_code(exc)})

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(AssistantService(session, settings).answer, ask_request.question),
            timeout=settings.assistant_timeout_seconds,
        )
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error_code": "ASSISTANT_TIMEOUT"})

    return JSONResponse(status_code=200, content=response.model_dump())


def _validation_error_code(exc: Exception) -> str:
    message = str(exc)
    if "session_id" in message:
        return "MISSING_SESSION_ID"
    if "question" in message and "at most" in message:
        return "QUESTION_TOO_LONG"
    return "EMPTY_QUESTION"
