from __future__ import annotations

import json
import re

import pytest

from app.assistant.catalogue_tools import NOT_PUBLISHED, get_program, search_programs
from app.assistant.generation import CATALOGUE_INSTRUCTION
from app.assistant.llm import Generation, LlmUnavailable
from app.assistant.service import AssistantService
from app.catalogue.models import Program
from app.config import get_settings

CONTACT = get_settings().admissions_office_contact


class FakeLlm:
    def __init__(self, reply=None, failure: Exception | None = None):
        self.reply = reply
        self.failure = failure
        self.prompts: list[str] = []
        self.systems: list[str] = []

    def generate(self, system, prompt, json_schema) -> Generation:
        self.prompts.append(prompt)
        self.systems.append(system)
        if self.failure is not None:
            raise self.failure
        programs = json.loads(re.search(r"<programs>\n(.*?)\n</programs>", prompt, re.S).group(1))
        text = self.reply(programs) if callable(self.reply) else self.reply
        return Generation(text=text, model="fake", prompt_tokens=1, output_tokens=1, latency_ms=1)


def reply(answer: str, programs: list[str], faq_ids: list[str] | None = None) -> str:
    return json.dumps({"answer": answer, "cited_program_ids": programs, "cited_faq_ids": faq_ids or []})


def ask(session, question: str, llm=None):
    return AssistantService(session, get_settings(), llm=llm).answer(question, "s1")


def page(session, program_id: str) -> str:
    return session.get(Program, program_id).source_url


def links(response) -> list[str]:
    return [source.link for source in response.sources]


def test_tools_return_catalogue_facts_with_unknown_values_marked(assistant_session):
    facts = get_program(assistant_session, "7M06101")
    assert facts["tuition_per_ects"] == "27,000 KZT (about USD 90)"
    assert facts["deadline_local"] == NOT_PUBLISHED
    assert facts["program_page"] == page(assistant_session, "7M06101")
    assert get_program(assistant_session, "0X00000") is None

    masters = search_programs(assistant_session, degree_level="master", language="English")
    assert [facts["program_id"] for facts in masters] == ["7M06101", "7M04115"]


def test_fee_per_ects_comes_from_the_catalogue_with_the_program_link(assistant_session):
    response = ask(assistant_session, "How much does one ECTS cost for Information Systems (7M06101)?")

    assert "27,000 KZT (about USD 90) per ECTS credit" in response.answer
    assert links(response) == [page(assistant_session, "7M06101")]
    assert response.source_link == page(assistant_session, "7M06101")


def test_comparison_lists_fee_language_and_both_deadlines_side_by_side(assistant_session):
    response = ask(assistant_session, "Compare 6B06101 and 6B06102")

    lines = response.answer.splitlines()
    assert lines[0] == (
        "Comparison of Information Systems (bachelor, 6B06101) and Computer Science (bachelor, 6B06102):"
    )
    assert "- Tuition: 6B06101 40,000 KZT (about USD 90) per ECTS credit; 6B06102 33,000 KZT (about USD 90) per ECTS credit" in lines
    assert "- Language of instruction: 6B06101 English; 6B06102 English" in lines
    assert "- Application deadline, local applicants: 6B06101 25.08.2026; 6B06102 25.08.2026" in lines
    assert "- Application deadline, international applicants: 6B06101 31.07.2026; 6B06102 31.07.2026" in lines
    assert links(response) == [page(assistant_session, "6B06101"), page(assistant_session, "6B06102")]


def test_two_program_codes_with_a_fee_question_compare_the_fee(assistant_session):
    response = ask(assistant_session, "How much is tuition for 6B06101 and 6B06102?")

    assert response.answer.splitlines() == [
        "Comparison of Information Systems (bachelor, 6B06101) and Computer Science (bachelor, 6B06102):",
        "- Tuition: 6B06101 40,000 KZT (about USD 90) per ECTS credit; 6B06102 33,000 KZT (about USD 90) per ECTS credit",
    ]


def test_unpublished_deadline_is_never_answered_with_a_number(assistant_session):
    response = ask(assistant_session, "When is the application deadline for 7M06101?")

    assert response.answer == (
        "Application deadlines for Information Systems (master, 7M06101): local applicants not published yet, "
        f"international applicants not published yet. {CONTACT}"
    )
    assert response.sources == []


def test_unpublished_deadline_for_one_applicant_type(assistant_session):
    response = ask(assistant_session, "What is the deadline for international applicants to Management (7M04115)?")

    assert response.answer == (
        "The application deadline for international applicants to Management (master, 7M04115) is not published yet. "
        f"{CONTACT}"
    )


def test_published_deadline_for_one_applicant_type(assistant_session):
    response = ask(assistant_session, "Until when can international applicants apply to Applied Law?")

    assert response.answer == (
        "The application deadline for international applicants to Applied Law (bachelor, 6B04201) is 31.07.2026."
    )
    assert links(response) == [page(assistant_session, "6B04201")]


def test_comparison_with_an_unpublished_value_gives_the_office_contact(assistant_session):
    response = ask(assistant_session, "Compare 7M06101 and 7M04115")

    assert "- Application deadline, local applicants: 7M06101 not published yet; 7M04115 not published yet" in (
        response.answer.splitlines()
    )
    assert response.answer.endswith(CONTACT)


def test_language_and_faculty_questions(assistant_session):
    language = ask(assistant_session, "What is the language of instruction for Applied Law?")
    faculty = ask(assistant_session, "Which faculty offers Translation Studies?")

    assert language.answer == "Applied Law (bachelor, 6B04201) is taught in Kazakh, Russian."
    assert faculty.answer == "Translation Studies (bachelor, 6B02302) is offered by the School of Education and Humanities."


