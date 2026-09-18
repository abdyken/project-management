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


def test_program_round_trip(catalogue_session):
    catalogue_session.add(
        make_program(tuition_fee=Decimal("2500000.00"), application_deadline=date(2026, 8, 1))
    )
    catalogue_session.flush()
    catalogue_session.expire_all()

    program = catalogue_session.get(Program, "test-cs-bsc")

    assert program.title == "Computer Science"
    assert program.tuition_fee == Decimal("2500000.00")
    assert program.application_deadline == date(2026, 8, 1)
    assert program.is_active is True


def test_fee_and_deadline_may_be_unknown(catalogue_session):
    catalogue_session.add(make_program())
    catalogue_session.flush()
    catalogue_session.expire_all()

    program = catalogue_session.get(Program, "test-cs-bsc")

    assert program.tuition_fee is None
    assert program.application_deadline is None


def test_unknown_degree_level_rejected(catalogue_session):
    catalogue_session.add(make_program(degree_level="diploma"))

    with pytest.raises(IntegrityError, match="ck_program_degree_level"):
        catalogue_session.flush()


def test_negative_tuition_fee_rejected(catalogue_session):
    catalogue_session.add(make_program(tuition_fee=Decimal("-1")))

    with pytest.raises(IntegrityError, match="ck_program_tuition_fee_non_negative"):
        catalogue_session.flush()


def test_duplicate_program_id_rejected(catalogue_session):
    catalogue_session.add(make_program())
    catalogue_session.flush()
    catalogue_session.add(make_program(title="Another title"))

    with pytest.raises(IntegrityError):
        catalogue_session.flush()
