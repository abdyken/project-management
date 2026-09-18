"""T1.1: program table - migration applied and model constraints (needs the database)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalogue.models import Program
from app.config import get_settings
from app.db import get_engine


@pytest.fixture(scope="module")
def engine():
    command.upgrade(Config("alembic.ini"), "head")
    return get_engine(get_settings())


@pytest.fixture
def session(engine):
    """Each test runs in a transaction that is rolled back, so the database stays clean."""
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()


def make_program(**overrides) -> Program:
    fields = {
        "program_id": "test-cs-bsc",
        "title": "Computer Science",
        "faculty": "Faculty of Engineering",
        "degree_level": "bachelor",
        "language": "English",
    }
    return Program(**(fields | overrides))


def test_program_table_has_agreed_columns(engine):
    columns = {column["name"] for column in inspect(engine).get_columns("program")}

    assert columns == {
        "program_id",
        "title",
        "faculty",
        "degree_level",
        "language",
        "tuition_fee",
        "application_deadline",
        "is_active",
    }


def test_program_round_trip(session):
    session.add(
        make_program(tuition_fee=Decimal("2500000.00"), application_deadline=date(2026, 8, 1))
    )
    session.flush()
    session.expire_all()

    program = session.get(Program, "test-cs-bsc")

    assert program.title == "Computer Science"
    assert program.tuition_fee == Decimal("2500000.00")
    assert program.application_deadline == date(2026, 8, 1)
    assert program.is_active is True


def test_fee_and_deadline_may_be_unknown(session):
    session.add(make_program())
    session.flush()
    session.expire_all()

    program = session.get(Program, "test-cs-bsc")

    assert program.tuition_fee is None
    assert program.application_deadline is None


def test_unknown_degree_level_rejected(session):
    session.add(make_program(degree_level="diploma"))

    with pytest.raises(IntegrityError, match="ck_program_degree_level"):
        session.flush()


def test_negative_tuition_fee_rejected(session):
    session.add(make_program(tuition_fee=Decimal("-1")))

    with pytest.raises(IntegrityError, match="ck_program_tuition_fee_non_negative"):
        session.flush()


def test_duplicate_program_id_rejected(session):
    session.add(make_program())
    session.flush()
    session.add(make_program(title="Another title"))

    with pytest.raises(IntegrityError):
        session.flush()
