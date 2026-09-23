from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.catalogue.models import Program
from app.db import get_db_session
from app.main import app

def make_programs() -> list[Program]:
    return [
        Program(program_id="cs-bsc-en", title="Computer Science", faculty="Engineering",
                degree_level="bachelor", language="English",
                tuition_per_ects_kzt=33000, tuition_per_ects_usd=90,
                deadline_local=date(2026, 8, 25), deadline_international=date(2026, 7, 31),
                source_url="https://sdu.edu.kz/en/computer-science-3/"),
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
            "tuition_per_ects_kzt": 33000,
            "tuition_per_ects_usd": 90,
            "deadline_local": "2026-08-25",
            "deadline_international": "2026-07-31",
            "source_url": "https://sdu.edu.kz/en/computer-science-3/",
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


def test_get_program_by_id(client):
    response = client.get("/api/programs/cs-bsc-en")

    assert response.status_code == 200
    assert response.json() == {
        "program_id": "cs-bsc-en",
        "title": "Computer Science",
        "faculty": "Engineering",
        "degree_level": "bachelor",
        "language": "English",
        "tuition_per_ects_kzt": 33000,
        "tuition_per_ects_usd": 90,
        "deadline_local": "2026-08-25",
        "deadline_international": "2026-07-31",
        "source_url": "https://sdu.edu.kz/en/computer-science-3/",
        "is_active": True,
    }


@pytest.mark.parametrize("program_id", ["does-not-exist", "arch-old"])
def test_get_unknown_or_inactive_program_returns_404(client, program_id):
    response = client.get(f"/api/programs/{program_id}")

    assert response.status_code == 404
    assert response.json() == {"error_code": "PROGRAM_NOT_FOUND", "message": "Program not found."}


def test_keyword_matches_program_id(client):
    response = client.get("/api/programs", params={"q": "MSC-EN"})

    assert ids(response) == ["ba-msc-en", "cs-msc-en"]
    assert response.json()["total"] == 2


def test_language_filter_matches_one_of_several_languages(catalogue_session):
    from app.catalogue.service import search_programs

    catalogue_session.add_all(
        [
            Program(program_id="ped", title="Pedagogy", faculty="Education", degree_level="bachelor", language="Kazakh, English"),
            Program(program_id="law", title="Law", faculty="Law", degree_level="bachelor", language="Kazakh, Russian"),
            Program(program_id="cs", title="Computer Science", faculty="IT", degree_level="bachelor", language="English"),
        ]
    )
    catalogue_session.flush()

    def ids(language: str) -> list[str]:
        return sorted(program.program_id for program in search_programs(catalogue_session, language=language))

    assert ids("kazakh") == ["law", "ped"]
    assert ids("English") == ["cs", "ped"]
    assert ids("Russian") == ["law"]
    assert ids("Kazakh, English") == []
    assert ids("eng") == []
