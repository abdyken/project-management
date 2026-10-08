from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache
from threading import Lock

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIMENSIONS = 384
CACHE_SIZE = 4096

_cache: OrderedDict[str, list[float]] = OrderedDict()
_lock = Lock()


@lru_cache
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    with _lock:
        known = {text: _cache[text] for text in dict.fromkeys(texts) if text in _cache}
        for text in known:
            _cache.move_to_end(text)
    missing = [text for text in dict.fromkeys(texts) if text not in known]
    vectors = dict(zip(missing, (vector.tolist() for vector in _model().embed(missing)), strict=True)) if missing else {}
    with _lock:
        _cache.update(vectors)
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
    return [known[text] if text in known else vectors[text] for text in texts]


def warm_up() -> None:
    embed(["warm-up"])
