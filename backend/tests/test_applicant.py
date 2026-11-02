from datetime import date, timedelta
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import delete, select

from app.applicant import mail, router, service
from app.applicant.models import Applicant, ApplicantSession, DeadlineReminder, DocumentProgress, SavedProgram
from app.applicant.reminders import send_due_reminders
from app.catalogue.models import Program
from app.checklist.models import ProgramDocumentRequirement
from app.config import get_settings
from app.db import get_db_session
from app.main import app
from app.staff.service import LoginLimiter

ROOT = "/api/applicant"
PASSWORD = "a secure test password"
TODAY = date(2026, 10, 22)


@pytest.fixture
def applicant_env(catalogue_session, monkeypatch):
    monkeypatch.setenv("APPLICANT_ACCOUNTS_ENABLED", "true")
    monkeypatch.setenv("SMTP_HOST", "test-smtp")
    get_settings.cache_clear()
    monkeypatch.setattr(router, "login_limiter", LoginLimiter())
    monkeypatch.setattr(router, "register_limiter", LoginLimiter())
    messages = []
    monkeypatch.setattr(
        mail, "send_mail", lambda settings, recipient, subject, body: messages.append((recipient, subject, body))
    )
    monkeypatch.setattr(mail.Mailer, "send", lambda self, recipient, subject, body: messages.append((recipient, subject, body)))
    session = catalogue_session
    session.execute(delete(Applicant))
    session.add_all(
        [
            Program(
                program_id="cs",
                title="Computer Science",
                title_ru="Информатика",
                title_kk="Компьютерлік ғылымдар",
                faculty="Engineering",
                degree_level="bachelor",
                deadline_local=TODAY + timedelta(days=7),
                deadline_international=TODAY + timedelta(days=1),
                source_url="https://sdu.edu.kz/en/",
            ),
            Program(program_id="empty", title="Unknown list", faculty="Engineering", degree_level="master"),
        ]
    )
    session.flush()
    session.add_all(
        [
            ProgramDocumentRequirement(
                program_id="cs",
                applicant_type="local",
                name="School certificate",
                document_format="original",
                deadline="Enrolment",
                display_order=0,
            ),
            ProgramDocumentRequirement(
                program_id="cs",
                applicant_type="local",
                name="National ID",
                document_format="copy",
                deadline="Enrolment",
                display_order=1,
            ),
            ProgramDocumentRequirement(
                program_id="cs",
                applicant_type="international",
                name="Passport",
                document_format="copy",
                translation_required=True,
                notarisation_required=True,
                deadline="Application",
            ),
        ]
    )
    session.commit()
    app.dependency_overrides[get_db_session] = lambda: session
    # No context manager: lifespan's independent workers must not use the test database.
    client = TestClient(app, base_url="https://localhost")
    try:
        yield client, session, messages
    finally:
        client.close()
        app.dependency_overrides.pop(get_db_session, None)


def register(client, email="applicant@example.com", language="en"):
    return client.post(f"{ROOT}/register", json={"email": email, "password": PASSWORD, "language": language})


def verify(client, messages, password=PASSWORD):
    token = messages[-1][2].split("#token=")[1].strip()
    response = client.post(f"{ROOT}/verify", json={"token": token, "password": password})
    assert response.status_code == 200, response.text
    return token


@pytest.fixture
def logged_in(applicant_env):
    client, session, messages = applicant_env
    assert register(client).status_code == 202
    verify(client, messages)
    return client, session, messages


