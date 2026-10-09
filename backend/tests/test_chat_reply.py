from __future__ import annotations

import json
from contextlib import nullcontext

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.assistant.fallback import FALLBACK_TEMPLATE
from app.assistant.llm import Generation, LlmUnavailable
from app.assistant.service import AssistantService
from app.config import get_settings
from app.db import get_session_factory
from app.followups.models import AdmissionsFollowup
from app.main import app


class ChatLlm:
    def __init__(self, answer: str = "", is_admission_question: bool = False, failure: Exception | None = None):
        self.answer = answer
        self.is_admission_question = is_admission_question
        self.failure = failure
        self.prompts: list[str] = []

    def generate(self, system, prompt, json_schema):
        self.prompts.append(prompt)
        if self.failure:
            raise self.failure
        text = json.dumps({"answer": self.answer, "is_admission_question": self.is_admission_question})
        return Generation(text=text, model="fake", prompt_tokens=1, output_tokens=1, latency_ms=1)


def ask(session, question, llm, history=None):
    return AssistantService(session, get_settings(), llm=llm, history=history).answer(question, "s1")


def logged(session):
    return session.scalars(select(AdmissionsFollowup)).all()


def test_greeting_gets_a_natural_reply_and_is_not_logged(assistant_session):
    llm = ChatLlm("Hi! Ask me anything about admission to SDU.")

    response = ask(assistant_session, "hi", llm)

    assert response.answer == "Hi! Ask me anything about admission to SDU."
    assert response.sources == []
    assert logged(assistant_session) == []


def test_admission_question_without_a_source_is_logged(assistant_session):
    llm = ChatLlm("I don't have official information on that. Please contact the office.", is_admission_question=True)

    response = ask(assistant_session, "Is there a hackathon for applicants?", llm)

    assert response.answer.startswith("I don't have official information")
    assert len(logged(assistant_session)) == 1


def test_a_reply_with_an_invented_number_falls_back(assistant_session):
    llm = ChatLlm("Sure, the parking costs 5000 tenge a month.", is_admission_question=True)

    response = ask(assistant_session, "How much is parking?", llm)

    assert response.answer == FALLBACK_TEMPLATE.format(contact=get_settings().admissions_office_contact)


def test_contact_numbers_are_allowed(assistant_session):
    contact = get_settings().admissions_office_contact
    llm = ChatLlm(f"I don't know that. {contact}", is_admission_question=True)

    response = ask(assistant_session, "Is there a hackathon for applicants?", llm)

    assert response.answer.endswith(contact)


def test_no_model_answer_keeps_the_fallback(assistant_session):
    response = ask(assistant_session, "hi", ChatLlm(failure=LlmUnavailable("limits")))

    assert response.answer == FALLBACK_TEMPLATE.format(contact=get_settings().admissions_office_contact)


def test_model_sees_the_conversation(assistant_session):
    llm = ChatLlm("You're welcome!")

    ask(assistant_session, "thanks a lot", llm, history=[("user", "How much does the dormitory cost?"), ("assistant", "...")])

    assert "How much does the dormitory cost?" in llm.prompts[0]


def test_router_passes_the_session_history(assistant_session, monkeypatch):
    llm = ChatLlm("Glad to help!")
    monkeypatch.setattr("app.assistant.service.get_llm", lambda settings: llm)
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        client = TestClient(app)
        client.post("/api/assistant/ask", json={"question": "How much does the dormitory cost?", "session_id": "h"})
        body = client.post("/api/assistant/ask", json={"question": "thank you!", "session_id": "h"}).json()
    finally:
        app.dependency_overrides.clear()

    assert body["answer"] == "Glad to help!"
    assert "How much does the dormitory cost?" in llm.prompts[-1]
