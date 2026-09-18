"""Picks the retrieval index backend (T3.2) based on INDEX_BACKEND
("file" for offline dev, "postgres"/pgvector once the dev DB exists)."""
from __future__ import annotations

from typing import Protocol

from app.assistant.providers import EmbeddingProvider
from app.assistant.retrieval import RetrievalIndex, SearchResult
from app.config import Settings


class SearchableIndex(Protocol):
    def search(self, query: str, embedder: EmbeddingProvider, top_k: int = 1) -> list[SearchResult]: ...


def load_retrieval_index(settings: Settings) -> SearchableIndex:
    if settings.index_backend == "postgres":
        from app.assistant.retrieval_pg import PgRetrievalIndex
        from app.db import get_session

        return PgRetrievalIndex(get_session(settings), settings)
    return RetrievalIndex.load(settings.faq_index_path)
