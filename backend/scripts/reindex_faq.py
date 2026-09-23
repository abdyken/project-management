from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.retrieval import load_faq_base, rebuild_index
from app.config import get_settings
from app.db import get_session


def main() -> int:
    settings = get_settings()
    faq_items = load_faq_base(settings.faq_data_path)
    with get_session(settings) as session:
        rebuild_index(session, faq_items)
    print(f"Indexed {len(faq_items)} FAQ items from {settings.faq_data_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
