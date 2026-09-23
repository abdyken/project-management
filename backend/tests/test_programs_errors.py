from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.main import app


@pytest.fixture
def client_without_database():
    engine = create_engine(
        "postgresql+psycopg://nobody:nothing@127.0.0.1:1/none",
        connect_args={"connect_timeout": 1},
    )

    def unreachable_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = unreachable_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        engine.dispose()


@pytest.fixture
def client_with_empty_catalogue(catalogue_session):
    app.dependency_overrides[get_db_session] = lambda: catalogue_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)


def test_database_unavailable_returns_503_with_error_code(client_without_database):
    response = client_without_database.get("/api/programs", params={"q": "computer"})

    assert response.status_code == 503
    assert response.json() == {
        "error_code": "DATABASE_UNAVAILABLE",
        "message": "The service is temporarily unavailable. Please try again.",
    }
    assert response.headers["Retry-After"] == "5"


def test_no_matching_programs_returns_200_with_empty_list(client_with_empty_catalogue):
    response = client_with_empty_catalogue.get("/api/programs", params={"q": "no such program"})

    assert response.status_code == 200
    assert response.json() == {"total": 0, "programs": []}


def test_empty_catalogue_returns_200_with_total_zero(client_with_empty_catalogue):
    response = client_with_empty_catalogue.get("/api/programs")

    assert response.status_code == 200
    assert response.json() == {"total": 0, "programs": []}


def test_503_is_documented_in_openapi():
    operation = app.openapi()["paths"]["/api/programs"]["get"]

    assert "503" in operation["responses"]
    assert operation["responses"]["503"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")
