"""Sprint 7: online application (US31), document upload (US32), review queue (US33) and
application status in the chat (US6). Decisions: docs/adr/0001-0004."""

import smtplib

import pytest
from sqlalchemy import select

from app.applicant import mail
from app.applicant.models import DocumentProgress
from app.applications import storage
from app.applications.models import Application, ApplicationDocument
from app.applications.service import send_status_notifications
from app.config import get_settings
from tests.test_admissions_requests import officer
from tests.test_applicant import register, verify

pytest_plugins = ("tests.test_applicant",)

ROOT = "/api/applicant/applications"
STAFF = "/api/staff/applications"
PDF = b"%PDF-1.4\n" + b"0" * 2048
PNG = b"\x89PNG\r\n\x1a\n" + b"1" * 512
FORM = {
    "full_name": "  Aigerim   Bekova ",
    "date_of_birth": "2008-03-14",
    "citizenship": "Kazakhstan",
    "phone": "+7 701 000 00 00",
    "education_level": "school",
    "graduation_year": 2026,
    "exam_total": 110,
    "consent": True,
}


@pytest.fixture
def uploads(tmp_path, monkeypatch):
    monkeypatch.setenv("APPLICATIONS_ENABLED", "true")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    yield tmp_path / "uploads"
    get_settings.cache_clear()


@pytest.fixture
def app_client(logged_in, uploads):
    client, session, messages = logged_in
    return client, session, messages, uploads


def start(client, program="cs", kind="local", language="en"):
    return client.post(ROOT, json={"program_id": program, "applicant_type": kind, "language": language})


def upload(client, application_id, content=PDF, name="scan.pdf", requirement_id=None):
    data = {"requirement_id": str(requirement_id)} if requirement_id is not None else {}
    return client.post(f"{ROOT}/{application_id}/documents", files={"file": (name, content, "application/pdf")}, data=data)


def ready(client, application_id, requirement_id=None):
    assert client.put(f"{ROOT}/{application_id}", json=FORM).status_code == 200
    assert upload(client, application_id, requirement_id=requirement_id).status_code == 201


def submitted(client):
    application = start(client).json()
    ready(client, application["id"], application["requirements"][0]["id"])
    response = client.post(f"{ROOT}/{application['id']}/submit")
    assert response.status_code == 200, response.text
    return response.json()


# ---- gate and authentication


def test_applications_are_off_until_enabled(logged_in, monkeypatch):
    client, _, _ = logged_in
    monkeypatch.setenv("APPLICATIONS_ENABLED", "false")
    get_settings.cache_clear()
    for method, path in (("get", ROOT), ("post", ROOT), ("get", STAFF)):
        response = getattr(client, method)(path, **({"json": {}} if method == "post" else {}))
        assert response.status_code == 503 and response.json()["error_code"] == "APPLICATIONS_UNAVAILABLE"


def test_every_endpoint_needs_its_own_login(applicant_env, uploads):
    client, _, _ = applicant_env
    for method, path in (
        ("get", ROOT),
        ("get", f"{ROOT}/status"),
        ("get", f"{ROOT}/1"),
        ("put", f"{ROOT}/1"),
        ("post", f"{ROOT}/1/submit"),
        ("get", f"{ROOT}/1/documents/1"),
        ("get", STAFF),
        ("get", f"{STAFF}/1"),
        ("post", f"{STAFF}/1/status"),
    ):
        response = getattr(client, method)(path, **({"json": {}} if method in ("post", "put") else {}))
        assert response.status_code == 401, (method, path, response.text)


# ---- US31: form, drafts, submit


