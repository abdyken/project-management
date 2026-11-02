from fastapi import Request


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
