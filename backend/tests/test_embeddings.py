from __future__ import annotations

from app.assistant import embeddings


def test_cached_vectors_match_fresh_ones_and_keep_order():
    first = embeddings.embed(["dormitory cost", "UNT score", "dormitory cost"])
    again = embeddings.embed(["UNT score", "dormitory cost"])

    assert first[0] == first[2] == again[1]
    assert first[1] == again[0]
    assert len(first[0]) == embeddings.DIMENSIONS


def test_cache_is_bounded(monkeypatch):
    monkeypatch.setattr(embeddings, "CACHE_SIZE", 2)
    embeddings.embed(["a one", "b two", "c three"])

    assert len(embeddings._cache) <= 2
