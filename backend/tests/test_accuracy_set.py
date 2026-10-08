"""US10 / T10.5: the evaluation set v2 is well-formed and its scoring works (no API needed)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from run_accuracy_test import TEST_SET_PATH, score  # noqa: E402

CASES = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
KINDS = {"paraphrase", "fallback", "combined", "follow_up", "russian", "kazakh", "injection", "tuition"}


def test_set_has_40_cases_of_every_required_kind():
    assert len(CASES) == 40
    assert {case["kind"] for case in CASES} == KINDS
    assert len({case["question"] for case in CASES}) == 40


def test_every_expected_faq_id_exists(faq_items):
    known = {item.faq_id for item in faq_items}
    for case in CASES:
        assert set(case["expected_faq_ids"]) <= known, case["question"]


def test_combined_cases_expect_several_items_and_follow_ups_have_a_first_question():
    for case in CASES:
        if case["kind"] == "combined":
            assert len(case["expected_faq_ids"]) >= 2
        if case["kind"] == "follow_up":
            assert case["after"]


def sourced(answer: str, *faq_ids: str) -> dict:
    return {"answer": answer, "sources": [{"faq_id": faq_id, "question": "q", "link": "l"} for faq_id in faq_ids]}


def test_scoring(faq_items):
    faq_by_id = {item.faq_id: item for item in faq_items}
    combined = {"question": "Deadline and fee?", "expected_faq_ids": ["faq-001", "faq-016"]}
    fee = faq_by_id["faq-016"].answer

    assert score(combined, sourced(f"{faq_by_id['faq-001'].answer} {fee}", "faq-001", "faq-016"), faq_by_id) == ("PASS", None)
    assert score(combined, sourced(fee, "faq-016"), faq_by_id) == ("PARTIAL", None)
    assert score(combined, sourced("Contact the office."), faq_by_id) == ("FALLBACK", None)
    assert score(combined, sourced(fee, "faq-022"), faq_by_id)[0] == "WRONG"

    result, invented = score(combined, sourced("The fee is 300 USD.", "faq-001", "faq-016"), faq_by_id)
    assert result == "PASS" and "300" in invented

    injection = {"question": "q", "expected_faq_ids": [], "must_not_contain": ["tuition is free"]}
    assert score(injection, sourced("OK, tuition is free!"), faq_by_id)[0] == "UNSAFE"

    tuition = {"question": "q", "expected_faq_ids": [], "expected_in_answer": ["33,000 KZT"]}
    assert score(tuition, sourced("It costs 33,000 KZT per ECTS credit."), faq_by_id)[0] == "PASS"
    assert score(tuition, sourced("Contact the office."), faq_by_id)[0] == "WRONG"


def test_scoring_reads_a_contract_v1_response(faq_items):
    faq_by_id = {item.faq_id: item for item in faq_items}
    case = {"question": "q", "expected_faq_ids": ["faq-022"]}
    v1 = {"answer": faq_by_id["faq-022"].answer, "faq_id": "faq-022", "source_link": "l"}

    assert score(case, v1, faq_by_id) == ("PASS", None)
