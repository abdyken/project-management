"""T3.3 / T3.5 — POST /api/assistant/ask.

HTTP wrapper around AssistantService, enforcing exactly the contract in
docs/serdar-ai-tasks/T3.5-chat-api-contract.md:
  - 400 on invalid input (empty question / missing session_id / too long)
  - 503 when the LLM/embedding provider is unavailable
  - 504 when the internal timeout budget is exceeded
  - 200 otherwise, including the below-threshold fallback (T3.4), which
    uses the same response shape so the front-end needs no special case.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.assistant.catalog_client import get_catalog_client
from app.assistant.checklist_client import get_checklist_client
from app.assistant.index_factory import load_retrieval_index
from app.assistant.providers import ProviderError, get_embedding_provider
from app.assistant.schemas import AskRequest, AskResponse
from app.assistant.service import AssistantService
from app.config import Settings, get_settings

router = APIRouter()

_service_instance: AssistantService | None = None


def get_assistant_service(settings: Settings | None = None) -> AssistantService:
    global _service_instance
    if _service_instance is None:
        settings = settings or get_settings()
        _service_instance = AssistantService(
            settings=settings,
            index=load_retrieval_index(settings),
            embedder=get_embedding_provider(settings),
            catalog_client=get_catalog_client(settings),
            checklist_client=get_checklist_client(settings),
        )
    return _service_instance


def reset_assistant_service_cache() -> None:
    """Test helper — clears the singleton so a fresh service (e.g. pointing
    at a temp FAQ index) is built on next use."""
    global _service_instance
    _service_instance = None


@router.post("/api/assistant/ask")
async def ask(request: Request) -> JSONResponse:
    settings = get_settings()

    try:
        body = await request.json()
        ask_request = AskRequest(**body)
    except (ValidationError, ValueError, TypeError) as exc:
        return JSONResponse(status_code=400, content={"error_code": _validation_error_code(exc)})

    service = get_assistant_service(settings)

    try:
        response: AskResponse = await asyncio.wait_for(
            asyncio.to_thread(service.answer, ask_request.question, ask_request.session_id),
            timeout=settings.assistant_timeout_seconds,
        )
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error_code": "ASSISTANT_TIMEOUT"})
    except ProviderError:
        return JSONResponse(status_code=503, content={"error_code": "ASSISTANT_UNAVAILABLE"})

    return JSONResponse(status_code=200, content=response.model_dump())


def _validation_error_code(exc: Exception) -> str:
    message = str(exc)
    if "session_id" in message:
        return "MISSING_SESSION_ID"
    if "question" in message and "at most" in message:
        return "QUESTION_TOO_LONG"
    return "EMPTY_QUESTION"
