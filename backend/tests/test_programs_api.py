"""T1.3: GET /api/programs - keyword search, combinable filters, total (needs the database)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.catalogue.models import Program
from app.db import get_db_session
from app.main import app

def make_programs() -> list[Program]:
    return [
        Program(program_id="cs-bsc-en", title="Computer Science", faculty="Engineering",
                degree_level="bachelor", language="English",
                tuition_fee=Decimal("2500000"), application_deadline=date(2026, 8, 1)),
        Program(program_id="cs-msc-en", title="Computer Science", faculty="Engineering",
                degree_level="master", language="English"),
        Program(program_id="cs-bsc-kk", title="Computer Science", faculty="Engineering",
                degree_level="bachelor", language="Kazakh"),
        Program(program_id="law-bsc-en", title="International Law", faculty="Law and Social Sciences",
                degree_level="bachelor", language="English"),
        Program(program_id="ba-msc-en", title="Business Administration", faculty="Business School",
                degree_level="master", language="English"),
        Program(program_id="fin-100", title="Finance 100% Online", faculty="Business School",
                degree_level="bachelor", language="English"),
        Program(program_id="arch-old", title="Architecture", faculty="Engineering",
                degree_level="bachelor", language="English", is_active=False),
    ]


@pytest.fixture
def client(catalogue_session):
    catalogue_session.add_all(make_programs())
    catalogue_session.flush()
    app.dependency_overrides[get_db_session] = lambda: catalogue_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)


def ids(response) -> list[str]:
    return [program["program_id"] for program in response.json()["programs"]]


def test_no_filters_returns_all_active_programs_ordered_by_title(client):
    response = client.get("/api/programs")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert ids(response) == ["ba-msc-en", "cs-bsc-en", "cs-bsc-kk", "cs-msc-en", "fin-100", "law-bsc-en"]


def test_inactive_programs_are_never_returned(client):
    response = client.get("/api/programs", params={"q": "architecture"})

    assert response.json() == {"total": 0, "programs": []}


def test_program_fields_in_response(client):
    response = client.get("/api/programs", params={"q": "computer", "degree_level": "bachelor", "language": "english"})

    assert response.json()["programs"] == [
        {
            "program_id": "cs-bsc-en",
            "title": "Computer Science",
            "faculty": "Engineering",
            "degree_level": "bachelor",
            "language": "English",
            "tuition_fee": 2500000.0,
            "application_deadline": "2026-08-01",
            "is_active": True,
        }
    ]


def test_keyword_matches_title_case_insensitive(client):
    response = client.get("/api/programs", params={"q": "cOmPuTeR"})

    assert ids(response) == ["cs-bsc-en", "cs-bsc-kk", "cs-msc-en"]
    assert response.json()["total"] == 3


def test_keyword_matches_faculty(client):
    response = client.get("/api/programs", params={"q": "business school"})

    assert ids(response) == ["ba-msc-en", "fin-100"]


def test_keyword_wildcards_are_literal(client):
    assert ids(client.get("/api/programs", params={"q": "100%"})) == ["fin-100"]
    assert client.get("/api/programs", params={"q": "%"}).json()["total"] == 1
    assert client.get("/api/programs", params={"q": "_"}).json()["total"] == 0


def test_blank_keyword_means_no_filter(client):
    assert client.get("/api/programs", params={"q": "   "}).json()["total"] == 6


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"faculty": "Engineering"}, ["cs-bsc-en", "cs-bsc-kk", "cs-msc-en"]),
        ({"faculty": "engineering"}, ["cs-bsc-en", "cs-bsc-kk", "cs-msc-en"]),
        ({"degree_level": "master"}, ["ba-msc-en", "cs-msc-en"]),
        ({"language": "Kazakh"}, ["cs-bsc-kk"]),
        ({"faculty": "Engineering", "degree_level": "bachelor"}, ["cs-bsc-en", "cs-bsc-kk"]),
        ({"faculty": "Engineering", "language": "English"}, ["cs-bsc-en", "cs-msc-en"]),
        ({"degree_level": "master", "language": "English"}, ["ba-msc-en", "cs-msc-en"]),
        ({"faculty": "Engineering", "degree_level": "bachelor", "language": "English"}, ["cs-bsc-en"]),
        ({"q": "science", "faculty": "Engineering", "degree_level": "master", "language": "English"}, ["cs-msc-en"]),
        ({"q": "law", "degree_level": "master"}, []),
        ({"faculty": "Engineering", "language": "Russian"}, []),
    ],
)
def test_filters_combine_with_and(client, params, expected):
    response = client.get("/api/programs", params=params)

    assert response.status_code == 200
    assert ids(response) == expected
    assert response.json()["total"] == len(expected)


def test_faculty_filter_is_exact_not_substring(client):
    assert client.get("/api/programs", params={"faculty": "Engin"}).json()["total"] == 0


def test_invalid_degree_level_rejected(client):
    response = client.get("/api/programs", params={"degree_level": "diploma"})

    assert response.status_code == 422
