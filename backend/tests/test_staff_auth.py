"""US19 staff login: sessions, expiry, logout, roles, failed-login limit, deactivated accounts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.db import get_db_session
from app.main import app
from app.staff.models import StaffSession, StaffUser
from app.staff.passwords import hash_password, verify_password
from app.staff.service import LoginLimiter, create_user, login_limiter, set_active, set_password
from scripts.create_staff_user import main as manage_users

PASSWORD = "correct horse battery"


@pytest.fixture(autouse=True)
def _fresh_limiter():
    login_limiter.reset(*list(login_limiter._failures))
    yield
    login_limiter.reset(*list(login_limiter._failures))


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        # https, because the session cookie is Secure.
        yield TestClient(app, base_url="https://testserver")
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def officer(db_session):
    return create_user(db_session, "Officer@SDU.edu.kz", "Aigerim", "officer", PASSWORD)


@pytest.fixture
def admin(db_session):
    return create_user(db_session, "admin@sdu.edu.kz", "Admin", "admin", PASSWORD)


def _login(client, email="officer@sdu.edu.kz", password=PASSWORD):
    return client.post("/api/staff/login", json={"email": email, "password": password})


def test_password_hash_is_salted_and_checked():
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second and PASSWORD not in first
    assert verify_password(PASSWORD, first)
    assert not verify_password("wrong password!", first)
    assert not verify_password(PASSWORD, "not-a-hash")
    with pytest.raises(ValueError):
        hash_password("short")


def test_login_sets_http_only_cookie_and_me_returns_the_user(client, officer):
    response = _login(client, email="  OFFICER@sdu.edu.kz ")

    assert response.status_code == 200
    assert response.json() == {"id": officer.id, "email": "officer@sdu.edu.kz", "name": "Aigerim", "role": "officer"}
    cookie = response.headers["set-cookie"].lower()
    for part in ("staff_session=", "httponly", "secure", "samesite=strict", "path=/api/staff", "max-age=28800"):
        assert part in cookie
    assert client.get("/api/staff/me").json()["email"] == "officer@sdu.edu.kz"
    assert officer.last_login_at is not None


def test_only_the_token_hash_is_stored(client, officer, db_session):
    _login(client)
    token = client.cookies.get("staff_session")
    stored = db_session.scalars(select(StaffSession.token_hash)).all()
    assert len(stored) == 1 and token not in stored


def test_staff_endpoints_need_a_session(client, officer):
    for path in ("/api/staff/me", "/api/staff/users"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["error_code"] == "NOT_LOGGED_IN"
    client.cookies.set("staff_session", "made-up-token", domain="testserver.local", path="/api/staff")
    assert client.get("/api/staff/me").status_code == 401


def test_wrong_password_and_unknown_email_get_the_same_answer(client, officer):
    wrong = _login(client, password="not the password")
    unknown = _login(client, email="nobody@sdu.edu.kz")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"error_code": "INVALID_CREDENTIALS", "message": "Wrong e-mail or password."}
    assert "set-cookie" not in wrong.headers


def test_logout_ends_the_session(client, officer):
    _login(client)
    token = client.cookies.get("staff_session")
    client.cookies.clear()
    client.cookies.set("staff_session", token, domain="testserver.local", path="/api/staff")
    assert client.get("/api/staff/me").status_code == 200

    response = client.post("/api/staff/logout")

    assert response.status_code == 204
    assert 'staff_session=""' in response.headers["set-cookie"] or "max-age=0" in response.headers["set-cookie"].lower()
    client.cookies.set("staff_session", token, domain="testserver.local", path="/api/staff")
    assert client.get("/api/staff/me").status_code == 401


def test_expired_session_is_rejected(client, officer, db_session):
    _login(client)
    db_session.execute(update(StaffSession).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
    assert client.get("/api/staff/me").status_code == 401


def test_officer_cannot_open_admin_endpoint_but_admin_can(client, officer, admin):
    _login(client)
    forbidden = client.get("/api/staff/users")
    assert forbidden.status_code == 403
    assert forbidden.json()["error_code"] == "FORBIDDEN"

    _login(client, email="admin@sdu.edu.kz")
    listed = client.get("/api/staff/users")
    assert listed.status_code == 200
    assert [item["email"] for item in listed.json()["items"]] == ["admin@sdu.edu.kz", "officer@sdu.edu.kz"]
    assert "password_hash" not in listed.text


def test_sixth_failed_login_in_15_minutes_is_blocked_even_with_the_right_password(client, officer):
    for _ in range(5):
        assert _login(client, password="not the password").status_code == 401

    blocked = _login(client)

    assert blocked.status_code == 429
    assert blocked.json()["error_code"] == "TOO_MANY_ATTEMPTS"


def test_limit_counts_per_client_ip(client, officer, admin):
    for index in range(5):
        _login(client, email=f"guess{index}@sdu.edu.kz")
    assert _login(client, email="admin@sdu.edu.kz").status_code == 429
    other_ip = client.post(
        "/api/staff/login",
        json={"email": "admin@sdu.edu.kz", "password": PASSWORD},
        headers={"X-Forwarded-For": "203.0.113.7, 172.18.0.5"},
    )
    assert other_ip.status_code == 200


def test_limiter_window_slides():
    limiter = LoginLimiter(limit=2, window=timedelta(minutes=15))
    start = datetime(2026, 10, 16, 9, 0, tzinfo=timezone.utc)
    limiter.record_failure("k", now=start)
    limiter.record_failure("k", now=start + timedelta(minutes=1))
    assert limiter.blocked("k", now=start + timedelta(minutes=14))
    assert not limiter.blocked("k", now=start + timedelta(minutes=15))


def test_deactivating_or_resetting_the_password_logs_out(client, officer, db_session):
    _login(client)
    set_active(db_session, "officer@sdu.edu.kz", False)
    assert client.get("/api/staff/me").status_code == 401
    assert _login(client).status_code == 401

    set_active(db_session, "officer@sdu.edu.kz", True)
    assert _login(client).status_code == 200
    set_password(db_session, "officer@sdu.edu.kz", "a brand new password")
    assert client.get("/api/staff/me").status_code == 401


def test_script_creates_lists_and_rejects_duplicates(db_session, monkeypatch, capsys):
    monkeypatch.setattr("scripts.create_staff_user.get_session", lambda _: _NoClose(db_session))
    monkeypatch.setattr("sys.stdin", _Lines([PASSWORD, PASSWORD]))

    assert manage_users(["add", "new@sdu.edu.kz", "--name", "New", "--password-stdin"]) == 0
    assert manage_users(["add", "NEW@sdu.edu.kz", "--name", "New", "--password-stdin"]) == 1
    assert manage_users(["list"]) == 0

    output = capsys.readouterr()
    assert "Created officer new@sdu.edu.kz" in output.out
    assert "already has an account" in output.err
    assert PASSWORD not in output.out + output.err
    user = db_session.scalar(select(StaffUser).where(StaffUser.email == "new@sdu.edu.kz"))
    assert verify_password(PASSWORD, user.password_hash)


class _NoClose:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *_):
        return False


class _Lines:
    def __init__(self, lines):
        self.lines = [f"{line}\n" for line in lines]

    def readline(self):
        return self.lines.pop(0)