def test_registration_verification_login_and_logout(applicant_env):
    client, session, messages = applicant_env
    assert register(client, " Applicant@Example.com ").status_code == 202
    user = session.scalar(select(Applicant))
    assert user.email == "applicant@example.com"
    assert user.password_hash.startswith("scrypt$") and PASSWORD not in user.password_hash
    assert client.post(f"{ROOT}/login", json={"email": user.email, "password": PASSWORD}).status_code == 401
    token = verify(client, messages)
    assert session.scalar(select(ApplicantSession)).token_hash != client.cookies.get("applicant_session")
    assert token not in repr(user.verification_hash)
    assert client.post(f"{ROOT}/verify", json={"token": token, "password": PASSWORD}).status_code == 422
    assert client.get(f"{ROOT}/me").json()["email"] == user.email
    assert client.post(f"{ROOT}/logout").status_code == 204
    assert client.get(f"{ROOT}/me").status_code == 401
    login = client.post(f"{ROOT}/login", json={"email": "APPLICANT@example.com", "password": PASSWORD})
    assert login.status_code == 200
    cookie = login.headers["set-cookie"]
    assert all(value in cookie for value in ("HttpOnly", "Secure", "SameSite=strict", "Path=/api/applicant"))
    assert login.headers["cache-control"] == "no-store"
    assert "password" not in login.text and "verification" not in login.text


def test_expired_verification_and_session(applicant_env):
    client, session, messages = applicant_env
    register(client)
    user = session.scalar(select(Applicant))
    user.verification_expires_at = service.now() - timedelta(seconds=1)
    session.flush()
    token = messages[-1][2].split("#token=")[1].strip()
    assert client.post(f"{ROOT}/verify", json={"token": token, "password": PASSWORD}).status_code == 422
    register(client)
    verify(client, messages)
    session.scalar(select(ApplicantSession)).expires_at = service.now() - timedelta(seconds=1)
    session.flush()
    assert client.get(f"{ROOT}/me").status_code == 401


def test_resend_rotates_token_and_verified_account_is_unchanged(logged_in):
    client, session, messages = logged_in
    original = session.scalar(select(Applicant)).password_hash
    count = len(messages)
    assert register(client).status_code == 202
    assert len(messages) == count
    assert session.scalar(select(Applicant)).password_hash == original


def test_pending_resend_keeps_password_and_invalidates_old_link(applicant_env):
    client, session, messages = applicant_env
    register(client)
    original = session.scalar(select(Applicant)).password_hash
    old = messages[-1][2].split("#token=")[1].strip()
    client.post(f"{ROOT}/register", json={"email": "applicant@example.com", "password": PASSWORD + "2"})
    assert session.scalar(select(Applicant)).password_hash == original
    assert client.post(f"{ROOT}/verify", json={"token": old, "password": PASSWORD}).status_code == 422
    verify(client, messages)


@pytest.mark.parametrize("victim_first", [True, False])
def test_registering_a_pending_email_cannot_take_over_the_account(applicant_env, victim_first):
    # Either order: whoever opens the link from the inbox sets the password at verification.
    client, session, messages = applicant_env
    attacker = {"email": "applicant@example.com", "password": "attacker password 123"}
    if victim_first:
        register(client)
        client.post(f"{ROOT}/register", json=attacker)
    else:
        client.post(f"{ROOT}/register", json=attacker)
        register(client)
    verify(client, messages)  # the victim opens the newest link and enters their password
    client.post(f"{ROOT}/logout")
    assert client.post(f"{ROOT}/login", json=attacker).status_code == 401
    assert client.post(f"{ROOT}/login", json={"email": attacker["email"], "password": PASSWORD}).status_code == 200


def test_verification_requires_a_valid_password(applicant_env):
    client, _, messages = applicant_env
    register(client)
    token = messages[-1][2].split("#token=")[1].strip()
    assert client.post(f"{ROOT}/verify", json={"token": token}).status_code == 422
    assert client.post(f"{ROOT}/verify", json={"token": token, "password": "short"}).status_code == 422
    verify(client, messages)


@pytest.mark.parametrize(
    "body",
    [
        {"email": "bad", "password": PASSWORD},
        {"email": "a@example.com\nBcc:b@example.com", "password": PASSWORD},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": PASSWORD, "language": "fr"},
    ],
)
def test_registration_rejects_invalid_input(applicant_env, body):
    client, _, messages = applicant_env
    assert client.post(f"{ROOT}/register", json=body).status_code == 422
    assert messages == []