def test_several_facts_of_one_program_are_listed(assistant_session):
    response = ask(assistant_session, "What is the fee and the language of Statistics and Data Science?")

    assert response.answer.splitlines() == [
        "Statistics and Data Science (bachelor, 6B05402):",
        "- Tuition: 28,500 KZT (about USD 90) per ECTS credit",
        "- Language of instruction: English",
    ]


def test_title_words_are_not_read_as_a_question_topic(assistant_session):
    response = ask(assistant_session, "How much is tuition for Kazakh Language and Literature?")

    assert response.answer.startswith("Kazakh Language and Literature (bachelor, 6B01701) costs 22,000 KZT")


def test_shared_title_deadline_question_asks_which_program(assistant_session):
    response = ask(assistant_session, "When is the deadline for Information Systems?")

    assert response.answer.startswith("Your question matches several programs:")
    assert '"When is the application deadline for Information Systems (6B06101)?"' in response.answer


def test_comparison_of_more_than_three_programs_asks_to_narrow_down(assistant_session):
    response = ask(assistant_session, "Compare Computer Science, Information Systems, Applied Law and Management")

    assert response.answer.startswith("Your question matches 5 programs:")
    assert "Name up to 3 program codes to compare" in response.answer


def test_program_list_question_uses_the_search_tool(assistant_session):
    response = ask(assistant_session, "Which master programs are taught in English?")

    assert response.answer.splitlines() == [
        "The catalogue lists 2 master's programs taught in English:",
        "- Information Systems (master, 7M06101), English",
        "- Management (master, 7M04115), English",
    ]


def test_program_list_with_no_match(assistant_session):
    response = ask(assistant_session, "Which PhD programs are taught in Russian?")

    assert response.answer == "The catalogue has no PhD programs taught in Russian."


def test_program_named_alone_gets_its_catalogue_summary(assistant_session):
    response = ask(assistant_session, "Tell me about 6B05402")

    assert response.answer.startswith("Statistics and Data Science (bachelor, 6B05402):\n- Tuition:")
    assert links(response) == [page(assistant_session, "6B05402")]


def test_model_answer_from_the_catalogue_cites_the_program_page(assistant_session):
    llm = FakeLlm(reply("Information Systems (7M06101) costs 27,000 KZT, about 90 USD, per ECTS credit.", ["7M06101"]))

    response = ask(assistant_session, "How much does one ECTS cost for Information Systems (7M06101)?", llm)

    assert llm.systems == [CATALOGUE_INSTRUCTION]
    assert response.answer == "Information Systems (7M06101) costs 27,000 KZT, about 90 USD, per ECTS credit."
    assert links(response) == [page(assistant_session, "7M06101")]
    assert response.faq_id is None


def test_model_gets_unpublished_values_marked_and_the_contact(assistant_session):
    llm = FakeLlm(lambda programs: reply(f"Not published yet. {CONTACT}", ["7M06101"]))

    response = ask(assistant_session, "When is the application deadline for 7M06101?", llm)

    programs = json.loads(re.search(r"<programs>\n(.*?)\n</programs>", llm.prompts[0], re.S).group(1))
    assert programs[0]["deadline_local"] == NOT_PUBLISHED
    assert "tuition_per_ects_kzt" in programs[0]
    assert f"<contact>\n{CONTACT}\n</contact>" in llm.prompts[0]
    assert response.answer == f"Not published yet. {CONTACT}"


@pytest.mark.parametrize(
    "model_reply",
    [
        pytest.param(reply("The deadline is 15.08.2026.", ["7M06101"]), id="invented date"),
        pytest.param(reply("A full degree costs 6,480,000 KZT.", ["7M06101"]), id="computed total"),
        pytest.param(reply("27,000 KZT.", ["6B06102"]), id="program it was not given"),
        pytest.param(reply("27,000 KZT.", []), id="no citation"),
        pytest.param("not json", id="not json"),
    ],
)
def test_rejected_model_answer_falls_back_to_the_catalogue_answer(assistant_session, model_reply):
    response = ask(assistant_session, "How much does one ECTS cost for Information Systems (7M06101)?", FakeLlm(model_reply))

    assert response.answer.startswith("Information Systems (master, 7M06101) costs 27,000 KZT (about USD 90)")


def test_contact_numbers_are_allowed_only_for_unpublished_values(assistant_session):
    model_reply = reply(f"6B06102 costs 33,000 KZT. {CONTACT}", ["6B06102"])

    response = ask(assistant_session, "How much is tuition for 6B06102?", FakeLlm(model_reply))

    assert response.answer.startswith("Computer Science (bachelor, 6B06102) costs 33,000 KZT (about USD 90) per ECTS")


def test_no_model_available_falls_back_to_the_catalogue_answer(assistant_session):
    llm = FakeLlm(failure=LlmUnavailable("all limits reached"))

    response = ask(assistant_session, "Compare 6B06101 and 6B06102", llm)

    assert response.answer.startswith("Comparison of Information Systems (bachelor, 6B06101)")


def test_question_with_a_faq_part_sends_the_faq_items_too(assistant_session, faq_items):
    llm = FakeLlm(reply("x", []))

    ask(assistant_session, "How much is tuition for Computer Science and how are tuition fees calculated at SDU?", llm)

    assert '"faq_id": "faq-017"' in llm.prompts[0]


def test_ambiguous_program_question_does_not_use_the_model(assistant_session):
    llm = FakeLlm(reply("x", []))

    response = ask(assistant_session, "What is the price of Information Systems?", llm)

    assert llm.prompts == []
    assert "matches several programs" in response.answer
