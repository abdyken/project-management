"""The slim FAQ search model (scripts/build_slim_model.py) and the deployment settings."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from app.assistant import embeddings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_slim_model import build, source_dir  # noqa: E402

SENTENCES = [
    "Which documents do I need for 6B06102 as an international applicant?",
    "Сколько стоит общежитие для студентов?",
    "Жатақхана қанша тұрады және қашан өтініш беру керек?",
    "IELTS 5.5 or SDU Extension Center B1 — 200 USD fee, deadline 31.07.2026",
]


@pytest.fixture(scope="session")
def slim_dir(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("slim-model")
    build(source_dir(), out)
    return out


@pytest.fixture
def fresh_embeddings(monkeypatch):
    """Clear the module's model, cache and precomputed file before and after a test."""
    def reset():
        for cached in (embeddings._model, embeddings._load_precomputed):
            if hasattr(cached, "cache_clear"):
                cached.cache_clear()
        embeddings._cache.clear()

    reset()
    yield monkeypatch
    monkeypatch.undo()
    reset()


def unit(rows) -> np.ndarray:
    array = np.array(rows, dtype=np.float64)
    return array / np.linalg.norm(array, axis=1, keepdims=True)


def test_slim_vectors_point_the_same_way_as_the_original(slim_dir):
    original = unit(embeddings._FastembedModel().embed(SENTENCES))
    slim = unit(embeddings._SlimModel(slim_dir).embed(SENTENCES))

    assert (original * slim).sum(axis=1).min() >= 0.999


def test_kazakh_russian_and_english_split_into_the_same_pieces(slim_dir):
    from tokenizers import Tokenizer

    original = Tokenizer.from_file(str(source_dir() / "tokenizer.json"))
    slim = Tokenizer.from_file(str(slim_dir / "tokenizer.json"))

    for sentence in SENTENCES:
        assert slim.encode(sentence).tokens == original.encode(sentence).tokens


def test_only_latin_and_cyrillic_pieces_are_kept(slim_dir):
    manifest = json.loads((slim_dir / "slim_manifest.json").read_text())

    assert manifest["kept_pieces"] < manifest["vocabulary"] / 2
    assert (slim_dir / "model_optimized.onnx").stat().st_size < 120_000_000


def test_model_dir_setting_switches_embed_to_the_slim_model(slim_dir, fresh_embeddings):
    fresh_embeddings.setenv(embeddings.MODEL_DIR_ENV, str(slim_dir))

    vectors = embeddings.embed(["dormitory cost", "UNT score"])

    assert isinstance(embeddings._model(), embeddings._SlimModel)
    assert [len(vector) for vector in vectors] == [embeddings.DIMENSIONS, embeddings.DIMENSIONS]


def test_without_the_setting_the_original_model_is_used(fresh_embeddings):
    fresh_embeddings.delenv(embeddings.MODEL_DIR_ENV, raising=False)

    assert isinstance(embeddings._model(), embeddings._FastembedModel)


def test_precomputed_vectors_are_used_without_calling_the_model(tmp_path, fresh_embeddings):
    stored = {"How much does the dormitory cost?": [0.5] * embeddings.DIMENSIONS}
    cache_file = tmp_path / "faq-embeddings.json"
    cache_file.write_text(json.dumps(stored))
    fresh_embeddings.setenv(embeddings.CACHE_FILE_ENV, str(cache_file))

    class NoModel:
        def embed(self, texts):
            raise AssertionError(f"model called for {texts}")

    fresh_embeddings.setattr(embeddings, "_model", lambda: NoModel())

    assert embeddings.embed(["How much does the dormitory cost?"]) == [[0.5] * embeddings.DIMENSIONS]


def test_missing_precomputed_file_is_ignored(fresh_embeddings):
    fresh_embeddings.setenv(embeddings.CACHE_FILE_ENV, "/nonexistent/faq-embeddings.json")

    assert len(embeddings.embed(["UNT score"])[0]) == embeddings.DIMENSIONS
