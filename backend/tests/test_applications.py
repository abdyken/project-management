"""Sprint 7: online application (US31), document upload (US32), review queue (US33) and
application status in the chat (US6). Decisions: docs/adr/0001-0004."""

import json
import os
import smtplib
import time
from collections import namedtuple

import pytest
from pathlib import Path
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
    assert application["missing"] == [
        "full_name", "date_of_birth", "citizenship", "phone", "education_level", "graduation_year", "consent", "documents"
    ]
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
    assert response.status_code == (415 if code == "UNSUPPORTED_FILE_TYPE" else 422)
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
    full = upload(client, application["id"], content=b"%PDF-" + b"0" * 3500)
    assert full.status_code == 413 and full.json()["error_code"] == "APPLICATION_FULL"
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
    assert storage.download_name("Diploma.bat", "application/pdf") == "Diploma.pdf"
    assert storage.download_name("scan.PNG", "image/png") == "scan.png"
    assert storage.download_name("no extension", "image/jpeg") == "no extension.jpg"
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
        ("What is the status of my application?", "My applications"),
        ("Какой статус моей заявки?", "Мои заявки"),
        ("Өтінішімнің мәртебесі қандай?", "Менің өтініштерім"),
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
        json={"question": "What is the status of my application?", "session_id": "00000000-0000-4000-8000-000000000072"},
    )
    assert response.status_code == 200
    done = [line for line in response.text.splitlines() if line.startswith("data:") and "answer_id" in line][-1]
    assert json.loads(done.removeprefix("data:"))["intent"] == "application_status"



# ---- review follow-ups (ECC and gstack reviews, 20.11.2026)


def test_every_new_status_is_e_mailed_again(app_client):
    client, session, messages, _ = app_client
    application = submitted(client)
    officer(client, session)
    before = len(messages)
    for round_ in (1, 2):
        assert client.post(f"{STAFF}/{application['id']}/status", json={"status": "needs_changes", "note": f"Fix {round_}"}).status_code == 200
        assert len(messages) == before + round_  # the second request for changes is e-mailed too
        assert client.post(f"{ROOT}/{application['id']}/submit").status_code == 200
    assert send_status_notifications(session, get_settings()) == 0


@pytest.mark.parametrize(
    "question",
    [
        "Has my application been accepted?",
        "Is my application approved?",
        "Where is my application?",
        "Моя заявка принята?",
        "Где моя заявка?",
        "Өтінішім қабылданды ма?",
        "Менің өтінішім қайда?",
    ],
)
def test_status_questions_are_recognised(question):
    from app.assistant.intents import is_application_status_question

    assert is_application_status_question(question)


@pytest.mark.parametrize(
    "question",
    [
        "What documents do I need for my application?",
        "How do I submit my application?",
        "Where do I submit my application?",
        "What are the stages of the application process?",
        "What is the application deadline?",
        "application status",
        "Какие этапы подачи заявки?",
        "Как отправить мою заявку?",
        "Где подать мою заявку?",
        "Нужна ли справка о состоянии здоровья для заявления?",
        "Өтініш беру кезеңдері қандай?",
        "Өтініш беру үшін қандай жағдай керек?",
        "Can I progress to a master after applied physics?",
    ],
)
def test_ordinary_questions_are_not_status_questions(question):
    from app.assistant.intents import is_application_status_question

    assert not is_application_status_question(question)


def test_chat_has_no_status_intent_when_applications_are_off(app_client, monkeypatch):
    from app.assistant import router as assistant_router
    from app.assistant.schemas import Answer

    client, _, _, _ = app_client
    monkeypatch.setenv("APPLICATIONS_ENABLED", "false")
    get_settings.cache_clear()

    class FakeService:
        def __init__(self, *args, **kwargs):
            pass

        def answer(self, question, session_id):
            return Answer(answer="FAQ answer", sources=[], source_link=None, faq_id=None, similarity_score=None)

    monkeypatch.setattr(assistant_router, "AssistantService", FakeService)
    body = client.post(
        "/api/assistant/ask", json={"question": "What is the status of my application?", "session_id": "00000000-0000-4000-8000-000000000073"}
    ).json()
    assert body["answer"] == "FAQ answer" and "intent" not in body


def test_documents_are_only_reachable_through_their_own_application(app_client):
    client, _, _, _ = app_client
    first = start(client).json()
    assert upload(client, first["id"]).status_code == 201
    document_id = client.get(f"{ROOT}/{first['id']}").json()["documents"][0]["id"]
    second = start(client, kind="international").json()
    assert client.get(f"{ROOT}/{second['id']}/documents/{document_id}").status_code == 404
    assert client.delete(f"{ROOT}/{second['id']}/documents/{document_id}").status_code == 404


