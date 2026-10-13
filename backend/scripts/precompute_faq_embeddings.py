"""Precompute the FAQ vectors at image build time (EMBEDDING_CACHE_FILE).

Uses the same model the server will use (EMBEDDING_MODEL_DIR), so the startup
reindex finds every FAQ text in the cache and does not embed the FAQ again on
a small server. Texts not in the file are still embedded normally.

    EMBEDDING_MODEL_DIR=/opt/slim-model uv run python scripts/precompute_faq_embeddings.py --out /opt/faq-embeddings.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.embeddings import _model  # noqa: E402
from app.assistant.retrieval import load_faq_base  # noqa: E402
from app.config import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    items = load_faq_base(BACKEND_ROOT / get_settings().faq_data_path)
    texts = list(dict.fromkeys(text for item in items for text in item.texts().values()))
    vectors = _model().embed(texts)
    args.out.write_text(json.dumps(dict(zip(texts, vectors, strict=True))), encoding="utf-8")
    print(f"Precomputed {len(texts)} FAQ vectors into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
