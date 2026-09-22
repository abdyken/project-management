"""T3.2 DoD check: "the index builds from scratch with one command".

    python scripts/reindex_faq.py

Idempotent: always rebuilds the index file from scratch from FAQ_DATA_PATH,
never appends. Re-run whenever the admissions office updates the FAQ base
(T3.1).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.providers import get_embedding_provider  # noqa: E402
from app.assistant.retrieval import RetrievalIndex, load_faq_base  # noqa: E402
from app.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    faq_items = load_faq_base(settings.faq_data_path)
    print(f"Loaded {len(faq_items)} FAQ items from {settings.faq_data_path}")

    embedder = get_embedding_provider(settings)

    if settings.index_backend == "postgres":
        from app.assistant.retrieval_pg import rebuild_index
        from app.db import get_session

        session = get_session(settings)
        rebuild_index(session, faq_items, embedder)
        print(f"Index written to Postgres table 'faq_embeddings' ({settings.database_url})")
    else:
        index = RetrievalIndex.build(faq_items, embedder)
        index.save(settings.faq_index_path)
        print(f"Index written to {settings.faq_index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
