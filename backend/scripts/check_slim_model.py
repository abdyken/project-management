"""Check the slim model against the original before it is used (Docker build).

Exits with an error, failing the build, unless for every FAQ question and
answer in English, Russian and Kazakh:
  - the slim and original vectors point the same way (cosine >= 0.999), and
  - asking an FAQ item's own question finds the same top item with both models.

    uv run python scripts/check_slim_model.py --model-dir /opt/slim-model
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.embeddings import _FastembedModel, _SlimModel  # noqa: E402
from app.assistant.retrieval import load_faq_base  # noqa: E402
from app.config import get_settings  # noqa: E402

MIN_COSINE = 0.999
MIN_SAME_TOP = 0.98


def unit(rows: list[list[float]]) -> np.ndarray:
    array = np.array(rows, dtype=np.float64)
    return array / np.linalg.norm(array, axis=1, keepdims=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()

    items = load_faq_base(BACKEND_ROOT / get_settings().faq_data_path)
    documents = [(language, item.faq_id, text) for item in items for language, text in item.texts().items()]
    questions = [
        (language, item.faq_id, question)
        for item in items
        for language, question in (("en", item.question), ("ru", item.question_ru), ("kk", item.question_kk))
        if question
    ]
    texts = [text for _, _, text in documents] + [text for _, _, text in questions]

    original, slim = _FastembedModel(), _SlimModel(args.model_dir)
    a, b = unit(original.embed(texts)), unit(slim.embed(texts))
    cosine = (a * b).sum(axis=1)
    failed = False
    print(f"vectors: {len(texts)} texts, min cosine {cosine.min():.5f} (required {MIN_COSINE})")
    if cosine.min() < MIN_COSINE:
        worst = int(cosine.argmin())
        print(f"FAIL: lowest similarity for {texts[worst][:80]!r}")
        failed = True

    split = len(documents)
    for language in ("en", "ru", "kk"):
        doc_rows = [index for index, (lang, _, _) in enumerate(documents) if lang == language]
        q_rows = [index for index, (lang, _, _) in enumerate(questions) if lang == language]
        if not q_rows:
            continue
        top_a = (a[split:][q_rows] @ a[:split][doc_rows].T).argmax(axis=1)
        top_b = (b[split:][q_rows] @ b[:split][doc_rows].T).argmax(axis=1)
        same = float((top_a == top_b).mean())
        print(f"{language}: same top FAQ item for {int((top_a == top_b).sum())}/{len(q_rows)} questions")
        if same < MIN_SAME_TOP:
            print(f"FAIL: {language} search results differ from the original model")
            failed = True

    print("slim model check: FAILED" if failed else "slim model check: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