def test_registration_mail_failure_keeps_pending_account_and_allows_retry(applicant_env, monkeypatch):
    client, session, messages = applicant_env
    with monkeypatch.context() as patch:
        patch.setattr(mail, "send_mail", lambda *args: (_ for _ in ()).throw(OSError("mail down")))
        assert register(client).status_code == 503
    # Committed before sending: no lock or connection is held while SMTP is slow.
    assert session.scalar(select(Applicant)).verified is False
    assert register(client).status_code == 202
    verify(client, messages)


def test_login_and_registration_rate_limits(applicant_env):
    client, _, _ = applicant_env
    for index in range(5):
        assert (
            client.post(
                f"{ROOT}/login", json={"email": f"unknown{index}@example.com", "password": PASSWORD}
            ).status_code
            == 401
        )
    assert client.post(f"{ROOT}/login", json={"email": "other@example.com", "password": PASSWORD}).status_code == 429
    for _ in range(5):
        assert register(client).status_code == 202
    assert register(client).status_code == 429


def test_rate_limits_count_per_visitor_behind_the_proxy(applicant_env):
    # In production every request reaches the API from the nginx container; the visitor
    # is the first X-Forwarded-For entry. One visitor's failures must not block others.
    client, _, _ = applicant_env
    nginx = "172.18.0.5"
    for index in range(5):
        response = client.post(
            f"{ROOT}/login",
            json={"email": f"guess{index}@example.com", "password": PASSWORD},
            headers={"X-Forwarded-For": f"203.0.113.7, {nginx}"},
        )
        assert response.status_code == 401
    blocked = client.post(
        f"{ROOT}/login",
        json={"email": "someone@example.com", "password": PASSWORD},
        headers={"X-Forwarded-For": f"203.0.113.7, {nginx}"},
    )
    assert blocked.status_code == 429
    for index in range(5):
        response = client.post(
            f"{ROOT}/register",
            json={"email": f"new{index}@example.com", "password": PASSWORD},
            headers={"X-Forwarded-For": f"198.51.100.{index}, {nginx}"},
        )
        assert response.status_code == 202
    other = client.post(
        f"{ROOT}/login",
        json={"email": "someone@example.com", "password": PASSWORD},
        headers={"X-Forwarded-For": f"198.51.100.200, {nginx}"},
    )
    assert other.status_code == 401
    sixth = client.post(
        f"{ROOT}/register",
        json={"email": "new6@example.com", "password": PASSWORD},
        headers={"X-Forwarded-For": f"198.51.100.6, {nginx}"},
    )
    assert sixth.status_code == 202


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/me", None),
        ("patch", "/me", {"language": "en", "reminders_enabled": True}),
        ("delete", "/me", None),
        ("get", "/programs", None),
        ("get", "/programs/cs/local", None),
        ("put", "/programs/cs/local", None),
        ("delete", "/programs/cs/local", None),
        ("put", "/programs/cs/local/documents/1", {"prepared": True}),
        ("get", "/programs/cs/local/pdf", None),
    ],
)
def test_every_private_endpoint_needs_applicant_login(applicant_env, method, path, body):
    client, _, _ = applicant_env
    response = client.request(method, ROOT + path, json=body)
    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_LOGGED_IN"
    assert response.headers["cache-control"] == "no-store"


