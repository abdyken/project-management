from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.retrieval import rebuild_index
from app.config import get_settings
from app.db import get_session
from app.faq.service import load_published


def main() -> int:
    # Since US20 the faq_item table is the source of truth (app/data/faq.json only seeded it).
    with get_session(get_settings()) as session:
        faq_items = load_published(session)
        rebuild_index(session, faq_items)
    print(f"Indexed {len(faq_items)} published FAQ items from the faq_item table")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
