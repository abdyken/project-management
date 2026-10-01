"""US11 T11.2: follow-up questions become standalone questions (no database)."""
from __future__ import annotations

import pytest

from app.catalogue.models import Program
from app.conversation.context import standalone_question
from app.conversation.models import ASSISTANT, USER, ChatTurn

PROGRAMS = [
    Program(program_id="6B06102", title="Computer Science", faculty="IT", degree_level="bachelor", language="English"),
    Program(program_id="6B06101", title="Information Systems", faculty="IT", degree_level="bachelor", language="English"),
    Program(program_id="6B04201", title="Applied Law", faculty="Law", degree_level="bachelor", language="English"),
]


def history(*questions: str) -> list[ChatTurn]:
    turns = []
    for question in questions:
        turns.append(ChatTurn(session_id="s1", role=USER, text=question))
        turns.append(ChatTurn(session_id="s1", role=ASSISTANT, text="(answer)"))
    return turns


def rewrite(question: str, *earlier: str) -> str:
    return standalone_question(question, history(*earlier), PROGRAMS)


LOCAL_DOCS = "Which documents do I need for 6B06102 as a local applicant?"


@pytest.mark.parametrize(
    "follow_up",
    [
        "and as an international applicant?",
        "And for international students?",
        "international?",
        "what about international applicants?",
        "А для иностранцев?",
    ],
)
def test_applicant_type_follow_up_keeps_program_and_topic(follow_up):
    assert rewrite(follow_up, LOCAL_DOCS) == "Which documents do I need for 6B06102 as an international applicant?"


def test_program_follow_up_keeps_topic_and_applicant_type():
    assert rewrite("and for 6B06101?", LOCAL_DOCS) == "Which documents do I need for 6B06101 as a local applicant?"


def test_program_named_by_title_in_a_follow_up():
    assert (
        rewrite("and for Information Systems?", LOCAL_DOCS)
        == "Which documents do I need for 6B06101 as a local applicant?"
    )


def test_topic_follow_up_keeps_program():
    assert rewrite("and the fee?", LOCAL_DOCS) == "How much is tuition for 6B06102?"
    assert rewrite("and how much is it?", "How much is tuition for Applied Law?") == "How much is tuition for 6B04201?"


def test_full_document_question_keeps_the_earlier_applicant_type():
    assert (
        rewrite("Which documents do I need for 6B06101?", "Which documents for 6B06102 as an international applicant?")
        == "Which documents do I need for 6B06101 as an international applicant?"
    )


def test_context_survives_a_chain_of_follow_ups():
    earlier = (LOCAL_DOCS, "and as an international applicant?")
    assert rewrite("and the fee?", *earlier) == "How much is tuition for 6B06102?"
    assert rewrite("and for 6B06101?", *earlier) == "Which documents do I need for 6B06101 as an international applicant?"


@pytest.mark.parametrize(
    "question",
    [
        "How much does the dormitory cost?",
        "Dormitory price?",
        "When is the application deadline?",
        "Thanks!",
        "and?",
        "What English level do I need?",
        "Which documents do I need for 6B06101 as a local applicant?",
    ],
)
def test_questions_with_their_own_subject_are_not_rewritten(question):
    assert rewrite(question, LOCAL_DOCS) == question


def test_no_history_means_no_rewrite():
    assert standalone_question("and as an international applicant?", [], PROGRAMS) == "and as an international applicant?"


def test_follow_up_without_a_known_program_is_left_alone():
    assert rewrite("and as an international applicant?", "When is the application deadline?") == (
        "and as an international applicant?"
    )


def test_only_the_applicants_own_questions_are_used():
    turns = [ChatTurn(session_id="s1", role=ASSISTANT, text="Required documents for 6B06102, local applicant: ...")]
    assert standalone_question("and as an international applicant?", turns, PROGRAMS) == (
        "and as an international applicant?"
    )
