from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import DataError, OperationalError, TimeoutError as PoolTimeoutError

logger = logging.getLogger(__name__)

DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
PROGRAM_NOT_FOUND = "PROGRAM_NOT_FOUND"
INVALID_REQUEST = "INVALID_REQUEST"
RETRY_AFTER_SECONDS = 5


class ErrorResponse(BaseModel):
    error_code: str
    message: str


DATABASE_UNAVAILABLE_RESPONSE = {
    503: {
        "model": ErrorResponse,
        "description": "The database is unreachable. The request can be retried; "
        f"the Retry-After header suggests a delay in seconds (currently {RETRY_AFTER_SECONDS}).",
        "content": {
            "application/json": {
                "example": {
                    "error_code": DATABASE_UNAVAILABLE,
                    "message": "The service is temporarily unavailable. Please try again.",
                }
            }
        },
    }
}

INVALID_REQUEST_RESPONSE = {
    422: {
        "model": ErrorResponse,
        "description": "A parameter or the request body is invalid.",
        "content": {
            "application/json": {
                "example": {"error_code": INVALID_REQUEST, "message": "question: String should have at least 1 character"}
            }
        },
    }
}


async def database_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Database unavailable on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error_code=DATABASE_UNAVAILABLE,
            message="The service is temporarily unavailable. Please try again.",
        ).model_dump(),
        headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
    )


async def invalid_request_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    error = exc.errors()[0]
    field = ".".join(str(part) for part in error["loc"] if part not in ("body", "query", "path"))
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error_code=INVALID_REQUEST, message=f"{field}: {error['msg']}").model_dump(),
    )


async def invalid_data_handler(request: Request, exc: DataError) -> JSONResponse:
    logger.info("Rejected data on %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error_code=INVALID_REQUEST, message="The request contains invalid characters.").model_dump(),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, invalid_request_handler)
    app.add_exception_handler(DataError, invalid_data_handler)
    app.add_exception_handler(OperationalError, database_unavailable_handler)
    app.add_exception_handler(PoolTimeoutError, database_unavailable_handler)
