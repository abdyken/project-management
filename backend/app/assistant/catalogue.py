from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.assistant import catalogue_tools
from app.assistant.catalogue_tools import NOT_PUBLISHED, program_facts, program_source
from app.assistant.intents import (
    CATALOGUE_FIELDS,
    DEADLINE,
    FACULTY,
    FEE,
    LANGUAGE,
    applicant_type_mentioned,
    catalogue_fields,
    degrees_mentioned,
    faculty_mentioned,
    is_comparison,
    is_program_list_question,
    language_mentioned,
    program_titles,
    programs_named_by_code,
    resolve_programs,
    without_titles,
)
from app.assistant.schemas import AnswerSource, Language
from app.assistant.texts import language_names, text
from app.catalogue.models import Program

MAX_COMPARED = 3
APPLICANT_TYPES = ("local", "international")

STANDALONE_QUESTIONS = {
    FEE: "How much is tuition for {program_id}?",
    DEADLINE: "When is the application deadline for {program_id}?",
    LANGUAGE: "What is the language of instruction for {program_id}?",
    FACULTY: "Which faculty offers {program_id}?",
}
_DEGREE_NAMES = {"bachelor": "bachelor's", "master": "master's", "phd": "PhD"}


@dataclass(frozen=True)
class CatalogueRequest:
    programs: list[dict[str, Any]]
    fields: tuple[str, ...]
    applicant_type: str | None = None
    ambiguous: bool = False
    listing: dict[str, str] | None = None
    by_code: bool = False


@dataclass(frozen=True)
class CatalogueAnswer:
    text: str
    sources: list[AnswerSource]


def catalogue_request(session: Session, question: str, programs: list[Program]) -> CatalogueRequest | None:
    matched = _in_mention_order(question, resolve_programs(question, programs))
    rest = without_titles(question, matched)
    fields = catalogue_fields(rest)
    compare = is_comparison(question)
    applicant_type = applicant_type_mentioned(rest)

    if matched:
        if not fields and not compare:
            return None
        named = programs_named_by_code(question, programs)
        ambiguous = len(matched) > 1 and not compare and len(named) < 2
        return CatalogueRequest(
            programs=[program_facts(program) for program in matched],
            fields=fields or CATALOGUE_FIELDS,
            applicant_type=applicant_type,
            ambiguous=ambiguous,
            by_code=bool(named),
        )

    if not is_program_list_question(question):
        return None
    filters = _list_filters(question, programs)
    if not filters:
        return None
    return CatalogueRequest(
        programs=catalogue_tools.search_programs(session, **filters),
        fields=fields,
        applicant_type=applicant_type,
        listing=filters,
    )


def summary_request(question: str, programs: list[Program]) -> CatalogueRequest | None:
    matched = resolve_programs(question, programs)
    if len(matched) != 1:
        return None
    return CatalogueRequest(programs=[program_facts(matched[0])], fields=CATALOGUE_FIELDS)


def standalone_question_for(field_name: str, program_id: str) -> str:
    return STANDALONE_QUESTIONS[field_name].format(program_id=program_id)


def answer_from_catalogue(request: CatalogueRequest, contact: str, language: Language = "en") -> CatalogueAnswer:
    if request.listing is not None:
        return _listing(request, language)
    if request.ambiguous:
        return _choose_program(request, language)
    if len(request.programs) > MAX_COMPARED:
        return _too_many(request, language)
    if len(request.programs) > 1:
        return _comparison(request, contact, language)
    return _single(request, contact, language)


def title_in(facts: dict[str, Any], language: Language) -> str:
    return (facts.get(f"title_{language}") if language != "en" else None) or facts["title"]


def label(facts: dict[str, Any], language: Language = "en") -> str:
    return text(
        language,
        "label",
        title=title_in(facts, language),
        degree=text(language, f"degree.{facts['degree_level']}"),
        code=facts["program_id"],
    )


def _in_mention_order(question: str, programs: list[Program]) -> list[Program]:
    lowered = question.lower()

    def position(program: Program) -> int:
        for name in (program.program_id.lower(), *(title.lower() for title in program_titles(program))):
            index = lowered.find(name)
            if index != -1:
                return index
        return len(lowered)

    return sorted(programs, key=position)


