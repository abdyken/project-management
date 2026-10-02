"""Grounding check for model answers (US10 / T10.3).

A model answer is used only when it cites at least one of the FAQ items it was
given, cites nothing else, and every number in it (fees, dates, scores,
deadlines) also appears in the cited items or in the applicant's question.
Anything else is rejected and the applicant gets the FAQ answer word for word.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from app.assistant.schemas import FaqItem

# "31.07.2026", "33,000", "5.5", "200", "6B06102" -> digit groups 31/07/2026, 33/000, 5/5, 200, 6/06102
_DIGITS = re.compile(r"\d+")


def check_grounding(
    answer: str, cited_faq_ids: list[str], given: list[FaqItem], question: str
) -> tuple[list[FaqItem], str | None]:
    """The cited items in citation order and None, or [] and the reason for rejecting the answer."""
    if not answer.strip():
        return [], "empty answer"
    by_id = {item.faq_id: item for item in given}
    unknown = [faq_id for faq_id in cited_faq_ids if faq_id not in by_id]
    if unknown:
        return [], f"cites faq_ids it was not given: {unknown}"
    cited = [by_id[faq_id] for faq_id in dict.fromkeys(cited_faq_ids)]
    if not cited:
        return [], "cites no faq_id"

    allowed = _numbers([question, *(text for item in cited for text in (item.question, item.answer))])
    invented = sorted(_numbers([answer]) - allowed, key=int)
    if invented:
        return [], f"numbers not in the cited items: {invented}"
    return cited, None


def _numbers(texts: Iterable[str]) -> set[str]:
    # Leading zeros dropped, so "07" in "31.07.2026" matches "7 July"-style "7" and vice versa.
    return {match.lstrip("0") or "0" for text in texts for match in _DIGITS.findall(text)}
