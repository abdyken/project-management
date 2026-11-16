from datetime import timedelta

from fastapi import Request

from app.api.errors import ApiProblem, ErrorResponse
from app.config import get_settings
from app.staff.service import LoginLimiter

TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
TOO_MANY_REQUESTS_MESSAGE = "Too many requests. Please wait a minute and try again."
REQUEST_WINDOW = timedelta(minutes=1)


def client_ip(request: Request) -> str:
    """The visitor's address for rate limits.

    In production Caddy sets X-Forwarded-For to the real client (it ignores the header a
    client sends) and nginx appends Caddy's address, so the first entry is the visitor;
    the socket address would be the nginx container for everyone. Without a proxy
    (tests, local uvicorn) the socket address is used.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RequestRateLimit:
    """Dependency: at most the Settings field `setting` requests per client IP per minute."""

    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.limiter = LoginLimiter(window=REQUEST_WINDOW)

    def __call__(self, request: Request) -> None:
        self.limiter.limit = getattr(get_settings(), self.setting)
        key = client_ip(request)
        if self.limiter.blocked(key):
            raise ApiProblem(429, TOO_MANY_REQUESTS, TOO_MANY_REQUESTS_MESSAGE)
        self.limiter.record_failure(key)


def too_many_requests_response(description: str) -> dict:
    return {
        429: {
            "model": ErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": {"error_code": TOO_MANY_REQUESTS, "message": TOO_MANY_REQUESTS_MESSAGE}
                }
            },
        }
    }


assistant_rate_limit = RequestRateLimit("assistant_requests_per_minute")
recommendations_rate_limit = RequestRateLimit("recommendations_requests_per_minute")
