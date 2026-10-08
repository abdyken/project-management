from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.checklist.service import get_requirements
from app.db import get_db_session
from app.main import app


@pytest.fixture
def client(assistant_session):
    app.dependency_overrides[get_db_session] = lambda: assistant_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_compare_returns_programs_in_the_requested_order_with_document_counts(client, assistant_session):
    response = client.get("/api/programs/compare", params={"ids": "7M06101,6B06102,6B04201"})

    assert response.status_code == 200
    programs = response.json()["programs"]
    assert [program["program_id"] for program in programs] == ["7M06101", "6B06102", "6B04201"]
    computer_science = programs[1]
    assert computer_science["tuition_per_ects_kzt"] == 33000
    assert computer_science["documents_local"] == len(get_requirements(assistant_session, "6B06102", "local"))
    assert computer_science["documents_international"] == len(
        get_requirements(assistant_session, "6B06102", "international")
    )
    assert programs[0]["documents_international"] == 0
    assert programs[0]["deadline_local"] is None


def test_compare_trims_spaces_around_ids(client):
    response = client.get("/api/programs/compare", params={"ids": " 6B06101 , 6B06102 "})

    assert [program["program_id"] for program in response.json()["programs"]] == ["6B06101", "6B06102"]


@pytest.mark.parametrize("ids", ["6B06101", "6B06101,6B06102,6B04201,7M06101", "6B06101,6B06101", "", ",,"])
def test_compare_needs_two_or_three_different_ids(client, ids):
    response = client.get("/api/programs/compare", params={"ids": ids})

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_REQUEST"


def test_compare_with_an_unknown_program_names_it(client):
    response = client.get("/api/programs/compare", params={"ids": "6B06101,0X00000"})

    assert response.status_code == 404
    assert response.json() == {"error_code": "PROGRAM_NOT_FOUND", "message": "Program not found: 0X00000"}


def test_compare_path_is_not_read_as_a_program_id(client):
    assert client.get("/api/programs/compare").status_code == 422