def test_draft_form_and_submit(app_client):
    client, session, _, _ = app_client
    created = start(client)
    assert created.status_code == 201, created.text
    application = created.json()
    assert application["status"] == "draft" and application["editable"] is True
    assert [item["name"] for item in application["requirements"]] == ["School certificate", "National ID"]
    assert set(application["missing"]) >= {"full_name", "consent", "documents"}
    assert start(client).json()["error_code"] == "APPLICATION_EXISTS"

    saved = client.put(f"{ROOT}/{application['id']}", json=FORM).json()
    assert saved["full_name"] == "Aigerim Bekova" and saved["phone"] == "+7 701 000 00 00"
    assert saved["missing"] == ["documents"]
    incomplete = client.post(f"{ROOT}/{application['id']}/submit")
    assert incomplete.status_code == 422 and incomplete.json()["error_code"] == "APPLICATION_INCOMPLETE"

    assert upload(client, application["id"]).status_code == 201
    done = client.post(f"{ROOT}/{application['id']}/submit").json()
    assert done["status"] == "submitted" and done["editable"] is False and done["submitted_at"]
    # Submitted applications are read-only for the applicant.
    for response in (
        client.put(f"{ROOT}/{application['id']}", json=FORM),
        upload(client, application["id"]),
        client.post(f"{ROOT}/{application['id']}/submit"),
        client.delete(f"{ROOT}/{application['id']}"),
    ):
        assert response.status_code == 409 and response.json()["error_code"] == "APPLICATION_LOCKED"
    assert client.get(ROOT).json()["items"][0]["documents"] == 1


@pytest.mark.parametrize(
    "change",
    [
        {"phone": "call me"},
        {"date_of_birth": "2999-01-01"},
        {"graduation_year": 1800},
        {"exam_total": 151},
        {"education_level": "phd"},
        {"iin": "123456789012"},
    ],
)
def test_form_validation(app_client, change):
    client, _, _, _ = app_client
    application_id = start(client).json()["id"]
    assert client.put(f"{ROOT}/{application_id}", json={**FORM, **change}).status_code == 422


def test_start_rules(app_client):
    client, session, _, _ = app_client
    assert start(client, program="missing").status_code == 404
    assert start(client, kind="alien").status_code == 422
    assert start(client, kind="international").status_code == 201  # another applicant type is separate
    draft_id = start(client).json()["id"]
    assert client.delete(f"{ROOT}/{draft_id}").status_code == 204
    assert start(client).status_code == 201  # deleted drafts free the slot


# ---- US32: documents


def test_upload_download_and_tracker(app_client):
    client, session, _, folder = app_client
    application = start(client).json()
    requirement_id = application["requirements"][1]["id"]
    response = upload(client, application["id"], name="../../etc/passwd Copy.pdf", requirement_id=requirement_id)
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["content_type"] == "application/pdf" and document["size_bytes"] == len(PDF)
    assert document["original_name"] == "passwd Copy.pdf"
    stored = session.scalar(select(ApplicationDocument))
    assert (folder / stored.storage_key).read_bytes() == PDF
    assert list(folder.iterdir()) == [folder / stored.storage_key]  # random name, no temporary files left
    # The scan ticks that document in the tracker (US25).
    owner = session.get(Application, stored.application_id).applicant_id
    assert session.get(DocumentProgress, (owner, requirement_id)) is not None

    download = client.get(f"{ROOT}/{application['id']}/documents/{document['id']}")
    assert download.status_code == 200 and download.content == PDF
    assert download.headers["content-disposition"].startswith("attachment")
    assert download.headers["x-content-type-options"] == "nosniff"
    assert download.headers["cache-control"] == "no-store"

    detail = client.get(f"{ROOT}/{application['id']}").json()
    assert detail["requirements"][1]["uploaded"] is True and detail["bytes_used"] == len(PDF)
    assert client.delete(f"{ROOT}/{application['id']}/documents/{document['id']}").status_code == 204
    assert list(folder.iterdir()) == []


@pytest.mark.parametrize(
    "content,name,code",
    [
        (b"MZ\x90\x00 not a pdf", "virus.pdf", "UNSUPPORTED_FILE_TYPE"),
        (b"<html><script>alert(1)</script>", "page.png", "UNSUPPORTED_FILE_TYPE"),
        (b"", "empty.pdf", "EMPTY_FILE"),
    ],
)
def test_upload_rejects_wrong_content(app_client, content, name, code):
    client, _, _, folder = app_client
    application_id = start(client).json()["id"]
    response = upload(client, application_id, content=content, name=name)
    assert response.json()["error_code"] == code
    assert not folder.exists() or list(folder.iterdir()) == []


