"""T3.2 DoD: "a manual check of 5 questions returns the expected FAQ item on top"."""
from __future__ import annotations

import pytest

from app.assistant.providers import MockEmbeddingProvider
from app.assistant.retrieval import RetrievalIndex, load_faq_base

FAQ_PATH = "app/data/faq_sample.json"

FIVE_QUESTIONS = [
    ("What is the deadline to apply for the Fall intake?", "faq-001"),
    ("Which documents do international students need to submit?", "faq-002"),
    ("Is there an application fee?", "faq-003"),
    ("What language are bachelor programs taught in?", "faq-004"),
    ("How can I contact the admissions office?", "faq-008"),
]


@pytest.fixture(scope="module")
def index() -> RetrievalIndex:
    faq_items = load_faq_base(FAQ_PATH)
    return RetrievalIndex.build(faq_items, MockEmbeddingProvider())


@pytest.mark.parametrize("question,expected_faq_id", FIVE_QUESTIONS)
def test_top_result_matches_expected_faq(index: RetrievalIndex, question: str, expected_faq_id: str):
    results = index.search(question, MockEmbeddingProvider(), top_k=1)
    assert results[0].faq_item.faq_id == expected_faq_id


def test_out_of_scope_question_scores_low(index: RetrievalIndex):
    results = index.search("What is the capital of France?", MockEmbeddingProvider(), top_k=1)
    assert results[0].similarity_score < 0.72  # default SIMILARITY_THRESHOLD


def test_save_and_load_roundtrip(tmp_path, index: RetrievalIndex):
    path = tmp_path / "index.json"
    index.save(path)
    reloaded = RetrievalIndex.load(path)
    results = reloaded.search(FIVE_QUESTIONS[0][0], MockEmbeddingProvider(), top_k=1)
    assert results[0].faq_item.faq_id == FIVE_QUESTIONS[0][1]