def test_download_name_takes_the_detected_extension(app_client):
    client, _, _, _ = app_client
    application_id = start(client).json()["id"]
    document = upload(client, application_id, name="Diploma.bat").json()
    assert document["original_name"] == "Diploma.pdf"
    download = client.get(f"{ROOT}/{application_id}/documents/{document['id']}")
    assert 'filename="Diploma.pdf"' in download.headers["content-disposition"]
    jpeg = upload(client, application_id, content=b"\xff\xd8\xff\xe0" + b"2" * 300, name="photo.png").json()
    assert jpeg["content_type"] == "image/jpeg" and jpeg["original_name"] == "photo.jpg"


def test_count_and_storage_limits(app_client, monkeypatch):
    from app.applications import router as applications_router

    client, _, _, folder = app_client
    monkeypatch.setattr(applications_router, "MAX_DOCUMENTS", 2)
    monkeypatch.setattr(applications_router, "MAX_LIVE_APPLICATIONS", 2)
    monkeypatch.setenv("APPLICANT_MAX_BYTES", str(len(PDF) * 3 + 10))
    get_settings.cache_clear()
    first = start(client).json()
    assert upload(client, first["id"]).status_code == 201
    assert upload(client, first["id"]).status_code == 201
    third = upload(client, first["id"])
    assert third.status_code == 409 and third.json()["error_code"] == "TOO_MANY_DOCUMENTS"
    second = start(client, kind="international").json()
    assert upload(client, second["id"]).status_code == 201  # 3 PDFs: the account limit is now almost reached
    full = upload(client, second["id"])
    assert full.status_code == 413 and full.json()["error_code"] == "ACCOUNT_STORAGE_FULL"
    assert client.delete(f"{ROOT}/{second['id']}").status_code == 204
    start(client, kind="international")
    assert start(client, program="empty").json()["error_code"] == "TOO_MANY_APPLICATIONS"
    assert len(list(folder.iterdir())) == 2


def test_uploads_pause_when_the_disk_is_nearly_full(app_client, monkeypatch):
    client, _, _, folder = app_client
    application_id = start(client).json()["id"]
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(storage.shutil, "disk_usage", lambda path: usage(10**12, 10**12 - 10**6, 10**6))
    paused = upload(client, application_id)
    assert paused.status_code == 507 and paused.json()["error_code"] == "UPLOADS_PAUSED"
    assert not folder.exists() or list(folder.iterdir()) == []


def test_start_rules_for_archived_programmes_and_locked_deletes(app_client):
    from app.catalogue.models import Program

    client, session, _, _ = app_client
    application = submitted(client)
    officer(client, session)
    assert client.post(f"{STAFF}/{application['id']}/status", json={"status": "needs_changes", "note": "x"}).status_code == 200
    assert client.delete(f"{ROOT}/{application['id']}").json()["error_code"] == "APPLICATION_LOCKED"
    session.get(Program, "cs").is_active = False
    session.flush()
    assert start(client, kind="international").json()["error_code"] == "PROGRAM_NOT_FOUND"


@pytest.mark.parametrize(
    "first,second,code",
    [
        ("in_review", "in_review", 409),
        ("rejected", None, None),
        ("in_review", "submitted", 422),
    ],
)
def test_status_change_rules(app_client, first, second, code):
    client, session, _, _ = app_client
    application = submitted(client)
    officer(client, session)
    if first == "rejected":
        assert client.post(f"{STAFF}/{application['id']}/status", json={"status": "rejected"}).json()["error_code"] == "NOTE_REQUIRED"
        assert client.post(f"{STAFF}/{application['id']}/status", json={"status": "rejected", "note": "   "}).json()["error_code"] == "NOTE_REQUIRED"
        return
    assert client.post(f"{STAFF}/{application['id']}/status", json={"status": first}).status_code == 200
    assert client.post(f"{STAFF}/{application['id']}/status", json={"status": second}).status_code == code