def test_cross_site_mutations_rejected(logged_in):
    client, _, _ = logged_in
    assert client.delete(f"{ROOT}/me", headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert client.get(f"{ROOT}/me").status_code == 200


def test_staff_cookie_cannot_authenticate_an_applicant(applicant_env):
    client, _, _ = applicant_env
    client.cookies.set("staff_session", "a-staff-cookie", path="/api/staff")
    assert client.get(f"{ROOT}/me").status_code == 401


def test_registration_without_smtp_is_explicitly_unavailable(applicant_env, monkeypatch):
    client, session, messages = applicant_env
    monkeypatch.setenv("SMTP_HOST", "")
    get_settings.cache_clear()
    assert register(client).status_code == 503
    assert messages == [] and session.scalar(select(Applicant)) is None


def test_feature_gate(applicant_env, monkeypatch):
    client, _, _ = applicant_env
    monkeypatch.setenv("APPLICANT_ACCOUNTS_ENABLED", "false")
    get_settings.cache_clear()
    assert client.get(f"{ROOT}/me").status_code == 503
    # PDF export remains available without accounts.
    assert client.get("/api/programs/cs/checklist/pdf?applicant_type=local").status_code == 200


def save(client, kind="local", program="cs"):
    response = client.put(f"{ROOT}/programs/{program}/{kind}")
    assert response.status_code == 200, response.text
    return response.json()


def test_saved_programs_progress_and_types_are_separate(logged_in):
    client, session, _ = logged_in
    local = save(client)
    save(client)
    international = save(client, "international")
    assert len(client.get(f"{ROOT}/programs").json()["items"]) == 2
    assert len(list(session.scalars(select(SavedProgram)))) == 2
    assert [item["name"] for item in local["items"]] == ["School certificate", "National ID"]
    document_id = local["items"][0]["id"]
    path = f"{ROOT}/programs/cs/local/documents/{document_id}"
    assert client.put(path, json={"prepared": True}).json()["prepared"] == 1
    assert client.put(path, json={"prepared": True}).json()["prepared"] == 1
    assert client.get(f"{ROOT}/programs/cs/local").json()["items"][0]["prepared"] is True
    assert client.get(f"{ROOT}/programs/cs/international").json()["prepared"] == 0
    wrong = f"{ROOT}/programs/cs/local/documents/{international['items'][0]['id']}"
    assert client.put(wrong, json={"prepared": True}).status_code == 404
    assert client.put(path, json={"prepared": False}).json()["prepared"] == 0
    assert client.put(f"{ROOT}/programs/missing/local").status_code == 404
    assert client.put(f"{ROOT}/programs/cs/alien").status_code == 422


def test_two_accounts_cannot_read_or_change_each_others_progress(logged_in):
    client, session, messages = logged_in
    local = save(client)
    document_id = local["items"][0]["id"]
    client.put(f"{ROOT}/programs/cs/local/documents/{document_id}", json={"prepared": True})
    client.post(f"{ROOT}/logout")
    register(client, "second@example.com")
    verify(client, messages)
    assert client.get(f"{ROOT}/programs").json() == {"items": []}
    assert client.get(f"{ROOT}/programs/cs/local").status_code == 404
    assert client.put(f"{ROOT}/programs/cs/local/documents/{document_id}", json={"prepared": False}).status_code == 404
    assert save(client)["prepared"] == 0
    client.delete(f"{ROOT}/programs/cs/local")
    client.post(f"{ROOT}/logout")
    client.post(f"{ROOT}/login", json={"email": "applicant@example.com", "password": PASSWORD})
    assert client.get(f"{ROOT}/programs/cs/local").json()["prepared"] == 1


def test_checklist_replacement_clears_old_progress_and_archive_is_visible(logged_in):
    client, session, _ = logged_in
    local = save(client)
    document_id = local["items"][0]["id"]
    client.put(f"{ROOT}/programs/cs/local/documents/{document_id}", json={"prepared": True})
    session.execute(delete(ProgramDocumentRequirement).where(ProgramDocumentRequirement.id == document_id))
    session.add(
        ProgramDocumentRequirement(
            program_id="cs",
            applicant_type="local",
            name="Updated certificate",
            document_format="original",
            deadline="Updated official deadline",
        )
    )
    session.flush()
    updated = client.get(f"{ROOT}/programs/cs/local").json()
    assert updated["prepared"] == 0 and updated["total"] == 2
    assert list(session.scalars(select(DocumentProgress))) == []
    assert client.put(f"{ROOT}/programs/cs/local/documents/{document_id}", json={"prepared": True}).status_code == 404
    session.get(Program, "cs").is_active = False
    session.flush()
    assert client.get(f"{ROOT}/programs/cs/local").json()["program"]["is_active"] is False
    assert client.put(f"{ROOT}/programs/cs/local").status_code == 404


def test_remove_clears_progress_and_missing_list_has_warning(logged_in):
    client, session, _ = logged_in
    local = save(client)
    client.put(f"{ROOT}/programs/cs/local/documents/{local['items'][0]['id']}", json={"prepared": True})
    assert client.delete(f"{ROOT}/programs/cs/local").status_code == 204
    assert list(session.scalars(select(DocumentProgress))) == []
    assert save(client)["prepared"] == 0
    empty = save(client, program="empty")
    assert empty["warning"] and empty["contact"] and empty["total"] == 0


def test_account_delete_cascades_and_invalidates_all_sessions(logged_in):
    client, session, _ = logged_in
    local = save(client)
    client.put(f"{ROOT}/programs/cs/local/documents/{local['items'][0]['id']}", json={"prepared": True})
    client.patch(f"{ROOT}/me", json={"language": "en", "reminders_enabled": True})
    assert send_due_reminders(session, get_settings(), TODAY) == 1
    assert client.delete(f"{ROOT}/me").status_code == 204
    for model in (Applicant, ApplicantSession, SavedProgram, DocumentProgress, DeadlineReminder):
        assert list(session.scalars(select(model))) == []
    assert client.get(f"{ROOT}/me").status_code == 401


@pytest.mark.parametrize(
    "language,title", [("en", "Document checklist"), ("ru", "Список документов"), ("kk", "Құжаттар тізімі")]
)
def test_pdf_exports_current_requirements_and_personal_progress(logged_in, language, title):
    client, session, _ = logged_in
    local = save(client)
    client.put(f"{ROOT}/programs/cs/local/documents/{local['items'][0]['id']}", json={"prepared": True})
    public = client.get(f"/api/programs/cs/checklist/pdf?applicant_type=local&language={language}")
    private = client.get(f"{ROOT}/programs/cs/local/pdf?language={language}")
    for response in (public, private):
        assert response.status_code == 200 and response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"].startswith("attachment;")
        reader = PdfReader(BytesIO(response.content))
        text = "\n".join(page.extract_text() for page in reader.pages)
        assert title in text and "School certificate" in text and "National ID" in text
        assert "Enrolment" in text and "2026-10-29" in text
        assert "example.com" not in text
    assert "1/2" in PdfReader(BytesIO(private.content)).pages[0].extract_text()
    assert "0/2" in PdfReader(BytesIO(public.content)).pages[0].extract_text()


def test_pdf_missing_list_and_invalid_requests(logged_in):
    client, _, _ = logged_in
    response = client.get("/api/programs/empty/checklist/pdf?applicant_type=local")
    assert response.status_code == 200
    assert "not published" in PdfReader(BytesIO(response.content)).pages[0].extract_text()
    assert client.get("/api/programs/nope/checklist/pdf?applicant_type=local").status_code == 404
    assert client.get("/api/programs/cs/checklist/pdf?applicant_type=alien").status_code == 422
    assert client.get("/api/programs/cs/checklist/pdf?applicant_type=local&language=fr").status_code == 422


def test_reminders_opt_in_milestones_deduplication_and_missing_documents(logged_in):
    client, session, messages = logged_in
    local = save(client)
    save(client, "international")
    save(client, program="empty")
    assert send_due_reminders(session, get_settings(), TODAY) == 0
    assert client.patch(f"{ROOT}/me", json={"language": "ru", "reminders_enabled": True}).status_code == 200
    client.put(f"{ROOT}/programs/cs/local/documents/{local['items'][0]['id']}", json={"prepared": True})
    # Local (7 days) and international (1 day) are both due: one e-mail lists both.
    assert send_due_reminders(session, get_settings(), TODAY) == 1
    subject, body = messages[-1][1], messages[-1][2]
    assert "напоминание" in subject
    assert "National ID" in body and "School certificate" not in body and "Passport" in body
    assert "местные абитуриенты" in body and "иностранные абитуриенты" in body
    assert send_due_reminders(session, get_settings(), TODAY) == 0
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=1)) == 1  # international deadline day
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=2)) == 0  # no overdue mail
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=6)) == 1
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=7)) == 1
    client.patch(f"{ROOT}/me", json={"language": "kk", "reminders_enabled": False})
    session.get(Program, "cs").deadline_local += timedelta(days=7)
    session.flush()
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=7)) == 0


