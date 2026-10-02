"""Delete chat turns older than the retention window (US11 privacy constraint).

Chat turns are stored only against the anonymous session id and must not be
kept longer than 30 days. Run this daily (cron job on the host).

    uv run python scripts/purge_chat_turns.py
    uv run python scripts/purge_chat_turns.py --retention-days 7
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402
from app.conversation.models import RETENTION_DAYS  # noqa: E402
from app.conversation.service import delete_expired_turns  # noqa: E402
from app.db import get_session  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retention-days", type=int, default=RETENTION_DAYS)
    args = parser.parse_args()

    with get_session(get_settings()) as session:
        deleted = delete_expired_turns(session, args.retention_days)
    print(f"Deleted {deleted} chat turns older than {args.retention_days} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