def test_upload_limits(app_client, monkeypatch):
    client, _, _, folder = app_client
    monkeypatch.setenv("UPLOAD_MAX_BYTES", "4096")
    monkeypatch.setenv("APPLICATION_MAX_BYTES", "6000")
    get_settings.cache_clear()
    application = start(client).json()
    too_big = upload(client, application["id"], content=b"%PDF-" + b"0" * 5000)
    assert too_big.status_code == 413 and too_big.json()["error_code"] == "FILE_TOO_LARGE"
    assert upload(client, application["id"]).status_code == 201  # 2057 bytes
    assert upload(client, application["id"], content=PNG).status_code == 201  # 520 bytes
    # 6000 - 2577 left: a third file of 3500 bytes passes the per-file limit but not the total.
    assert upload(client, application["id"], content=b"%PDF-" + b"0" * 3500).json()["error_code"] == "FILE_TOO_LARGE"
    other = session_requirement_from_other_programme(client, application["id"])
    assert other.status_code == 422 and other.json()["error_code"] == "INVALID_REQUIREMENT"
    assert len(list(folder.iterdir())) == 2


def session_requirement_from_other_programme(client, application_id):
    # The international checklist's passport is not on the local checklist of the same programme.
    international = client.post(ROOT, json={"program_id": "cs", "applicant_type": "international"}).json()
    return upload(client, application_id, requirement_id=international["requirements"][0]["id"])


# ---- isolation


def test_other_applicants_and_staff_cannot_see_drafts(app_client):
    client, session, messages, _ = app_client
    application = start(client).json()
    ready(client, application["id"])
    document_id = client.get(f"{ROOT}/{application['id']}").json()["documents"][0]["id"]
    client.post("/api/applicant/logout")
    register(client, "second@example.com")
    verify(client, messages)
    for path in (f"{ROOT}/{application['id']}", f"{ROOT}/{application['id']}/documents/{document_id}"):
        assert client.get(path).status_code == 404
    assert client.put(f"{ROOT}/{application['id']}", json=FORM).status_code == 404
    assert client.get(ROOT).json()["total"] == 0
    officer(client, session)
    assert client.get(f"{STAFF}/{application['id']}").status_code == 404  # drafts are private
    assert client.get(f"{STAFF}/{application['id']}/documents/{document_id}").status_code == 404
    assert client.get(STAFF, params={"status": "all"}).json()["total"] == 0


def test_account_deletion_removes_files(app_client):
    client, session, _, folder = app_client
    submitted(client)
    assert len(list(folder.iterdir())) == 1
    assert client.delete("/api/applicant/me").status_code == 204
    assert list(folder.iterdir()) == []
    assert session.scalar(select(Application)) is None


def test_storage_paths_cannot_escape_the_folder(uploads):
    for key in ("../secret", "a" * 31, "A" * 32, "g" * 32):
        with pytest.raises(ValueError):
            storage.file_path(get_settings(), key)
    assert storage.safe_name("C:\\Users\\x\\..\\scan.pdf") == "scan.pdf"
    assert storage.safe_name('a"b<c>.pdf') == "abc.pdf"
    assert storage.safe_name("   ") == "document"
    assert storage.safe_name("scan\x00\x1b[31m.pdf") == "scan[31m.pdf"


# ---- US33: review queue and status e-mails


