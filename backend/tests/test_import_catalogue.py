from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select

from app.catalogue.models import Program
from app.checklist.models import ProgramDocumentRequirement
from app.db import get_db_session
from app.main import app

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from import_catalogue import DEFAULT_SOURCE, SourceFile, import_catalogue, load_source


def program(program_id: str, **overrides) -> dict:
    return {
        "program_id": program_id,
        "title": f"Program {program_id}",
        "faculty": "School of Engineering",
        "degree_level": "bachelor",
        "language": "English",
        "tuition_fee": 2000000,
        "application_deadline": "2026-07-31",
        "source_url": "https://sdu.edu.kz/example",
        "documents": {
            "local": [{"name": "UNT certificate", "format": "original", "translation": False,
                       "notarisation": False, "deadline": "Enrolment"}],
        },
        **overrides,
    }


def source(*programs: dict) -> SourceFile:
    return SourceFile.model_validate({"programs": list(programs)})


def snapshot(session) -> tuple[list, list]:
    programs = session.execute(select(Program).order_by(Program.program_id)).scalars().all()
    requirements = session.execute(
        select(ProgramDocumentRequirement).order_by(
            ProgramDocumentRequirement.program_id,
            ProgramDocumentRequirement.applicant_type,
            ProgramDocumentRequirement.display_order,
        )
    ).scalars().all()
    return (
        [(p.program_id, p.title, p.faculty, p.degree_level, p.language, p.tuition_fee,
          p.application_deadline, p.is_active) for p in programs],
        [(r.program_id, r.applicant_type, r.display_order, r.name, r.document_format,
          r.translation_required, r.notarisation_required, r.deadline) for r in requirements],
    )


def test_official_source_file_imports(catalogue_session):
    result = import_catalogue(catalogue_session, load_source(DEFAULT_SOURCE))

    assert result.programs == 12
    assert result.requirements == 171
    assert result.deactivated == []
    active = catalogue_session.scalar(select(func.count()).select_from(Program).where(Program.is_active))
    assert active == 12


def test_second_run_changes_nothing(catalogue_session):
    data = load_source(DEFAULT_SOURCE)
    import_catalogue(catalogue_session, data)
    first = snapshot(catalogue_session)

    import_catalogue(catalogue_session, data)

    assert snapshot(catalogue_session) == first


def test_program_without_documents_gets_the_missing_data_warning(catalogue_session):
    import_catalogue(catalogue_session, source(program("P1", documents=None)))
    app.dependency_overrides[get_db_session] = lambda: catalogue_session
    try:
        response = TestClient(app).get("/api/programs/P1/checklist", params={"applicant_type": "local"})
    finally:
        app.dependency_overrides.pop(get_db_session, None)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert "Admissions Office" in response.json()["warning"]


def test_changed_values_update_the_program_and_replace_its_documents(catalogue_session):
    import_catalogue(catalogue_session, source(program("P1")))

    import_catalogue(
        catalogue_session,
        source(program("P1", title="Renamed", tuition_fee=None, application_deadline=None, documents={
            "international": [{"name": "Passport", "format": "copy", "translation": False,
                               "notarisation": True, "deadline": "Application"}],
        })),
    )

    programs, requirements = snapshot(catalogue_session)
    assert programs == [("P1", "Renamed", "School of Engineering", "bachelor", "English", None, None, True)]
    assert requirements == [("P1", "international", 0, "Passport", "copy", False, True, "Application")]


def test_programs_removed_from_the_source_are_deactivated_and_come_back(catalogue_session):
    import_catalogue(catalogue_session, source(program("P1"), program("P2")))

    result = import_catalogue(catalogue_session, source(program("P1")))

    assert result.deactivated == ["P2"]
    assert catalogue_session.get(Program, "P2").is_active is False

    result = import_catalogue(catalogue_session, source(program("P1"), program("P2")))

    assert result.deactivated == []
    assert catalogue_session.get(Program, "P2").is_active is True


@pytest.mark.parametrize(
    "bad_program",
    [
        program("P1", degree_level="diploma"),
        program("P1", tuition_fee=-1),
        program("P1", application_deadline="31.07.2026"),
        program("P1", documents={"local": [{"name": "X", "format": "scan", "translation": False,
                                             "notarisation": False, "deadline": "Enrolment"}]}),
        program("P1", documents={"refugee": []}),
        program("P1", unexpected_field=True),
        {k: v for k, v in program("P1").items() if k != "faculty"},
    ],
)
def test_invalid_source_is_rejected_before_anything_is_written(bad_program):
    with pytest.raises(ValidationError):
        source(bad_program)


def test_duplicate_program_ids_are_rejected():
    with pytest.raises(ValidationError, match="duplicate program_id"):
        source(program("P1"), program("P1"))
