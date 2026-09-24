from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.catalogue.models import Program
from app.checklist.models import ProgramDocumentRequirement
from app.checklist.service import MISSING_REQUIREMENTS_WARNING
from app.config import get_settings
from app.db import get_db_session
from app.followups.models import MISSING_DOCUMENTS, AdmissionsFollowup
from app.main import app


@pytest.fixture
def client(catalogue_session):
    catalogue_session.add(
        Program(
            program_id="cs-bsc",
            title="Computer Science",
            faculty="Engineering",
            degree_level="bachelor",
            language="English",
            deadline_local=date(2026, 8, 25),
        )
    )
    catalogue_session.add_all(
        [
            ProgramDocumentRequirement(
                program_id="cs-bsc",
                applicant_type="local",
                name="National ID",
                document_format="copy",
                translation_required=False,
                notarisation_required=False,
                deadline="Enrolment",
                display_order=2,
            ),
            ProgramDocumentRequirement(
                program_id="cs-bsc",
                applicant_type="local",
                name="School certificate",
                document_format="original",
                translation_required=False,
                notarisation_required=False,
                deadline="Enrolment",
                display_order=1,
            ),
            ProgramDocumentRequirement(
                program_id="cs-bsc",
                applicant_type="international",
                name="Passport",
                document_format="copy",
                translation_required=True,
                notarisation_required=True,
                deadline="Application",
            ),
        ]
    )
    catalogue_session.flush()
    app.dependency_overrides[get_db_session] = lambda: catalogue_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)


def test_local_checklist_returns_requirements_in_display_order(client):
    response = client.get("/api/programs/cs-bsc/checklist", params={"applicant_type": "local"})

    assert response.status_code == 200
    assert response.json() == {
        "program_id": "cs-bsc",
        "applicant_type": "local",
        "items": [
            {"name": "School certificate", "format": "original", "translation": False, "notarisation": False, "deadline": "Enrolment"},
            {"name": "National ID", "format": "copy", "translation": False, "notarisation": False, "deadline": "Enrolment"},
        ],
        "warning": None,
        "contact": None,
    }


def test_international_checklist_returns_type_specific_requirements(client):
    response = client.get("/api/programs/cs-bsc/checklist", params={"applicant_type": "international"})

    assert response.status_code == 200
    assert response.json()["items"] == [
        {"name": "Passport", "format": "copy", "translation": True, "notarisation": True, "deadline": "Application"}
    ]


def test_missing_requirements_returns_warning_not_an_ambiguous_empty_list(client):
    response = client.get("/api/programs/cs-bsc/checklist", params={"applicant_type": "local"})
    session = app.dependency_overrides[get_db_session]()
    session.query(ProgramDocumentRequirement).delete()
    session.flush()

    response = client.get("/api/programs/cs-bsc/checklist", params={"applicant_type": "local"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["warning"] == MISSING_REQUIREMENTS_WARNING
    assert body["contact"] == get_settings().admissions_office_contact
    logged = session.scalars(select(AdmissionsFollowup)).all()
    assert [(f.kind, f.program_id, f.applicant_type) for f in logged] == [(MISSING_DOCUMENTS, "cs-bsc", "local")]


def test_repeated_page_views_are_logged_once(client):
    session = app.dependency_overrides[get_db_session]()
    session.query(ProgramDocumentRequirement).delete()
    session.flush()

    for _ in range(3):
        client.get("/api/programs/cs-bsc/checklist", params={"applicant_type": "local"})

    assert len(session.scalars(select(AdmissionsFollowup)).all()) == 1


def test_invalid_applicant_type_returns_422_error_contract(client):
    response = client.get("/api/programs/cs-bsc/checklist", params={"applicant_type": "alien"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_REQUEST"
    assert response.json()["message"].startswith("applicant_type:")


def test_unknown_program_returns_the_catalogue_404_contract(client):
    response = client.get("/api/programs/unknown/checklist", params={"applicant_type": "local"})

    assert response.status_code == 404
    assert response.json() == {"error_code": "PROGRAM_NOT_FOUND", "message": "Program not found."}
