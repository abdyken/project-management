from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.errors import DATABASE_UNAVAILABLE_RESPONSE, INVALID_REQUEST_RESPONSE, ErrorResponse
from app.config import get_settings
from app.db import get_db_session
from app.staff.models import ADMIN, StaffUser
from app.staff.schemas import LoginRequest, StaffUserListItem, StaffUserListResponse, StaffUserOut
from app.staff.service import authenticate, end_session, list_users, login_limiter, normalize_email, start_session, user_for_token

COOKIE_NAME = "staff_session"
# The cookie is sent only to the staff API, never with public catalogue or chat requests.
COOKIE_PATH = "/api/staff"

NOT_LOGGED_IN = "NOT_LOGGED_IN"
FORBIDDEN = "FORBIDDEN"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"


class StaffAuthError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


async def staff_auth_error_handler(_: Request, exc: StaffAuthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error_code=exc.error_code, message=exc.message).model_dump(),
    )


def register_staff_error_handler(app: FastAPI) -> None:
    app.add_exception_handler(StaffAuthError, staff_auth_error_handler)


def _error_example(status: int, code: str, message: str, description: str) -> dict:
    return {
        status: {
            "model": ErrorResponse,
            "description": description,
            "content": {"application/json": {"example": {"error_code": code, "message": message}}},
        }
    }


NOT_LOGGED_IN_RESPONSE = _error_example(
    401, NOT_LOGGED_IN, "Please log in.", "No staff session cookie, or the session expired or was logged out."
)
FORBIDDEN_RESPONSE = _error_example(403, FORBIDDEN, "This page is for administrators only.", "The role is not allowed.")
STAFF_RESPONSES = {**NOT_LOGGED_IN_RESPONSE, **DATABASE_UNAVAILABLE_RESPONSE}


def current_staff(
    session: Annotated[Session, Depends(get_db_session)],
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME, include_in_schema=False)] = None,
) -> StaffUser:
    user = user_for_token(session, token)
    if user is None:
        raise StaffAuthError(401, NOT_LOGGED_IN, "Please log in.")
    return user


def require_staff(role: str | None = None):
    """Dependency for every /api/staff endpoint: 401 without a valid session, and
    403 when `role` is given and the user has another role."""

    def dependency(user: Annotated[StaffUser, Depends(current_staff)]) -> StaffUser:
        if role is not None and user.role != role:
            raise StaffAuthError(403, FORBIDDEN, "This page is for administrators only.")
        return user

    return dependency


def _client_ip(request: Request) -> str:
    # Caddy sets X-Forwarded-For to the real client and nginx appends Caddy's address,
    # so the first entry is the client. Without a proxy (tests) the socket address is used.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _user_out(user: StaffUser) -> StaffUserOut:
    return StaffUserOut(id=user.id, email=user.email, name=user.name, role=user.role)


router = APIRouter(prefix="/staff", tags=["staff"])


@router.post(
    "/login",
    response_model=StaffUserOut,
    responses={
        **_error_example(401, INVALID_CREDENTIALS, "Wrong e-mail or password.", "Unknown e-mail, wrong password or a deactivated account."),
        **_error_example(
            429,
            TOO_MANY_ATTEMPTS,
            "Too many failed logins. Try again in 15 minutes.",
            "Five failed logins in 15 minutes for this account or from this address.",
        ),
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Log in to the staff area",
    description="Sets the HttpOnly `staff_session` cookie (path `/api/staff`) for 8 hours.",
)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> StaffUserOut:
    keys = (f"email:{normalize_email(body.email)}", f"ip:{_client_ip(request)}")
    if login_limiter.blocked(*keys):
        raise StaffAuthError(429, TOO_MANY_ATTEMPTS, "Too many failed logins. Try again in 15 minutes.")
    user = authenticate(session, body.email, body.password)
    if user is None:
        login_limiter.record_failure(*keys)
        raise StaffAuthError(401, INVALID_CREDENTIALS, "Wrong e-mail or password.")
    login_limiter.reset(keys[0])
    settings = get_settings()
    lifetime = timedelta(hours=settings.staff_session_hours)
    token = start_session(session, user, lifetime)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(lifetime.total_seconds()),
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.staff_cookie_secure,
        samesite="strict",
    )
    return _user_out(user)


@router.post("/logout", status_code=204, responses=DATABASE_UNAVAILABLE_RESPONSE, summary="Log out")
def logout(
    session: Annotated[Session, Depends(get_db_session)],
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME, include_in_schema=False)] = None,
) -> Response:
    end_session(session, token)
    response = Response(status_code=204)
    response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH)
    return response


@router.get("/me", response_model=StaffUserOut, responses=STAFF_RESPONSES, summary="The logged-in staff user")
def me(user: Annotated[StaffUser, Depends(require_staff())]) -> StaffUserOut:
    return _user_out(user)


@router.get(
    "/users",
    response_model=StaffUserListResponse,
    responses={**STAFF_RESPONSES, **FORBIDDEN_RESPONSE},
    summary="Staff accounts (administrators only)",
    description="Accounts are added and deactivated with `scripts/create_staff_user.py`.",
)
def users(
    _: Annotated[StaffUser, Depends(require_staff(ADMIN))],
    session: Annotated[Session, Depends(get_db_session)],
) -> StaffUserListResponse:
    return StaffUserListResponse(
        items=[
            StaffUserListItem(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                active=user.active,
                last_login_at=user.last_login_at,
            )
            for user in list_users(session)
        ]
    )
