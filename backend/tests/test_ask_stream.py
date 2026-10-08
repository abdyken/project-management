"""US14: POST /api/assistant/ask/stream (server-sent events)."""
from __future__ import annotations

import json
import time
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.assistant.schemas import Answer
from app.assistant.service import AssistantService
from app.assistant.streaming import MAX_STREAM_SECONDS, chunk_text, pacing, sse_event
from app.conversation.models import ASSISTANT, ChatTurn
from app.db import get_session_factory
from app.main import app

DOCS_LOCAL = "Which documents do I need for 6B06102 as a local applicant?"


# --- chunking and event format (no database) ------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Required documents for Computer Science:\n- Passport (copy)\n- UNT certificate",
        "  leading and trailing spaces  ",
        "one",
        "Құжаттар тізімі: паспорт, аттестат.",
        "",
    ],
)
def test_chunks_join_back_to_exactly_the_answer(text):
    assert "".join(chunk_text(text)) == text


def test_chunks_hold_a_few_words_each():
    assert list(chunk_text("one two three four five six seven", words_per_chunk=3)) == [
        "one two three ",
        "four five six ",
        "seven",
    ]


def test_sse_event_format_keeps_non_ascii():
    assert sse_event("chunk", {"text": "Құжат"}) == 'event: chunk\ndata: {"text": "Құжат"}\n\n'


def test_short_answers_keep_the_configured_pace():
    assert pacing(10, 0.02) == 0.02


def test_long_answers_finish_within_the_maximum_stream_time():
    assert pacing(400, 0.02) * 400 == pytest.approx(MAX_STREAM_SECONDS)


def test_no_pause_when_disabled_or_empty():
    assert pacing(10, 0) == 0
    assert pacing(0, 0.02) == 0


# --- endpoint ------------------------------------------------------------------------


@pytest.fixture
def client(assistant_session, monkeypatch):
    monkeypatch.setenv("STREAM_CHUNK_DELAY_SECONDS", "0")
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def read_events(response) -> list[tuple[str, dict]]:
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def stream(client: TestClient, question: str, session_id: str):
    return client.post("/api/assistant/ask/stream", json={"question": question, "session_id": session_id})


def test_stream_is_server_sent_events_without_proxy_buffering(client):
    response = stream(client, DOCS_LOCAL, "s1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-accel-buffering"] == "no"
    assert response.headers["cache-control"] == "no-cache"


def test_chunks_then_one_done_event(client):
    events = read_events(stream(client, DOCS_LOCAL, "s1"))

    names = [name for name, _ in events]
    assert names[-1] == "done"
    assert names.count("done") == 1
    assert set(names[:-1]) == {"chunk"}
    assert len(names) > 2


def test_streamed_text_equals_the_ask_answer(client):
    streamed = "".join(data["text"] for name, data in read_events(stream(client, DOCS_LOCAL, "s1")) if name == "chunk")
    answered = client.post("/api/assistant/ask", json={"question": DOCS_LOCAL, "session_id": "s2"}).json()["answer"]

    assert streamed == answered


def test_done_event_carries_the_stored_answer_id_and_sources(client, assistant_session, faq_items):
    item = faq_items[0]
    done = read_events(stream(client, item.question, "s1"))[-1][1]

    answer_turn = assistant_session.scalars(
        select(ChatTurn).where(ChatTurn.session_id == "s1", ChatTurn.role == ASSISTANT)
    ).one()
    assert done["answer_id"] == str(answer_turn.id)
    assert done["sources"] == [{"faq_id": item.faq_id, "question": item.question, "link": item.source_link, "title": item.question}]
    assert set(done) == {"answer_id", "sources"}


def test_answer_without_a_source_has_an_empty_source_list(client):
    done = read_events(stream(client, DOCS_LOCAL, "s1"))[-1][1]

    assert done["sources"] == []
    assert set(done) == {"answer_id", "sources"}


def test_follow_ups_work_in_the_stream_too(client):
    stream(client, DOCS_LOCAL, "s1")

    text = "".join(
        data["text"] for name, data in read_events(stream(client, "and as an international applicant?", "s1"))
        if name == "chunk"
    )

    assert "6B06102" in text and "international applicant" in text


def test_slow_answer_returns_the_same_504_as_ask(client, monkeypatch):
    monkeypatch.setenv("ASSISTANT_TIMEOUT_SECONDS", "0.05")
    monkeypatch.setattr(AssistantService, "answer", lambda self, question, session_id: time.sleep(0.3))

    response = stream(client, DOCS_LOCAL, "s1")

    assert response.status_code == 504
    assert response.json()["error_code"] == "ASSISTANT_TIMEOUT"


def test_invalid_request_returns_the_same_error_as_ask(client):
    response = stream(client, "", "s1")

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_REQUEST"


def test_fallback_answers_stream_like_any_other(client, monkeypatch):
    fallback = Answer(answer="I could not find this. Contact the office.", source_link=None, faq_id=None,
                      similarity_score=0.1)
    monkeypatch.setattr(AssistantService, "answer", lambda self, question, session_id: fallback)

    events = read_events(stream(client, "something unrelated", "s1"))

    assert "".join(data["text"] for name, data in events if name == "chunk") == fallback.answer
    assert events[-1][1]["sources"] == []
    assert events[-1][0] == "done"