def _list_filters(question: str, programs: list[Program]) -> dict[str, str]:
    filters: dict[str, str] = {}
    degrees = degrees_mentioned(question)
    if len(degrees) == 1:
        filters["degree_level"] = next(iter(degrees))
    language = language_mentioned(question)
    if language:
        filters["language"] = language
    faculty = faculty_mentioned(question, sorted({program.faculty for program in programs}))
    if faculty:
        filters["faculty"] = faculty
    return filters


def _applicant_types(request: CatalogueRequest) -> tuple[str, ...]:
    return (request.applicant_type,) if request.applicant_type else APPLICANT_TYPES


def _shown(value: str, language: Language) -> str:
    return text(language, "not_published") if value == NOT_PUBLISHED else value


def _number(value: int, language: Language) -> str:
    formatted = f"{value:,}"
    return formatted if language == "en" else formatted.replace(",", " ")


def _fee(facts: dict[str, Any], language: Language) -> str:
    kzt, usd = facts["tuition_per_ects_kzt"], facts["tuition_per_ects_usd"]
    if kzt is None and usd is None:
        return NOT_PUBLISHED
    if kzt is None:
        return text(language, "fees.usd", usd=_number(usd, language))
    if usd is None:
        return text(language, "fees.kzt", kzt=_number(kzt, language))
    return text(language, "fees.both", kzt=_number(kzt, language), usd=_number(usd, language))


def _language(facts: dict[str, Any], language: Language) -> str:
    value = facts["language"]
    return value if value == NOT_PUBLISHED else language_names(language, value)


def _values(
    facts: dict[str, Any], field_name: str, applicant_types: tuple[str, ...], language: Language
) -> list[tuple[str, str]]:
    if field_name == FEE:
        fee = _fee(facts, language)
        shown = _shown(fee, language) if fee == NOT_PUBLISHED else text(language, "field.fee_value", fee=fee)
        return [(text(language, "field.fee"), shown)]
    if field_name == LANGUAGE:
        return [(text(language, "field.language"), _shown(_language(facts, language), language))]
    if field_name == FACULTY:
        return [(text(language, "field.faculty"), facts["faculty"])]
    return [
        (
            text(language, "field.deadline", kind=text(language, f"kinds.{kind}")),
            _shown(facts[f"deadline_{kind}"], language),
        )
        for kind in applicant_types
    ]


def _missing(value: str, language: Language) -> bool:
    return value in (NOT_PUBLISHED, text(language, "not_published"))


def _page(facts: dict[str, Any]) -> list[AnswerSource]:
    source = program_source(facts)
    return [source] if source is not None else []


def _with_contact(answer: str, missing: bool, contact: str) -> str:
    return f"{answer} {contact}" if missing else answer


def _single(request: CatalogueRequest, contact: str, language: Language) -> CatalogueAnswer:
    facts = request.programs[0]
    name = label(facts, language)
    applicant_types = _applicant_types(request)

    if request.fields == (FEE,):
        fee = _fee(facts, language)
        if fee == NOT_PUBLISHED:
            return CatalogueAnswer(text(language, "fee_missing", label=name, contact=contact), [])
        return CatalogueAnswer(text(language, "fee_answer", label=name, fee=fee, contact=contact), _page(facts))

    if request.fields == (DEADLINE,):
        deadlines = {kind: facts[f"deadline_{kind}"] for kind in applicant_types}
        missing = NOT_PUBLISHED in deadlines.values()
        published = any(value != NOT_PUBLISHED for value in deadlines.values())
        if len(deadlines) == 1:
            kind, value = next(iter(deadlines.items()))
            answer = text(
                language, "deadline_one", kind=text(language, f"kinds.{kind}"), label=name, value=_shown(value, language)
            )
        else:
            answer = text(
                language,
                "deadline_both",
                label=name,
                local=_shown(deadlines["local"], language),
                international=_shown(deadlines["international"], language),
            )
        return CatalogueAnswer(_with_contact(answer, missing, contact), _page(facts) if published else [])

    if request.fields == (LANGUAGE,):
        if facts["language"] == NOT_PUBLISHED:
            return CatalogueAnswer(text(language, "language_missing", label=name, contact=contact), [])
        return CatalogueAnswer(
            text(language, "language_answer", label=name, value=_language(facts, language)), _page(facts)
        )

    if request.fields == (FACULTY,):
        return CatalogueAnswer(text(language, "faculty_answer", label=name, faculty=facts["faculty"]), _page(facts))

    values = [
        value for field_name in request.fields for value in _values(facts, field_name, applicant_types, language)
    ]
    lines = [f"- {title}: {value}" for title, value in values]
    missing = any(_missing(value, language) for _, value in values)
    answer = f"{name}:\n" + "\n".join(lines)
    return CatalogueAnswer(f"{answer}\n{contact}" if missing else answer, _page(facts))