def test_review_queue_status_changes_and_e_mails(app_client):
    client, session, messages, _ = app_client
    first = submitted(client)
    second = client.post(ROOT, json={"program_id": "cs", "applicant_type": "international", "language": "ru"}).json()
    ready(client, second["id"])
    assert client.post(f"{ROOT}/{second['id']}/submit").status_code == 200
    officer(client, session)

    queue = client.get(STAFF).json()
    assert [item["id"] for item in queue["items"]] == [first["id"], second["id"]]  # oldest first
    assert queue["items"][0]["applicant_email"] == "applicant@example.com"
    assert client.get(STAFF, params={"status": "accepted"}).json()["total"] == 0
    detail = client.get(f"{STAFF}/{first['id']}").json()
    download = client.get(f"{STAFF}/{first['id']}/documents/{detail['documents'][0]['id']}")
    assert download.status_code == 200 and download.content == PDF

    no_note = client.post(f"{STAFF}/{first['id']}/status", json={"status": "needs_changes"})
    assert no_note.status_code == 422 and no_note.json()["error_code"] == "NOTE_REQUIRED"
    before = len(messages)
    assert client.post(f"{STAFF}/{first['id']}/status", json={"status": "in_review"}).status_code == 200
    assert len(messages) == before  # no e-mail for "in review"
    changes = client.post(
        f"{STAFF}/{first['id']}/status", json={"status": "needs_changes", "note": "Attach a clearer scan of the certificate."}
    )
    assert changes.status_code == 200 and changes.json()["status"] == "needs_changes"
    assert len(messages) == before + 1
    recipient, subject, body = messages[-1]
    assert recipient == "applicant@example.com" and "status" in subject
    assert f"/account/applications/{first['id']}" in body and "clearer scan" not in body  # the note stays private
    invalid = client.post(f"{STAFF}/{first['id']}/status", json={"status": "accepted"})
    assert invalid.status_code == 409 and invalid.json()["error_code"] == "INVALID_STATUS_CHANGE"

    # The applicant sees the note, corrects and submits again; the office accepts.
    mine = client.get(f"{ROOT}/{first['id']}").json()
    assert mine["editable"] is True and mine["staff_note"] == "Attach a clearer scan of the certificate."
    assert upload(client, first["id"], content=PNG, name="clear.png").status_code == 201
    assert client.post(f"{ROOT}/{first['id']}/submit").json()["status"] == "submitted"
    accepted = client.post(f"{STAFF}/{first['id']}/status", json={"status": "accepted"})
    assert accepted.status_code == 200 and len(messages) == before + 2
    assert send_status_notifications(session, get_settings()) == 0  # nothing left to retry
    assert client.post(f"{STAFF}/{first['id']}/status", json={"status": "rejected", "note": "x"}).status_code == 409


def test_status_e_mail_is_retried_when_smtp_fails(app_client, monkeypatch):
    client, session, messages, _ = app_client
    application = submitted(client)
    officer(client, session)
    before = len(messages)
    with monkeypatch.context() as patch:
        patch.setattr(mail, "send_mail", lambda *args: (_ for _ in ()).throw(smtplib.SMTPServerDisconnected("down")))
        assert client.post(f"{STAFF}/{application['id']}/status", json={"status": "rejected", "note": "Wrong programme."}).status_code == 200
    assert len(messages) == before
    assert send_status_notifications(session, get_settings()) == 1
    assert send_status_notifications(session, get_settings()) == 0
    # After a rejection the applicant may start again.
    assert start(client).status_code == 201


# ---- US6: status in the chat


def test_status_answer_for_the_chat(app_client):
    client, session, _, _ = app_client
    empty = client.get(f"{ROOT}/status", params={"language": "ru"}).json()
    assert empty["items"] == [] and "нет заявок" in empty["answer"]
    application = submitted(client)
    status = client.get(f"{ROOT}/status", params={"language": "en"})
    assert status.headers["cache-control"] == "no-store"
    body = status.json()
    assert body["items"][0] == {
        "id": application["id"],
        "program_id": "cs",
        "status": "submitted",
        "stage": "Computer Science (cs): submitted, waiting for review.",
        "next_step": "Nothing to do now; we e-mail you when it changes.",
    }
    kk = client.get(f"{ROOT}/status", params={"language": "kk"}).json()["answer"]
    assert "Компьютерлік ғылымдар" in kk and "жіберілді" in kk


@pytest.mark.parametrize(
    "question,language_marker",
    [
        ("What is the status of my application?", "log in"),
        ("Какой статус моей заявки?", "войдёте"),
        ("Өтінішімнің мәртебесі қандай?", "кіргенде"),
    ],
)
def test_chat_recognises_status_questions(app_client, question, language_marker):
    client, _, _, _ = app_client
    response = client.post(
        "/api/assistant/ask", json={"question": question, "session_id": "00000000-0000-4000-8000-000000000071"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["intent"] == "application_status" and body["sources"] == [] and language_marker in body["answer"]


def test_chat_status_intent_in_the_stream(app_client):
    client, _, _, _ = app_client
    response = client.post(
        "/api/assistant/ask/stream",
        json={"question": "application status?", "session_id": "00000000-0000-4000-8000-000000000072"},
    )
    assert response.status_code == 200
    assert '"intent": "application_status"' in response.text