def test_staff_status_change_rejects_other_origins(app_client):
    client, session, _, _ = app_client
    application = submitted(client)
    officer(client, session)
    response = client.post(
        f"{STAFF}/{application['id']}/status", json={"status": "in_review"}, headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403


def test_queue_order_filters_and_paging(app_client):
    client, session, _, _ = app_client
    local = start(client).json()
    international = start(client, kind="international").json()
    for application in (international, local):  # the later id is submitted first
        ready(client, application["id"])
        assert client.post(f"{ROOT}/{application['id']}/submit").status_code == 200
    officer(client, session)
    assert [item["id"] for item in client.get(STAFF).json()["items"]] == [international["id"], local["id"]]
    assert client.get(STAFF, params={"program_id": "cs"}).json()["total"] == 2
    assert client.get(STAFF, params={"program_id": "empty"}).json()["total"] == 0
    page = client.get(STAFF, params={"limit": 1, "offset": 1}).json()
    assert page["total"] == 2 and [item["id"] for item in page["items"]] == [local["id"]]
    assert client.get(STAFF, params={"limit": 101}).status_code == 422
    client.post(f"{STAFF}/{local['id']}/status", json={"status": "needs_changes", "note": "x"})
    assert [item["id"] for item in client.get(STAFF).json()["items"]] == [international["id"]]  # "open" excludes it
    assert client.get(STAFF, params={"status": "needs_changes"}).json()["total"] == 1


def test_both_switches_are_needed(logged_in, uploads, monkeypatch):
    client, _, _ = logged_in
    monkeypatch.setenv("APPLICANT_ACCOUNTS_ENABLED", "false")
    get_settings.cache_clear()
    for path in (ROOT, STAFF):
        response = client.get(path)
        assert response.status_code == 503 and response.json()["error_code"] == "APPLICATIONS_UNAVAILABLE"
    assert client.get("/api/features").json() == {"applicant_accounts": False, "applications": False}
    monkeypatch.setenv("APPLICANT_ACCOUNTS_ENABLED", "true")
    get_settings.cache_clear()
    assert client.get("/api/features").json() == {"applicant_accounts": True, "applications": True}


def test_failed_file_delete_does_not_fail_the_request(app_client, monkeypatch):
    client, _, _, _ = app_client
    application_id = start(client).json()["id"]
    document_id = upload(client, application_id).json()["id"]

    def broken(self, missing_ok=False):
        raise PermissionError("read-only volume")

    monkeypatch.setattr(Path, "unlink", broken)
    assert client.delete(f"{ROOT}/{application_id}/documents/{document_id}").status_code == 204


def test_stale_drafts_and_orphaned_files_are_cleaned_up(app_client):
    from datetime import timedelta

    from app.applicant.service import now
    from app.applications.service import storage_maintenance

    client, session, _, folder = app_client
    stale = start(client).json()
    assert upload(client, stale["id"]).status_code == 201
    kept = start(client, kind="international").json()
    assert upload(client, kept["id"]).status_code == 201
    session.get(Application, stale["id"]).updated_at = now() - timedelta(days=31)
    session.flush()
    old, recent, partial = folder / ("a" * 32), folder / ("b" * 32), folder / ".cccc.part"
    for path in (old, recent, partial):
        path.write_bytes(b"x")
    hour_ago = time.time() - 7200
    os.utime(old, (hour_ago, hour_ago))
    os.utime(partial, (hour_ago, hour_ago))
    storage_maintenance(session, get_settings())
    assert session.get(Application, stale["id"]) is None
    assert session.get(Application, kept["id"]) is not None
    remaining = {path.name for path in folder.iterdir()}
    assert old.name not in remaining and partial.name not in remaining and recent.name in remaining
    assert len(remaining) == 2  # the kept application's scan and the recent file


def test_hourly_run_includes_status_e_mails_and_storage_maintenance(monkeypatch):
    from app.applicant import reminders
    from app.applications import service

    calls = []

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(reminders, "get_session", lambda settings: Session())
    monkeypatch.setattr(reminders, "send_due_reminders", lambda session, settings: calls.append("reminders"))
    monkeypatch.setattr("app.applicant.requests.send_request_notifications", lambda session, settings: calls.append("replies"))
    monkeypatch.setattr(service, "send_status_notifications", lambda session, settings: calls.append("status"))
    monkeypatch.setattr(service, "storage_maintenance", lambda session, settings: calls.append("storage"))
    reminders._run(get_settings())
    assert calls == ["reminders", "replies", "status", "storage"]


def test_account_deletion_locks_applications_before_collecting_files(app_client):
    # An upload in flight holds its application's row lock; locking the applications first
    # makes deletion wait for it, so its file is collected too (ADR 0003, review H1).
    from sqlalchemy import event

    client, session, _, _ = app_client
    application_id = start(client).json()["id"]
    assert upload(client, application_id).status_code == 201
    statements = []
    engine = session.get_bind()
    listener = lambda conn, cursor, statement, *args: statements.append(" ".join(statement.split()).lower())  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        assert client.delete("/api/applicant/me").status_code == 204
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    lock = next(i for i, sql in enumerate(statements) if sql.startswith("select application.id") and "for update" in sql)
    keys = next(i for i, sql in enumerate(statements) if "select application_document.storage_key" in sql)
    removal = next(i for i, sql in enumerate(statements) if sql.startswith("delete from applicant"))
    assert lock < keys < removal
