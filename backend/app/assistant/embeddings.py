from __future__ import annotations

from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIMENSIONS = 384


@lru_cache
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in _model().embed(texts)]


def warm_up() -> None:
    embed(["warm-up"])
