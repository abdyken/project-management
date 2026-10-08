from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_catalogue_answers import cases, check, load_programs  # noqa: E402

from app.assistant.service import AssistantService  # noqa: E402
from app.config import get_settings  # noqa: E402

PROGRAMS = {program["program_id"]: program for program in load_programs()}
CASES = cases(list(PROGRAMS.values()))


def test_every_program_is_checked_for_fee_deadline_and_language():
    assert len(CASES) == 3 * len(PROGRAMS)
    assert {case.topic for case in CASES} == {"fee", "deadline", "language"}


@pytest.mark.parametrize("case", CASES, ids=lambda case: f"{case.program_id}-{case.topic}")
def test_catalogue_answer_matches_the_catalogue(full_catalogue_session, case):
    response = AssistantService(full_catalogue_session, get_settings()).answer(case.question, "s1")

    assert check(case, response.answer, PROGRAMS[case.program_id]) is None, response.answer
    if not case.unpublished:
        assert PROGRAMS[case.program_id]["source_url"] in [source.link for source in response.sources]


def test_check_catches_an_invented_fee_and_a_missing_value():
    program = PROGRAMS["7M06101"]
    fee = next(case for case in CASES if case.program_id == "7M06101" and case.topic == "fee")
    deadline = next(case for case in CASES if case.program_id == "7M06101" and case.topic == "deadline")

    assert check(fee, "It costs 27,000 KZT (about USD 90).", program) is None
    assert check(fee, "It costs 27 000 KZT, about USD 90, or 6,480,000 KZT in total.", program) is not None
    assert check(fee, "It costs 25,000 KZT.", program) is not None
    assert check(deadline, "The deadline is 25.08.2026.", program) is not None
    assert check(deadline, "The deadline is not published yet.", program) is None
