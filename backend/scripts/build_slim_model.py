"""Build the slim FAQ search model used in the Docker image.

Same model as app/assistant/embeddings.py (paraphrase-multilingual-MiniLM-L12-v2),
with two changes that cut its memory from ~610 MB to ~240 MB:

1. Vocabulary: only word pieces made of plain Latin, Cyrillic, digits,
   punctuation and symbols are kept (116k of 250k). Kazakh, Russian and
   English text can only ever be split into such pieces, so their vectors do
   not change; pieces of other scripts (CJK, Arabic, ...) are dropped.
2. The word table is stored as int8 with one scale per row instead of fp16.

scripts/check_slim_model.py verifies the result against the original model.

    uv run python scripts/build_slim_model.py --out /opt/slim-model
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import unicodedata
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.embeddings import MODEL_NAME  # noqa: E402

MODEL_FILE = "model_optimized.onnx"
WORD_TABLE = "embeddings.word_embeddings.weight"
TOKENIZER_FILES = ("tokenizer.json", "config.json", "special_tokens_map.json", "tokenizer_config.json")


def source_dir() -> Path:
    """The original model files, downloaded by fastembed if not cached yet."""
    from fastembed import TextEmbedding

    model = TextEmbedding(MODEL_NAME)
    return Path(model.model._model_dir)


def keeps(piece: str) -> bool:
    for char in piece:
        if char == "▁" or char.isspace() or ord(char) < 128:
            continue
        if unicodedata.category(char)[0] in "PSZ":
            continue
        try:
            if unicodedata.name(char).startswith("CYRILLIC"):
                continue
        except ValueError:
            pass
        return False
    return True


def build(source: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    tokenizer = json.loads((source / "tokenizer.json").read_text(encoding="utf-8"))
    vocab = tokenizer["model"]["vocab"]
    specials = {token["content"] for token in tokenizer["added_tokens"]}
    keep = [index for index, (piece, _) in enumerate(vocab) if piece in specials or keeps(piece)]
    remap = {old: new for new, old in enumerate(keep)}

    tokenizer["model"]["vocab"] = [vocab[index] for index in keep]
    tokenizer["model"]["unk_id"] = remap[tokenizer["model"]["unk_id"]]
    for token in tokenizer["added_tokens"]:
        token["id"] = remap[token["id"]]

    def remap_ids(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "ids" and isinstance(value, list):
                    node[key] = [remap[index] for index in value]
                elif key == "pad_id" and isinstance(value, int):
                    node[key] = remap[value]
                else:
                    remap_ids(value)
        elif isinstance(node, list):
            for value in node:
                remap_ids(value)

    remap_ids(tokenizer.get("post_processor"))
    remap_ids(tokenizer.get("padding"))
    (out / "tokenizer.json").write_text(json.dumps(tokenizer, ensure_ascii=False), encoding="utf-8")
    for name in TOKENIZER_FILES[1:]:
        if (source / name).exists():
            shutil.copy((source / name).resolve(), out / name)

    model = onnx.load(str(source / MODEL_FILE))
    graph = model.graph
    table_init = next(init for init in graph.initializer if init.name == WORD_TABLE)
    table = numpy_helper.to_array(table_init).astype(np.float32)[keep]
    scale = np.abs(table).max(axis=1, keepdims=True) / 127.0
    scale[scale == 0] = 1.0
    quantized = np.clip(np.round(table / scale), -127, 127).astype(np.int8)

    gather = next(node for node in graph.node if node.op_type == "Gather" and node.input[0] == WORD_TABLE)
    ids, output = gather.input[1], gather.output[0]
    graph.initializer.remove(table_init)
    graph.initializer.extend(
        [numpy_helper.from_array(quantized, "word_table_int8"), numpy_helper.from_array(scale.astype(np.float16), "word_table_scale")]
    )
    position = list(graph.node).index(gather)
    graph.node.remove(gather)
    replacement = [
        helper.make_node("Gather", ["word_table_int8", ids], ["word_rows_int8"], axis=0),
        helper.make_node("Gather", ["word_table_scale", ids], ["word_rows_scale"], axis=0),
        helper.make_node("Cast", ["word_rows_int8"], ["word_rows_fp16"], to=TensorProto.FLOAT16),
        helper.make_node("Mul", ["word_rows_fp16", "word_rows_scale"], [output]),
    ]
    for offset, node in enumerate(replacement):
        graph.node.insert(position + offset, node)
    onnx.save(model, str(out / MODEL_FILE))

    manifest = {"source_model": MODEL_NAME, "vocabulary": len(vocab), "kept_pieces": len(keep), "model_file": MODEL_FILE}
    (out / "slim_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source", type=Path, help="original model directory (default: download with fastembed)")
    args = parser.parse_args()
    manifest = build(args.source or source_dir(), args.out)
    size = (args.out / MODEL_FILE).stat().st_size / 1e6
    print(f"Slim model in {args.out}: {manifest['kept_pieces']} of {manifest['vocabulary']} pieces, {size:.0f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