def test_reminder_delivery_failure_is_retried_and_archived_program_is_skipped(logged_in, monkeypatch):
    client, session, _ = logged_in
    save(client)
    client.patch(f"{ROOT}/me", json={"language": "en", "reminders_enabled": True})
    with monkeypatch.context() as patch:
        patch.setattr(mail.Mailer, "send", lambda *args: (_ for _ in ()).throw(OSError("down")))
        assert send_due_reminders(session, get_settings(), TODAY) == 0
    assert send_due_reminders(session, get_settings(), TODAY) == 1
    session.get(Program, "cs").is_active = False
    session.flush()
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=6)) == 0


def _opted_in_applicants(client, session, messages, count):
    """`count` extra verified applicants who saved cs/local and opted in to reminders."""
    for index in range(count):
        client.cookies.clear()
        register(client, f"reader{index}@example.com")
        verify(client, messages)
        save(client)
        client.patch(f"{ROOT}/me", json={"language": "en", "reminders_enabled": True})


def test_reminders_send_one_digest_per_applicant(logged_in):
    client, session, messages = logged_in
    session.add(
        Program(
            program_id="law",
            title="Law",
            faculty="Law",
            degree_level="bachelor",
            deadline_local=TODAY + timedelta(days=7),
        )
    )
    session.flush()
    save(client)
    save(client, program="law")
    client.patch(f"{ROOT}/me", json={"language": "en", "reminders_enabled": True})
    before = len(messages)
    assert send_due_reminders(session, get_settings(), TODAY) == 1
    assert len(messages) == before + 1
    assert "Computer Science (cs)" in messages[-1][2] and "Law (law)" in messages[-1][2]
    assert len(list(session.scalars(select(DeadlineReminder).where(DeadlineReminder.sent_at.is_not(None))))) == 2