def _comparison(request: CatalogueRequest, contact: str, language: Language) -> CatalogueAnswer:
    programs = request.programs
    names = [label(facts, language) for facts in programs]
    lines = []
    missing = False
    for field_name in request.fields:
        rows = [_values(facts, field_name, _applicant_types(request), language) for facts in programs]
        for index, (title, _) in enumerate(rows[0]):
            cells = [f"{facts['program_id']} {row[index][1]}" for facts, row in zip(programs, rows, strict=True)]
            missing = missing or any(_missing(row[index][1], language) for row in rows)
            lines.append(f"- {title}: " + "; ".join(cells))
    heading = text(language, "comparison", names=_join(names, language))
    answer = heading + "\n" + "\n".join(lines)
    sources = list({source.link: source for facts in programs for source in _page(facts)}.values())
    return CatalogueAnswer(f"{answer}\n{contact}" if missing else answer, sources)


def _choose_program(request: CatalogueRequest, language: Language) -> CatalogueAnswer:
    example = request.programs[0]
    question = text(
        language,
        f"example.{request.fields[0]}",
        title=title_in(example, language),
        program_id=example["program_id"],
    )
    labels = "; ".join(label(facts, language) for facts in request.programs)
    return CatalogueAnswer(text(language, "choose_program", labels=labels, example=question), [])


def _too_many(request: CatalogueRequest, language: Language) -> CatalogueAnswer:
    first, second = request.programs[0], request.programs[1]
    return CatalogueAnswer(
        text(
            language,
            "too_many",
            count=len(request.programs),
            labels="; ".join(label(facts, language) for facts in request.programs),
            max=MAX_COMPARED,
            first=first["program_id"],
            second=second["program_id"],
        ),
        [],
    )


def _listing(request: CatalogueRequest, language: Language) -> CatalogueAnswer:
    filters = request.listing or {}
    description = _describe(filters, language)
    if not request.programs:
        return CatalogueAnswer(text(language, "listing_empty", description=description), [])
    applicant_types = _applicant_types(request)
    lines = []
    for facts in request.programs:
        extra = [
            f"{title.lower()} {value}" if field_name == DEADLINE else value
            for field_name in request.fields
            if field_name not in (LANGUAGE,)
            for title, value in _values(facts, field_name, applicant_types, language)
        ]
        shown_language = _shown(_language(facts, language), language)
        lines.append("- " + ", ".join([label(facts, language), shown_language, *extra]))
    heading = text(language, "listing", count=len(request.programs), description=description)
    return CatalogueAnswer(heading + "\n" + "\n".join(lines), [])


def _describe(filters: dict[str, str], language: Language) -> str:
    degree = filters.get("degree_level")
    if language == "en":
        description = f"{_DEGREE_NAMES[degree]} programs" if degree else "programs"
        if filters.get("language"):
            description += f" taught in {filters['language']}"
        if filters.get("faculty"):
            description += f" at the {filters['faculty']}"
        return description
    parts = []
    if degree:
        parts.append(text(language, f"degree.{degree}"))
    if filters.get("language"):
        parts.append(f"{text(language, 'field.language').lower()}: {language_names(language, filters['language'])}")
    if filters.get("faculty"):
        parts.append(filters["faculty"])
    return ", ".join(parts)


def _join(names: list[str], language: Language) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + text(language, "and") + names[-1]
