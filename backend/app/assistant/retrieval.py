"""T3.2 — Retrieval index.

Builds an index over the FAQ base combining:
  * an embedding index (primary signal — semantic similarity), and
  * a keyword (TF-IDF cosine) index, used as a fallback whenever the
    embedding provider is unavailable and as a tie-breaker signal.

At the demo scale of this iteration (~30 FAQ items) there is no need for a
dedicated vector database: vectors are kept in memory / a small JSON file.
If the team settles on Postgres for T0.1, this module can be re-pointed at a
`pgvector` column later without changing its public interface
(`RetrievalIndex.build` / `.search`).
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.assistant.providers import EmbeddingProvider, ProviderError
from app.assistant.schemas import FaqItem

_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in _TOKEN_RE.findall(text)]


def load_faq_base(path: str | Path) -> list[FaqItem]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [FaqItem(**item) for item in raw]


@dataclass
class SearchResult:
    faq_item: FaqItem
    similarity_score: float
    method: str  # "embedding" | "keyword_fallback"


class KeywordIndex:
    """Plain TF-IDF cosine similarity over `question + answer`."""

    def __init__(self, faq_items: list[FaqItem]):
        self._faq_items = faq_items
        self._docs_tokens = [tokenize(f"{it.question} {it.answer}") for it in faq_items]
        self._df = Counter()
        for tokens in self._docs_tokens:
            self._df.update(set(tokens))
        self._n_docs = len(faq_items)
        self._doc_vectors = [self._tfidf(tokens) for tokens in self._docs_tokens]

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log((1 + self._n_docs) / (1 + df)) + 1.0

    def _tfidf(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        vec = {term: count * self._idf(term) for term, count in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {term: v / norm for term, v in vec.items()}

    def score_all(self, query: str) -> list[float]:
        query_vec = self._tfidf(tokenize(query))
        scores = []
        for doc_vec in self._doc_vectors:
            common = set(query_vec) & set(doc_vec)
            scores.append(sum(query_vec[t] * doc_vec[t] for t in common))
        return scores


def _cosine_sim_matrix(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query_vec) or 1.0
    matrix_norms = np.linalg.norm(matrix, axis=1)
    matrix_norms[matrix_norms == 0] = 1.0
    return (matrix @ query_vec) / (matrix_norms * query_norm)


class RetrievalIndex:
    def __init__(self, faq_items: list[FaqItem], embeddings: np.ndarray):
        self._faq_items = faq_items
        self._embeddings = embeddings
        self._keyword_index = KeywordIndex(faq_items)

    @classmethod
    def build(cls, faq_items: list[FaqItem], embedder: EmbeddingProvider) -> "RetrievalIndex":
        texts = [item.question for item in faq_items]
        vectors = np.array(embedder.embed(texts), dtype=np.float64)
        return cls(faq_items, vectors)

    def save(self, path: str | Path) -> None:
        payload = {
            "faq_items": [item.model_dump() for item in self._faq_items],
            "embeddings": self._embeddings.tolist(),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "RetrievalIndex":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        faq_items = [FaqItem(**item) for item in payload["faq_items"]]
        embeddings = np.array(payload["embeddings"], dtype=np.float64)
        return cls(faq_items, embeddings)

    def search(self, query: str, embedder: EmbeddingProvider, top_k: int = 1) -> list[SearchResult]:
        if not self._faq_items:
            return []
        try:
            query_vec = np.array(embedder.embed([query])[0], dtype=np.float64)
            scores = _cosine_sim_matrix(query_vec, self._embeddings)
            method = "embedding"
        except ProviderError:
            scores = np.array(self._keyword_index.score_all(query))
            method = "keyword_fallback"

        ranked_indices = np.argsort(-scores)[:top_k]
        return [
            SearchResult(faq_item=self._faq_items[i], similarity_score=float(scores[i]), method=method)
            for i in ranked_indices
        ]