def test_reminder_daily_limit_leaves_the_rest_for_the_next_run(logged_in, monkeypatch):
    client, session, messages = logged_in
    _opted_in_applicants(client, session, messages, 3)
    monkeypatch.setenv("REMINDER_DAILY_LIMIT", "2")
    get_settings.cache_clear()
    assert send_due_reminders(session, get_settings(), TODAY) == 2
    assert send_due_reminders(session, get_settings(), TODAY) == 0  # limit reached for this Almaty day
    monkeypatch.setenv("REMINDER_DAILY_LIMIT", "300")
    get_settings.cache_clear()
    assert send_due_reminders(session, get_settings(), TODAY) == 1


def test_login_or_quota_error_stops_the_run_but_refused_recipient_does_not(logged_in, monkeypatch):
    import smtplib

    client, session, messages = logged_in
    _opted_in_applicants(client, session, messages, 3)
    attempts = []

    def quota(self, recipient, subject, body):
        attempts.append(recipient)
        raise smtplib.SMTPDataError(550, b"5.4.5 Daily user sending limit exceeded")

    with monkeypatch.context() as patch:
        patch.setattr(mail.Mailer, "send", quota)
        assert send_due_reminders(session, get_settings(), TODAY) == 0
    assert len(attempts) == 1  # no more Gmail attempts once the quota is reached

    def refused(self, recipient, subject, body):
        if recipient == "reader0@example.com":
            raise smtplib.SMTPRecipientsRefused({recipient: (550, b"no such user")})
        messages.append((recipient, subject, body))

    with monkeypatch.context() as patch:
        patch.setattr(mail.Mailer, "send", refused)
        assert send_due_reminders(session, get_settings(), TODAY) == 2  # reader1 and reader2


