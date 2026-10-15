"""US21 catalogue and checklist management: the database as the source of truth, staff
edits visible at once in the catalogue, the checklist and the assistant."""
from __future__ import annotations

import subprocess
import sys
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from app.catalogue.models import Program
from app.db import get_db_session, get_session_factory
from app.main import app
from app.staff.service import create_user, login_limiter

from tests.conftest import BACKEND_ROOT

PASSWORD = "correct horse battery"


@pytest.fixture
def client(full_catalogue_session):
    login_limiter.reset(*list(login_limiter._failures))
    app.dependency_overrides[get_db_session] = lambda: full_catalogue_session
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(full_catalogue_session)
    try:
        yield TestClient(app, base_url="https://testserver")
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def officer(client, full_catalogue_session):
    create_user(full_catalogue_session, "officer@sdu.edu.kz", "Aigerim", "officer", PASSWORD)
    assert client.post("/api/staff/login", json={"email": "officer@sdu.edu.kz", "password": PASSWORD}).status_code == 200
    return client


def _fields(program: dict) -> dict:
    return {key: value for key, value in program.items() if key not in ("program_id", "documents", "updated_at", "updated_by")}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/staff/programs"),
        ("get", "/api/staff/programs/6B04104"),
        ("post", "/api/staff/programs"),
        ("put", "/api/staff/programs/6B04104"),
        ("put", "/api/staff/programs/6B04104/documents/local"),
    ],
)
def test_every_catalogue_endpoint_needs_login(client, method, path):
    response = getattr(client, method)(path, **({"json": {}} if method in ("post", "put") else {}))
    assert response.status_code == 401


def test_list_includes_document_counts_and_filters(officer):
    items = officer.get("/api/staff/programs", params={"degree_level": "phd"}).json()["items"]
    assert len(items) == 7 and {item["degree_level"] for item in items} == {"phd"}
    finance = officer.get("/api/staff/programs", params={"q": "6B04104"}).json()["items"]
    assert finance[0]["documents_local"] > 0 and finance[0]["documents_international"] > 0
    assert officer.get("/api/staff/programs/0X00000").status_code == 404


def test_fee_edit_is_used_by_the_catalogue_and_the_assistant_at_once(officer):
    program = officer.get("/api/staff/programs/6B04104").json()
    assert program["tuition_per_ects_kzt"] == 41500

    saved = officer.put("/api/staff/programs/6B04104", json={**_fields(program), "tuition_per_ects_kzt": 43000})

    assert saved.status_code == 200 and saved.json()["updated_by"] == "Aigerim"
    assert officer.get("/api/programs/6B04104").json()["tuition_per_ects_kzt"] == 43000
    answer = officer.post(
        "/api/assistant/ask", json={"question": "How much does one ECTS cost for Finance (6B04104)?", "session_id": "us21"}
    ).json()["answer"]
    assert "43,000" in answer or "43 000" in answer
    assert "41,500" not in answer


def test_unknown_values_stay_not_published(officer):
    program = officer.get("/api/staff/programs/6B04104").json()
    saved = officer.put("/api/staff/programs/6B04104", json={**_fields(program), "language": "  ", "deadline_local": None})
    assert saved.json()["language"] is None and saved.json()["deadline_local"] is None
    assert officer.get("/api/programs/6B04104").json()["language"] is None


def test_archived_program_leaves_the_catalogue(officer):
    program = officer.get("/api/staff/programs/6B04104").json()
    officer.put("/api/staff/programs/6B04104", json={**_fields(program), "is_active": False})

    assert officer.get("/api/programs/6B04104").status_code == 404
    assert "6B04104" not in [item["program_id"] for item in officer.get("/api/programs", params={"q": "Finance"}).json()["programs"]]
    archived = officer.get("/api/staff/programs", params={"active": "false"}).json()["items"]
    assert "6B04104" in [item["program_id"] for item in archived]


def test_document_list_replaced_in_order_and_empty_list_warns(officer):
    documents = [
        {"name": "Identity document", "format": "copy", "translation": False, "notarisation": False, "deadline": "With the application"},
        {"name": "School certificate", "format": "original", "translation": True, "notarisation": True, "deadline": "By August 25"},
    ]

    saved = officer.put("/api/staff/programs/6B04104/documents/international", json={"documents": documents})

    assert saved.status_code == 200
    assert [item["name"] for item in saved.json()["documents"]["international"]] == ["Identity document", "School certificate"]
    checklist = officer.get("/api/programs/6B04104/checklist", params={"applicant_type": "international"}).json()
    assert [item["name"] for item in checklist["items"]] == ["Identity document", "School certificate"]
    assert checklist["warning"] is None
    # Another program that shared the same official list keeps its own copy.
    assert len(officer.get("/api/staff/programs/6B06102").json()["documents"]["international"]) > 2

    officer.put("/api/staff/programs/6B04104/documents/international", json={"documents": []})
    empty = officer.get("/api/programs/6B04104/checklist", params={"applicant_type": "international"}).json()
    assert empty["items"] == [] and empty["warning"]


def test_new_program_and_duplicate_code(officer):
    body = {
        "program_id": "6B06199",
        "title": "Data Engineering",
        "faculty": "School of Information Technologies and Applied Mathematics",
        "degree_level": "bachelor",
        "source_url": "https://sdu.edu.kz/en/programs/data-engineering/",
    }
    created = officer.post("/api/staff/programs", json=body)
    assert created.status_code == 201
    assert created.json()["tuition_per_ects_kzt"] is None
    assert created.json()["documents"] == {"local": [], "international": []}
    assert officer.get("/api/programs/6B06199").status_code == 200
    duplicate = officer.post("/api/staff/programs", json=body)
    assert duplicate.status_code == 409 and duplicate.json()["error_code"] == "PROGRAM_EXISTS"


@pytest.mark.parametrize(
    "change",
    [
        {"tuition_per_ects_kzt": -1},
        {"source_url": "http://sdu.edu.kz"},
        {"degree_level": "school"},
        {"title": "  "},
        {"deadline_local": "25.08.2026"},
    ],
)
def test_invalid_program_fields_are_rejected(officer, change):
    program = officer.get("/api/staff/programs/6B04104").json()
    response = officer.put("/api/staff/programs/6B04104", json={**_fields(program), **change})
    assert response.status_code == 422 and response.json()["error_code"] == "INVALID_REQUEST"


def test_invalid_document_is_rejected(officer):
    response = officer.put(
        "/api/staff/programs/6B04104/documents/local",
        json={"documents": [{"name": "Photo", "format": "scan", "deadline": "Now"}]},
    )
    assert response.status_code == 422


def test_start_import_skips_a_filled_catalogue(db_engine):
    from app.config import get_settings
    from app.db import get_session

    with get_session(get_settings()) as session:
        if session.query(Program).count() == 0:
            pytest.skip("needs the dev database with a catalogue")
    result = subprocess.run(
        [sys.executable, "scripts/import_catalogue.py", "--if-empty"], cwd=BACKEND_ROOT, capture_output=True, text=True, check=True
    )
    assert "import skipped" in result.stdout
