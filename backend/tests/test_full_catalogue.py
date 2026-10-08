from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.assistant.service import AssistantService
from app.catalogue.models import Program
from app.checklist.service import get_requirements
from app.config import get_settings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from import_catalogue import DEFAULT_SOURCE, SourceFile, load_source  # noqa: E402

SOURCE = load_source(DEFAULT_SOURCE)


def ask(session, question: str):
    return AssistantService(session, get_settings()).answer(question, "s1")


def test_every_degree_level_is_in_the_catalogue():
    levels = [program.degree_level for program in SOURCE.programs]
    assert (levels.count("bachelor"), levels.count("master"), levels.count("phd")) == (33, 24, 7)
    assert all(program.title_ru and program.title_kk for program in SOURCE.programs)


def test_a_shared_document_list_is_copied_from_its_owner(full_catalogue_session):
    for applicant_type in ("local", "international"):
        finance = [r.name for r in get_requirements(full_catalogue_session, "6B04104", applicant_type)]
        owner = [r.name for r in get_requirements(full_catalogue_session, "6B06102", applicant_type)]
        assert finance == owner and finance


def test_titles_in_three_languages_are_stored(full_catalogue_session):
    program = full_catalogue_session.get(Program, "6B06102")
    assert (program.title, program.title_ru, program.title_kk) == (
        "Computer Science",
        "Компьютерные науки",
        "Компьютерлік ғылымдар",
    )


def test_a_title_shared_by_three_degree_levels_asks_which_program(full_catalogue_session):
    response = ask(full_catalogue_session, "Which documents do I need for Computer Science as a local applicant?")

    assert response.answer.startswith("Your question matches several programs:")
    for code in ("6B06102", "7M06102", "8D06102"):
        assert code in response.answer


def test_a_degree_word_picks_the_program(full_catalogue_session):
    response = ask(full_catalogue_session, "How much is tuition for a master's in Computer Science?")

    assert response.answer.startswith("Computer Science (master, 7M06102) costs 27,000 KZT")


def test_program_without_a_published_list_warns(full_catalogue_session):
    response = ask(full_catalogue_session, "Which documents do I need for 7M04113 as a local applicant?")

    assert response.answer.startswith("The document list for this program is not published yet")


def test_unpublished_language_is_never_guessed(full_catalogue_session):
    response = ask(full_catalogue_session, "What is the language of instruction for 8D06102?")

    assert response.answer.startswith("The catalogue does not publish the language of instruction of Computer science (phd, 8D06102)")
    assert "English" not in response.answer


def test_phd_program_list(full_catalogue_session):
    response = ask(full_catalogue_session, "Which PhD programs are there at the School of Social Sciences, Business and Law?")

    assert response.answer.splitlines()[0] == (
        "The catalogue lists 2 PhD programs at the School of Social Sciences, Business and Law:"
    )


def _program(program_id: str, **overrides) -> dict:
    return {
        "program_id": program_id,
        "title": program_id,
        "faculty": "School",
        "degree_level": "bachelor",
        "language": None,
        "tuition_per_ects_kzt": None,
        "tuition_per_ects_usd": None,
        "deadline_local": None,
        "deadline_international": None,
        "source_url": "https://sdu.edu.kz/x",
        **overrides,
    }


def test_documents_from_must_name_a_program_with_its_own_list():
    with pytest.raises(ValidationError, match="documents_from"):
        SourceFile.model_validate({"programs": [_program("a"), _program("b", documents_from="a")]})


def test_documents_and_documents_from_are_exclusive():
    documents = {"local": [{"name": "x", "format": "copy", "translation": False, "notarisation": False, "deadline": "d"}]}
    with pytest.raises(ValidationError, match="not both"):
        SourceFile.model_validate({"programs": [_program("a", documents=documents, documents_from="a")]})