def test_one_failing_applicant_does_not_stop_the_run(logged_in, monkeypatch):
    from app.applicant import reminders

    client, session, messages = logged_in
    _opted_in_applicants(client, session, messages, 2)
    real = reminders.saved_checklist

    def flaky(session, user, *args, **kwargs):
        if user.email == "reader0@example.com":
            raise RuntimeError("unexpected")
        return real(session, user, *args, **kwargs)

    monkeypatch.setattr(reminders, "saved_checklist", flaky)
    assert send_due_reminders(session, get_settings(), TODAY) == 1


def test_reminder_failure_does_not_block_reply_notifications(monkeypatch):
    from app.applicant import reminders

    calls = []

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def broken(session, settings):
        raise RuntimeError("reminders broke")

    monkeypatch.setattr(reminders, "get_session", lambda settings: Session())
    monkeypatch.setattr(reminders, "send_due_reminders", broken)
    monkeypatch.setattr("app.applicant.requests.send_request_notifications", lambda session, settings: calls.append(1))
    reminders._run(get_settings())
    assert calls == [1]


def test_smtp_verifies_the_server_certificate_and_reuses_one_connection(monkeypatch):
    import ssl

    import app.applicant.mail as mail_module

    connections = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            self.sent, self.context = [], None
            connections.append(self)

        def starttls(self, context=None):
            self.context = context

        def login(self, username, password):
            pass

        def send_message(self, message):
            self.sent.append(message["To"])

        def quit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(mail_module.smtplib, "SMTP", FakeSMTP)
    settings = get_settings().model_copy(update={"smtp_host": "smtp.gmail.com", "smtp_username": "portal@gmail.com"})
    with mail_module.Mailer(settings) as mailer:
        mailer.send("a@example.com", "s", "b")
        mailer.send("b@example.com", "s", "b")
    assert len(connections) == 1 and connections[0].sent == ["a@example.com", "b@example.com"]
    context = connections[0].context
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname is True


def test_staff_document_list_edits_keep_applicant_progress(logged_in):
    from app.staff.service import create_user

    client, session, _ = logged_in
    create_user(session, "officer@sdu.edu.kz", "Aigerim", "officer", PASSWORD)
    assert client.post("/api/staff/login", json={"email": "officer@sdu.edu.kz", "password": PASSWORD}).status_code == 200
    session.add(Program(program_id="6B06102", title="Computer Science", faculty="IT", degree_level="bachelor"))
    session.flush()
    session.add_all(
        ProgramDocumentRequirement(
            program_id="6B06102", applicant_type="local", name=name, document_format="copy", deadline="Enrolment"
        )
        for name in ("School certificate", "National ID")
    )
    session.flush()
    local = save(client, program="6B06102")
    for item in local["items"]:
        client.put(f"{ROOT}/programs/6B06102/local/documents/{item['id']}", json={"prepared": True})
    documents = [
        {"name": item["name"], "format": item["format"], "deadline": item["deadline"]} for item in local["items"]
    ]

    def edit(new_documents):
        response = client.put("/api/staff/programs/6B06102/documents/local", json={"documents": new_documents})
        assert response.status_code == 200, response.text
        return client.get(f"{ROOT}/programs/6B06102/local").json()

    # Saving the same list, reordering it or changing a deadline keeps every tick.
    assert edit(documents)["prepared"] == 2
    reordered = edit([{**documents[1], "deadline": "Updated deadline"}, documents[0]])
    assert reordered["prepared"] == 2 and reordered["items"][0]["name"] == documents[1]["name"]
    # Renaming one document clears only that document's tick; a new one starts unprepared.
    renamed = edit([{**documents[0], "name": "School leaving certificate"}, documents[1], {**documents[1], "name": "Photo"}])
    assert renamed["total"] == 3 and renamed["prepared"] == 1
