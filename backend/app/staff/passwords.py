"""Password hashing with the standard library's scrypt, so no new dependency is needed."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

# n=2**14, r=8 uses 16 MB per hash: fine on the 1 GB VM for a handful of staff logins.
_N, _R, _P = 2**14, 8, 1
_KEY_LENGTH = 32
MIN_PASSWORD_LENGTH = 10


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=_KEY_LENGTH)


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must have at least {MIN_PASSWORD_LENGTH} characters")
    salt = secrets.token_bytes(16)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(_derive(password, salt, _N, _R, _P))}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = stored.split("$")
        if scheme != "scrypt":
            return False
        actual = _derive(password, base64.b64decode(salt), int(n), int(r), int(p))
    except ValueError:
        return False
    return hmac.compare_digest(actual, base64.b64decode(expected))


# Checked when the e-mail is unknown, so a wrong e-mail takes as long as a wrong password.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
