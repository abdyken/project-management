"""T3.2 — Retrieval index, Postgres/pgvector-backed variant.

Same public shape as ``RetrievalIndex`` in ``retrieval.py`` (a ``search``
method returning ``SearchResult``s), but reads/writes the ``faq_embeddings``
table in the shared Postgres DB instead of a local JSON file. Selected via
``INDEX_BACKEND=postgres`` (see ``app/config.py``) — this is the backend to
use once the real dev database (T0.5) exists; ``file`` stays available for
fully offline development and unit tests.
"""
from __future__ import annotations

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.assistant.models import FaqEmbeddingRecord, assert_dimensions_match
from app.assistant.providers import EmbeddingProvider, ProviderError
from app.assistant.retrieval import KeywordIndex, SearchResult
from app.assistant.schemas import FaqItem
from app.config import Settings


def rebuild_index(session: Session, faq_items: list[FaqItem], embedder: EmbeddingProvider) -> None:
    """Full rebuild: delete all rows, re-insert from scratch. Idempotent —
    matches the T3.2 DoD ("index builds from scratch with one command")."""
    vectors = embedder.embed([item.question for item in faq_items])
    session.execute(delete(FaqEmbeddingRecord))
    session.add_all(
        FaqEmbeddingRecord(
            faq_id=item.faq_id,
            question=item.question,
            answer=item.answer,
            category=item.category,
            source_link=item.source_link,
            last_update=item.last_update,
            embedding=vector,
        )
        for item, vector in zip(faq_items, vectors)
    )
    session.commit()


class PgRetrievalIndex:
    def __init__(self, session: Session, settings: Settings):
        assert_dimensions_match(settings)
        self._session = session

    def _load_all(self) -> list[FaqEmbeddingRecord]:
        return list(self._session.execute(select(FaqEmbeddingRecord)).scalars())

    def search(self, query: str, embedder: EmbeddingProvider, top_k: int = 1) -> list[SearchResult]:
        try:
            query_vec = embedder.embed([query])[0]
            rows = list(
                self._session.execute(
                    select(
                        FaqEmbeddingRecord,
                        FaqEmbeddingRecord.embedding.cosine_distance(query_vec).label("distance"),
                    )
                    .order_by("distance")
                    .limit(top_k)
                )
            )
            return [
                SearchResult(
                    faq_item=_to_faq_item(record),
                    similarity_score=1.0 - float(distance),
                    method="embedding",
                )
                for record, distance in rows
            ]
        except ProviderError:
            records = self._load_all()
            faq_items = [_to_faq_item(r) for r in records]
            keyword_index = KeywordIndex(faq_items)
            scores = np.array(keyword_index.score_all(query))
            ranked = np.argsort(-scores)[:top_k]
            return [
                SearchResult(faq_item=faq_items[i], similarity_score=float(scores[i]), method="keyword_fallback")
                for i in ranked
            ]


def _to_faq_item(record: FaqEmbeddingRecord) -> FaqItem:
    return FaqItem(
        faq_id=record.faq_id,
        question=record.question,
        answer=record.answer,
        category=record.category,
        source_link=record.source_link,
        last_update=record.last_update,
    )
