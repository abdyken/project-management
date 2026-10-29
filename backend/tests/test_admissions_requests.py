from sqlalchemy import select

from app.applicant import mail
from app.applicant.requests import AdmissionsRequest, send_request_notifications
from app.config import get_settings
from app.staff.service import create_user
from tests.test_applicant import register, verify
pytest_plugins = ("tests.test_applicant",)


def send(client, text="Please help with my admission", key="request-key-00000001"):
    return client.post(
        "/api/applicant/requests",
        json={"question": text, "client_key": key, "language": "kk"},
    )


def officer(client, session):
    create_user(
        session, "requests@sdu.edu.kz", "Officer", "officer", "a safe test password"
    )
    assert (
        client.post(
            "/api/staff/login",
            json={"email": "requests@sdu.edu.kz", "password": "a safe test password"},
        ).status_code
        == 200
    )


def test_all_endpoints_require_separate_authentication(applicant_env):
    client, _, _ = applicant_env
    for method, path, body in [
        ("get", "/api/applicant/requests", None),
        ("get", "/api/applicant/requests/1", None),
        (
            "post",
            "/api/applicant/requests",
            {"question": "Q", "client_key": "request-key-00000001"},
        ),
        ("get", "/api/staff/requests", None),
        ("get", "/api/staff/requests/1", None),
        ("post", "/api/staff/requests/1/answer", {"answer": "A"}),
    ]:
        assert client.request(method, path, json=body).status_code == 401


def test_full_roundtrip_deduplication_mail_retry_and_deletion(logged_in, monkeypatch):
    client, session, messages = logged_in
    result = send(client)
    assert result.status_code == 201, result.text
    request_id = result.json()["id"]
    assert "no-store" in result.headers["cache-control"]
    assert send(client).json()["id"] == request_id
    assert send(client, "Different question").status_code == 409
    assert client.get("/api/applicant/requests").json()["total"] == 1
    officer(client, session)
    assert client.get("/api/staff/requests").json()["total"] == 1
    reply = client.post(
        f"/api/staff/requests/{request_id}/answer",
        json={"answer": "Please contact the office with your programme code."},
    )
    assert reply.status_code == 200 and reply.json()["answered_at"]
    assert (
        client.post(
            f"/api/staff/requests/{request_id}/answer",
            json={"answer": "Different reply"},
        ).status_code
        == 409
    )
    assert client.get("/api/staff/requests?status=new").json()["total"] == 0
    assert client.get("/api/staff/requests?status=answered").json()["total"] == 1
    before = len(messages)
    with monkeypatch.context() as patch:
        patch.setattr(
            mail, "send_mail", lambda *args: (_ for _ in ()).throw(OSError("SMTP down"))
        )
        assert send_request_notifications(session, get_settings()) == 0
    assert client.get(f"/api/applicant/requests/{request_id}").json()["answer"]
    assert send_request_notifications(session, get_settings()) == 1
    assert len(messages) == before + 1 and "жеке" in messages[-1][2]
    assert "Please help" not in messages[-1][2]
    assert send_request_notifications(session, get_settings()) == 0
    assert client.delete("/api/applicant/me").status_code == 204
    assert list(session.scalars(select(AdmissionsRequest))) == []


def test_account_isolation_and_origin(logged_in):
    client, session, messages = logged_in
    request_id = send(client).json()["id"]
    client.post("/api/applicant/logout")
    register(client, "second@example.com")
    verify(client, messages)
    assert client.get("/api/applicant/requests").json()["items"] == []
    assert client.get(f"/api/applicant/requests/{request_id}").status_code == 404
    assert (
        client.post(
            "/api/applicant/requests",
            headers={"Origin": "https://evil.example"},
            json={"question": "Q", "client_key": "request-key-00000002"},
        ).status_code
        == 403
    )
    officer(client, session)
    assert (
        client.post(
            f"/api/staff/requests/{request_id}/answer",
            headers={"Origin": "https://evil.example"},
            json={"answer": "A"},
        ).status_code
        == 403
    )


def test_request_rate_limit_and_empty_validation(logged_in):
    client, _, _ = logged_in
    for i in range(5):
        assert send(client, key=f"request-key-{i:08d}").status_code == 201
    assert send(client, key="request-key-99999999").status_code == 429
    assert (
        send(client, key="request-key-00000000").status_code == 201
    )  # retries do not count
    assert send(client, text="   ", key="request-key-99999999").status_code == 422


def test_accounts_gate_and_mail_not_configured(logged_in, monkeypatch):
    client, session, _ = logged_in
    request_id = send(client).json()["id"]
    officer(client, session)
    monkeypatch.setenv("SMTP_HOST", "")
    get_settings.cache_clear()
    assert (
        client.post(
            f"/api/staff/requests/{request_id}/answer",
            json={"answer": "Saved without mail"},
        ).status_code
        == 200
    )
    assert send_request_notifications(session, get_settings()) == 0
    monkeypatch.setenv("APPLICANT_ACCOUNTS_ENABLED", "false")
    get_settings.cache_clear()
    assert client.get("/api/applicant/requests").status_code == 503
