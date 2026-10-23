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


def verify(client, messages):
    token = messages[-1][2].split("#token=")[1].strip()
    response = client.post(f"{ROOT}/verify", json={"token": token})
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
    assert client.post(f"{ROOT}/verify", json={"token": token}).status_code == 422
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
    assert client.post(f"{ROOT}/verify", json={"token": token}).status_code == 422
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


def test_pending_resend_uses_latest_password_and_invalidates_old_link(applicant_env):
    client, session, messages = applicant_env
    register(client)
    old = messages[-1][2].split("#token=")[1].strip()
    client.post(f"{ROOT}/register", json={"email": "applicant@example.com", "password": PASSWORD + "2"})
    assert client.post(f"{ROOT}/verify", json={"token": old}).status_code == 422
    verify(client, messages)
    client.post(f"{ROOT}/logout")
    assert (
        client.post(f"{ROOT}/login", json={"email": "applicant@example.com", "password": PASSWORD}).status_code == 401
    )
    assert (
        client.post(f"{ROOT}/login", json={"email": "applicant@example.com", "password": PASSWORD + "2"}).status_code
        == 200
    )


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


def test_registration_mail_failure_rolls_back_and_allows_retry(applicant_env, monkeypatch):
    client, session, messages = applicant_env
    with monkeypatch.context() as patch:
        patch.setattr(mail, "send_mail", lambda *args: (_ for _ in ()).throw(OSError("mail down")))
        assert register(client).status_code == 503
    assert session.scalar(select(Applicant)) is None
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
    assert send_due_reminders(session, get_settings(), TODAY) == 2
    assert "напоминание" in messages[-2][1]
    assert "National ID" in messages[-2][2] and "School certificate" not in messages[-2][2]
    assert "Passport" in messages[-1][2]
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
        patch.setattr(mail, "send_mail", lambda *args: (_ for _ in ()).throw(OSError("down")))
        assert send_due_reminders(session, get_settings(), TODAY) == 0
    assert send_due_reminders(session, get_settings(), TODAY) == 1
    session.get(Program, "cs").is_active = False
    session.flush()
    assert send_due_reminders(session, get_settings(), TODAY + timedelta(days=6)) == 0
