"""T1.1: program table - migration applied and model constraints (needs the database)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.catalogue.models import Program


def make_program(**overrides) -> Program:
    fields = {
        "program_id": "test-cs-bsc",
        "title": "Computer Science",
        "faculty": "Faculty of Engineering",
        "degree_level": "bachelor",
        "language": "English",
    }
    return Program(**(fields | overrides))


def test_program_table_has_agreed_columns(db_engine):
    columns = {column["name"] for column in inspect(db_engine).get_columns("program")}

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


def test_program_round_trip(db_session):
    db_session.add(
        make_program(tuition_fee=Decimal("2500000.00"), application_deadline=date(2026, 8, 1))
    )
    db_session.flush()
    db_session.expire_all()

    program = db_session.get(Program, "test-cs-bsc")

    assert program.title == "Computer Science"
    assert program.tuition_fee == Decimal("2500000.00")
    assert program.application_deadline == date(2026, 8, 1)
    assert program.is_active is True


def test_fee_and_deadline_may_be_unknown(db_session):
    db_session.add(make_program())
    db_session.flush()
    db_session.expire_all()

    program = db_session.get(Program, "test-cs-bsc")

    assert program.tuition_fee is None
    assert program.application_deadline is None


def test_unknown_degree_level_rejected(db_session):
    db_session.add(make_program(degree_level="diploma"))

    with pytest.raises(IntegrityError, match="ck_program_degree_level"):
        db_session.flush()


def test_negative_tuition_fee_rejected(db_session):
    db_session.add(make_program(tuition_fee=Decimal("-1")))

    with pytest.raises(IntegrityError, match="ck_program_tuition_fee_non_negative"):
        db_session.flush()


def test_duplicate_program_id_rejected(db_session):
    db_session.add(make_program())
    db_session.flush()
    db_session.add(make_program(title="Another title"))

    with pytest.raises(IntegrityError):
        db_session.flush()
