"""US10 / T10.3: grounding check of model answers (no database, no model)."""
from __future__ import annotations

from app.assistant.grounding import check_grounding
from app.assistant.schemas import FaqItem


def item(faq_id: str, answer: str, question: str = "Question?") -> FaqItem:
    return FaqItem(
        faq_id=faq_id, question=question, answer=answer, category="deadlines",
        source_link=f"https://sdu.edu.kz/{faq_id}", last_update="2026-09-01",
    )


DEADLINES = item("faq-001", "The Fall Intake application deadline is 31.07.2026.")
FEE = item("faq-007", "The Student Fee is 200 USD.")
GIVEN = [DEADLINES, FEE]


def test_answer_citing_given_items_with_their_numbers_passes():
    cited, reason = check_grounding(
        "Apply by 31.07.2026 and pay the 200 USD student fee.", ["faq-001", "faq-007"], GIVEN, "Deadline and fee?"
    )
    assert reason is None
    assert cited == [DEADLINES, FEE]


def test_cited_items_keep_citation_order_without_duplicates():
    cited, _ = check_grounding("Fee 200 USD, deadline 31.07.2026.", ["faq-007", "faq-001", "faq-007"], GIVEN, "?")
    assert cited == [FEE, DEADLINES]


def test_invented_number_is_rejected():
    cited, reason = check_grounding("The student fee is 250 USD.", ["faq-007"], GIVEN, "How much is the fee?")
    assert cited == []
    assert "250" in reason


def test_invented_date_is_rejected():
    _, reason = check_grounding("The deadline is 15.08.2026.", ["faq-001"], GIVEN, "Deadline?")
    assert reason is not None
    assert "15" in reason


def test_number_from_another_given_but_uncited_item_is_rejected():
    _, reason = check_grounding("The deadline is 31.07.2026 and the fee is 200 USD.", ["faq-001"], GIVEN, "?")
    assert "200" in reason


def test_number_from_the_question_is_allowed():
    _, reason = check_grounding(
        "For 6B06102 the Fall deadline is 31.07.2026.", ["faq-001"], GIVEN, "Deadline for 6B06102?"
    )
    assert reason is None


def test_reformatted_date_with_same_numbers_passes():
    _, reason = check_grounding("The deadline is 31/7/2026.", ["faq-001"], GIVEN, "Deadline?")
    assert reason is None


def test_answer_without_a_citation_is_rejected():
    assert check_grounding("Apply by 31.07.2026.", [], GIVEN, "?") == ([], "cites no faq_id")


def test_citation_of_an_item_that_was_not_given_is_rejected():
    _, reason = check_grounding("Apply by 31.07.2026.", ["faq-001", "faq-999"], GIVEN, "?")
    assert "faq-999" in reason


def test_empty_answer_is_rejected():
    assert check_grounding("  ", ["faq-001"], GIVEN, "?") == ([], "empty answer")
