from __future__ import annotations

import json
import os
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Protocol

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIMENSIONS = 384
CACHE_SIZE = 4096

# Deployment settings (the Docker image sets both, see Dockerfile):
# EMBEDDING_MODEL_DIR  - slim copy of MODEL_NAME built by scripts/build_slim_model.py;
#                        unset = the original model through fastembed.
# EMBEDDING_CACHE_FILE - FAQ vectors precomputed at build time, so the server does not
#                        embed the whole FAQ again on every start.
MODEL_DIR_ENV = "EMBEDDING_MODEL_DIR"
CACHE_FILE_ENV = "EMBEDDING_CACHE_FILE"

_cache: OrderedDict[str, list[float]] = OrderedDict()
_lock = Lock()


class _Model(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class _FastembedModel:
    def __init__(self) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(MODEL_NAME)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


class _SlimModel:
    """The slim model in onnxruntime with low-memory settings.

    Mean pooling over the attention mask without normalisation, one text at a
    time: the same vectors fastembed returns for MODEL_NAME (no padding).
    """

    def __init__(self, model_dir: Path) -> None:
        import onnxruntime
        from tokenizers import Tokenizer

        self._tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self._tokenizer.no_padding()
        options = onnxruntime.SessionOptions()
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        self._session = onnxruntime.InferenceSession(
            str(model_dir / "model_optimized.onnx"), options, providers=["CPUExecutionProvider"]
        )
        self._inputs = {item.name for item in self._session.get_inputs()}

    def embed(self, texts: list[str]) -> list[list[float]]:
        import numpy as np

        vectors = []
        for text in texts:
            encoding = self._tokenizer.encode(text)
            ids = np.array([encoding.ids], dtype=np.int64)
            mask = np.array([encoding.attention_mask], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self._inputs:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = self._session.run(None, feeds)[0].astype(np.float32)
            pooled = (hidden * mask[..., None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)
            vectors.append(pooled[0].tolist())
        return vectors


@lru_cache
def _model() -> _Model:
    model_dir = os.environ.get(MODEL_DIR_ENV)
    return _SlimModel(Path(model_dir)) if model_dir else _FastembedModel()


@lru_cache
def _load_precomputed() -> None:
    path = os.environ.get(CACHE_FILE_ENV)
    if not path or not Path(path).is_file():
        return
    stored: dict[str, list[float]] = json.loads(Path(path).read_text(encoding="utf-8"))
    with _lock:
        for text, vector in stored.items():
            if len(_cache) >= CACHE_SIZE:
                break
            _cache.setdefault(text, vector)


def embed(texts: list[str]) -> list[list[float]]:
    _load_precomputed()
    with _lock:
        known = {text: _cache[text] for text in dict.fromkeys(texts) if text in _cache}
        for text in known:
            _cache.move_to_end(text)
    missing = [text for text in dict.fromkeys(texts) if text not in known]
    vectors = dict(zip(missing, _model().embed(missing), strict=True)) if missing else {}
    with _lock:
        _cache.update(vectors)
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
    return [known[text] if text in known else vectors[text] for text in texts]


def warm_up() -> None:
    embed(["warm-up"])
