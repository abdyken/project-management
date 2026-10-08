from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from app.assistant.catalogue_tools import has_missing_values
from app.assistant.schemas import FaqItem

_DIGITS = re.compile(r"\d+")


def check_grounding(
    answer: str, cited_faq_ids: list[str], given: list[FaqItem], question: str
) -> tuple[list[FaqItem], str | None]:
    if not answer.strip():
        return [], "empty answer"
    by_id = {item.faq_id: item for item in given}
    unknown = [faq_id for faq_id in cited_faq_ids if faq_id not in by_id]
    if unknown:
        return [], f"cites faq_ids it was not given: {unknown}"
    cited = [by_id[faq_id] for faq_id in dict.fromkeys(cited_faq_ids)]
    if not cited:
        return [], "cites no faq_id"

    invented = invented_numbers(answer, [question, *_faq_texts(cited)])
    if invented:
        return [], f"numbers not in the cited items: {invented}"
    return cited, None


def check_catalogue_grounding(
    answer: str,
    cited_faq_ids: list[str],
    cited_program_ids: list[str],
    items: list[FaqItem],
    programs: list[dict[str, Any]],
    question: str,
    contact: str,
) -> tuple[list[FaqItem], list[dict[str, Any]], str | None]:
    if not answer.strip():
        return [], [], "empty answer"
    faq_by_id = {item.faq_id: item for item in items}
    program_by_id = {facts["program_id"]: facts for facts in programs}
    unknown = [faq_id for faq_id in cited_faq_ids if faq_id not in faq_by_id]
    unknown += [program_id for program_id in cited_program_ids if program_id not in program_by_id]
    if unknown:
        return [], [], f"cites ids it was not given: {unknown}"
    cited_items = [faq_by_id[faq_id] for faq_id in dict.fromkeys(cited_faq_ids)]
    cited_programs = [program_by_id[program_id] for program_id in dict.fromkeys(cited_program_ids)]
    if not cited_items and not cited_programs:
        return [], [], "cites no source"

    allowed = [question, *_faq_texts(cited_items), *(json.dumps(facts, ensure_ascii=False) for facts in cited_programs)]
    if any(has_missing_values(facts) for facts in cited_programs):
        allowed.append(contact)
    invented = invented_numbers(answer, allowed)
    if invented:
        return [], [], f"numbers not in the cited sources: {invented}"
    return cited_items, cited_programs, None


def invented_numbers(answer: str, allowed_texts: Iterable[str]) -> list[str]:
    return sorted(_numbers([answer]) - _numbers(allowed_texts), key=int)


def _faq_texts(items: list[FaqItem]) -> list[str]:
    return [text for item in items for text in (item.question, item.answer)]


def _numbers(texts: Iterable[str]) -> set[str]:
    return {match.lstrip("0") or "0" for text in texts for match in _DIGITS.findall(text)}
