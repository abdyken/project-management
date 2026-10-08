from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.assistant import catalogue_tools
from app.assistant.catalogue_tools import NOT_PUBLISHED, program_facts
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
    programs_named_by_code,
    resolve_programs,
    without_titles,
)
from app.catalogue.models import Program

MAX_COMPARED = 3
APPLICANT_TYPES = ("local", "international")

EXAMPLE_QUESTIONS = {
    FEE: "How much is tuition for {title} ({program_id})?",
    DEADLINE: "When is the application deadline for {title} ({program_id})?",
    LANGUAGE: "What is the language of instruction for {title} ({program_id})?",
    FACULTY: "Which faculty offers {title} ({program_id})?",
}
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


@dataclass(frozen=True)
class CatalogueAnswer:
    text: str
    links: list[str]


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


def answer_from_catalogue(request: CatalogueRequest, contact: str) -> CatalogueAnswer:
    if request.listing is not None:
        return _listing(request)
    if request.ambiguous:
        return _choose_program(request)
    if len(request.programs) > MAX_COMPARED:
        return _too_many(request)
    if len(request.programs) > 1:
        return _comparison(request, contact)
    return _single(request, contact)


def label(facts: dict[str, Any]) -> str:
    return f"{facts['title']} ({facts['degree_level']}, {facts['program_id']})"


def _in_mention_order(question: str, programs: list[Program]) -> list[Program]:
    lowered = question.lower()

    def position(program: Program) -> int:
        for name in (program.program_id.lower(), program.title.lower()):
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


def _values(facts: dict[str, Any], field_name: str, applicant_types: tuple[str, ...]) -> list[tuple[str, str]]:
    if field_name == FEE:
        fee = facts["tuition_per_ects"]
        return [("Tuition", fee if fee == NOT_PUBLISHED else f"{fee} per ECTS credit")]
    if field_name == LANGUAGE:
        return [("Language of instruction", facts["language"])]
    if field_name == FACULTY:
        return [("Faculty", facts["faculty"])]
    return [(f"Application deadline, {kind} applicants", facts[f"deadline_{kind}"]) for kind in applicant_types]


def _page(facts: dict[str, Any]) -> list[str]:
    return [facts["program_page"]] if facts.get("program_page") else []


def _with_contact(text: str, missing: bool, contact: str) -> str:
    return f"{text} {contact}" if missing else text


def _single(request: CatalogueRequest, contact: str) -> CatalogueAnswer:
    facts = request.programs[0]
    name = label(facts)
    applicant_types = _applicant_types(request)

    if request.fields == (FEE,):
        if facts["tuition_per_ects"] == NOT_PUBLISHED:
            return CatalogueAnswer(f"The catalogue does not publish a tuition fee for {name}. {contact}", [])
        return CatalogueAnswer(
            f"{name} costs {facts['tuition_per_ects']} per ECTS credit. "
            "The total depends on how many ECTS credits you take per semester, so confirm the final amount with "
            f"the Admissions Office. {contact}",
            _page(facts),
        )

    if request.fields == (DEADLINE,):
        deadlines = {kind: facts[f"deadline_{kind}"] for kind in applicant_types}
        missing = NOT_PUBLISHED in deadlines.values()
        published = any(value != NOT_PUBLISHED for value in deadlines.values())
        if len(deadlines) == 1:
            kind, value = next(iter(deadlines.items()))
            text = f"The application deadline for {kind} applicants to {name} is {value}."
        else:
            text = (
                f"Application deadlines for {name}: local applicants {deadlines['local']}, "
                f"international applicants {deadlines['international']}."
            )
        return CatalogueAnswer(_with_contact(text, missing, contact), _page(facts) if published else [])

    if request.fields == (LANGUAGE,):
        return CatalogueAnswer(f"{name} is taught in {facts['language']}.", _page(facts))

    if request.fields == (FACULTY,):
        return CatalogueAnswer(f"{name} is offered by the {facts['faculty']}.", _page(facts))

    values = [value for field_name in request.fields for value in _values(facts, field_name, applicant_types)]
    lines = [f"- {title}: {value}" for title, value in values]
    missing = any(value == NOT_PUBLISHED for _, value in values)
    text = f"{name}:\n" + "\n".join(lines)
    return CatalogueAnswer(f"{text}\n{contact}" if missing else text, _page(facts))


def _comparison(request: CatalogueRequest, contact: str) -> CatalogueAnswer:
    programs = request.programs
    names = [label(facts) for facts in programs]
    lines = []
    missing = False
    for field_name in request.fields:
        rows = [_values(facts, field_name, _applicant_types(request)) for facts in programs]
        for index, (title, _) in enumerate(rows[0]):
            cells = [f"{facts['program_id']} {row[index][1]}" for facts, row in zip(programs, rows, strict=True)]
            missing = missing or any(row[index][1] == NOT_PUBLISHED for row in rows)
            lines.append(f"- {title}: " + "; ".join(cells))
    heading = f"Comparison of {_join(names)}:"
    text = heading + "\n" + "\n".join(lines)
    links = [link for facts in programs for link in _page(facts)]
    return CatalogueAnswer(f"{text}\n{contact}" if missing else text, list(dict.fromkeys(links)))


def _choose_program(request: CatalogueRequest) -> CatalogueAnswer:
    example = request.programs[0]
    question = EXAMPLE_QUESTIONS[request.fields[0]].format(title=example["title"], program_id=example["program_id"])
    return CatalogueAnswer(
        f"Your question matches several programs: {'; '.join(label(facts) for facts in request.programs)}. "
        f'Ask again with the program code, for example: "{question}"',
        [],
    )


def _too_many(request: CatalogueRequest) -> CatalogueAnswer:
    first, second = request.programs[0], request.programs[1]
    return CatalogueAnswer(
        f"Your question matches {len(request.programs)} programs: "
        f"{'; '.join(label(facts) for facts in request.programs)}. "
        f"Name up to {MAX_COMPARED} program codes to compare, for example: "
        f'"Compare {first["program_id"]} and {second["program_id"]}"',
        [],
    )


def _listing(request: CatalogueRequest) -> CatalogueAnswer:
    filters = request.listing or {}
    description = _describe(filters)
    if not request.programs:
        return CatalogueAnswer(f"The catalogue has no {description}.", [])
    applicant_types = _applicant_types(request)
    lines = []
    for facts in request.programs:
        extra = [
            f"{title.lower()} {value}" if field_name == DEADLINE else value
            for field_name in request.fields
            if field_name not in (LANGUAGE,)
            for title, value in _values(facts, field_name, applicant_types)
        ]
        lines.append("- " + ", ".join([label(facts), facts["language"], *extra]))
    return CatalogueAnswer(f"The catalogue lists {len(request.programs)} {description}:\n" + "\n".join(lines), [])


def _describe(filters: dict[str, str]) -> str:
    degree = filters.get("degree_level")
    text = f"{_DEGREE_NAMES[degree]} programs" if degree else "programs"
    if filters.get("language"):
        text += f" taught in {filters['language']}"
    if filters.get("faculty"):
        text += f" at the {filters['faculty']}"
    return text


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
