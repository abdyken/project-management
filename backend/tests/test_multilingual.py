from __future__ import annotations

import json
import re
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from app.assistant.language import detect_language
from app.assistant.llm import Generation
from app.assistant.service import AssistantService
from app.config import get_settings
from app.db import get_session_factory
from app.main import app


def by_id(faq_items, faq_id):
    return next(item for item in faq_items if item.faq_id == faq_id)


def ask(session, question: str, **options):
    return AssistantService(session, get_settings(), **options).answer(question, "s1")


@pytest.mark.parametrize(
    "text,language",
    [
        ("How much does the dormitory cost?", "en"),
        ("Сколько стоит общежитие?", "ru"),
        ("Жатақхана қанша тұрады?", "kk"),
        ("ҰБТ керек пе?", "kk"),
        ("Грант бар ма?", "kk"),
        ("Нужно ли сдавать ЕНТ?", "ru"),
        ("6B06102", "en"),
    ],
)
def test_detect_language(text, language):
    assert detect_language(text) == language


def test_kazakh_question_gets_the_official_kazakh_answer(assistant_session, faq_items):
    item = by_id(faq_items, "faq-022")

    response = ask(assistant_session, "Жатақхана қанша тұрады?")

    assert response.faq_id == "faq-022"
    assert response.answer == item.answer_kk
    assert [source.link for source in response.sources] == [item.source_link_kk]


def test_russian_question_gets_the_official_russian_answer(assistant_session, faq_items):
    item = by_id(faq_items, "faq-022")

    response = ask(assistant_session, "Сколько стоит проживание в общежитии?")

    assert response.answer == item.answer_ru
    assert response.sources[0].title == item.question_ru


def test_item_without_an_official_translation_is_given_in_english_with_a_note(assistant_session, faq_items):
    item = by_id(faq_items, "faq-001")
    assert item.answer_kk is None

    response = ask(assistant_session, item.question, language="kk")

    assert response.answer == f"Бұл жауап тек ағылшын тілінде жарияланған:\n{item.answer}"
    assert response.sources[0].link == item.source_link


def test_every_translated_question_finds_its_item(assistant_session, faq_items):
    misses = []
    for item in faq_items:
        for language in ("ru", "kk"):
            question = getattr(item, f"question_{language}")
            if question is None:
                continue
            response = ask(assistant_session, question)
            if response.faq_id != item.faq_id:
                misses.append((item.faq_id, language, response.faq_id))
    translated = sum(1 for item in faq_items for language in ("ru", "kk") if getattr(item, f"question_{language}"))
    assert len(misses) <= translated // 10, misses


def test_fallback_in_the_language_of_the_question(assistant_session):
    response = ask(assistant_session, "Алматыда бүгін ауа райы қандай?")

    assert response.answer.startswith("Бұл ақпарат ресми FAQ-та табылмады.")
    assert "Қаскелең" in response.answer


def test_kazakh_document_checklist(assistant_session):
    response = ask(assistant_session, "Отандық талапкер ретінде 6B06102 бағдарламасына қандай құжаттар қажет?")

    assert response.answer.startswith("Computer Science (бакалавриат, 6B06102) бағдарламасына қажетті құжаттар, отандық талапкер")


def test_russian_catalogue_fee(assistant_session):
    response = ask(assistant_session, "Сколько стоит обучение на 6B06102?")

    assert response.answer.startswith(
        "Стоимость программы Computer Science (бакалавриат, 6B06102) — 33 000 тенге (около 90 USD) за 1 кредит ECTS."
    )


def test_kazakh_title_finds_the_program_and_is_used_in_the_answer(full_catalogue_session):
    response = ask(full_catalogue_session, "Статистика және деректер ғылымы бағдарламасының оқу ақысы қанша?")

    assert response.answer.startswith(
        "Статистика және деректер ғылымы (бакалавриат, 6B05402) бағдарламасының құны — 1 ECTS кредиті үшін 28 500 теңге"
    )


def test_model_gets_the_items_in_the_language_of_the_question(assistant_session, faq_items):
    item = by_id(faq_items, "faq-022")

    class Recorder:
        prompts: list[str] = []

        def generate(self, system, prompt, json_schema):
            self.prompts.append(prompt)
            given = json.loads(re.search(r"<faq_items>\n(.*)\n</faq_items>", prompt, re.S).group(1))
            reply = {"answer": given[0]["answer"], "cited_faq_ids": [given[0]["faq_id"]]}
            return Generation(text=json.dumps(reply, ensure_ascii=False), model="fake", prompt_tokens=1, output_tokens=1, latency_ms=1)

    llm = Recorder()
    response = ask(assistant_session, "Жатақхана қанша тұрады?", llm=llm)

    assert item.answer_kk in llm.prompts[0]
    assert response.answer == item.answer_kk
    assert response.sources[0].link == item.source_link_kk


@pytest.fixture
def client(assistant_session):
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_follow_up_keeps_the_language_of_the_applicant(client):
    first = client.post(
        "/api/assistant/ask",
        json={"question": "Отандық талапкер ретінде 6B06102 бағдарламасына қандай құжаттар қажет?", "session_id": "kk"},
    ).json()["answer"]
    follow_up = client.post(
        "/api/assistant/ask", json={"question": "Ал шетелдік талапкерлерге ше?", "session_id": "kk"}
    ).json()["answer"]

    assert "отандық талапкер" in first
    assert follow_up.startswith("Computer Science (бакалавриат, 6B06102) бағдарламасына қажетті құжаттар, шетелдік талапкер")


@pytest.mark.parametrize("lang,expected", [("ru", "Нужно ли сдавать ЕНТ для поступления на бакалавриат?"), ("kk", "Бакалавриатқа түсу үшін ҰБТ тапсыру қажет пе?")])
def test_suggestions_in_the_chosen_language(client, lang, expected):
    suggestions = client.get("/api/assistant/suggestions", params={"session_id": f"new-{lang}", "lang": lang}).json()[
        "suggestions"
    ]

    assert len(suggestions) == 4
    assert expected in suggestions


def test_unknown_suggestion_language_is_rejected(client):
    response = client.get("/api/assistant/suggestions", params={"session_id": "x", "lang": "de"})

    assert response.status_code == 422
