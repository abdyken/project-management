from __future__ import annotations

from datetime import date

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
        "tuition_per_ects_kzt",
        "tuition_per_ects_usd",
        "deadline_local",
        "deadline_international",
        "source_url",
        "is_active",
    }


def test_program_round_trip(catalogue_session):
    catalogue_session.add(
        make_program(
            tuition_per_ects_kzt=33000,
            tuition_per_ects_usd=90,
            deadline_local=date(2026, 8, 25),
            deadline_international=date(2026, 7, 31),
            source_url="https://sdu.edu.kz/en/computer-science-3/",
        )
    )
    catalogue_session.flush()
    catalogue_session.expire_all()

    program = catalogue_session.get(Program, "test-cs-bsc")

    assert program.title == "Computer Science"
    assert (program.tuition_per_ects_kzt, program.tuition_per_ects_usd) == (33000, 90)
    assert (program.deadline_local, program.deadline_international) == (date(2026, 8, 25), date(2026, 7, 31))
    assert program.is_active is True


def test_fee_and_deadline_may_be_unknown(catalogue_session):
    catalogue_session.add(make_program())
    catalogue_session.flush()
    catalogue_session.expire_all()

    program = catalogue_session.get(Program, "test-cs-bsc")

    assert program.tuition_per_ects_kzt is None
    assert program.tuition_per_ects_usd is None
    assert program.deadline_local is None
    assert program.deadline_international is None


def test_unknown_degree_level_rejected(catalogue_session):
    catalogue_session.add(make_program(degree_level="diploma"))

    with pytest.raises(IntegrityError, match="ck_program_degree_level"):
        catalogue_session.flush()


@pytest.mark.parametrize(
    "field,constraint",
    [("tuition_per_ects_kzt", "ck_program_tuition_kzt_non_negative"), ("tuition_per_ects_usd", "ck_program_tuition_usd_non_negative")],
)
def test_negative_tuition_rejected(catalogue_session, field, constraint):
    catalogue_session.add(make_program(**{field: -1}))

    with pytest.raises(IntegrityError, match=constraint):
        catalogue_session.flush()


def test_duplicate_program_id_rejected(catalogue_session):
    catalogue_session.add(make_program())
    catalogue_session.flush()
    catalogue_session.add(make_program(title="Another title"))

    with pytest.raises(IntegrityError):
        catalogue_session.flush()
