"""Export recent thumbs-down answers for the Product Owner.

    uv run python scripts/export_negative_feedback.py --days 7 --output feedback.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.feedback import AnswerFeedback  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import get_session  # noqa: E402

HEADERS = ("created_at", "question", "answer", "sources", "reason")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\w)\+?\d[\d\s()\-]{7,}\d(?!\w)")


def _redact(text: str) -> str:
    return PHONE.sub("[phone redacted]", EMAIL.sub("[email redacted]", text))


def export_feedback(session: Session, output: TextIO, days: int = 7, now: datetime | None = None) -> int:
    if days < 1:
        raise ValueError("days must be positive")
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    rows = session.scalars(
        select(AnswerFeedback)
        .where(AnswerFeedback.rating == "down", AnswerFeedback.created_at >= cutoff)
        .order_by(AnswerFeedback.created_at.desc(), AnswerFeedback.id.desc())
    ).all()
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "created_at": row.created_at.isoformat(),
                "question": _redact(row.question),
                "answer": _redact(row.answer),
                "sources": json.dumps(row.sources or [], ensure_ascii=False),
                "reason": row.reason or "",
            }
        )
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=7, help="Include feedback from the last N days (default: 7)")
    parser.add_argument("--output", type=Path, required=True, help="Destination CSV file")
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")
    with get_session(get_settings()) as session, args.output.open("w", newline="", encoding="utf-8") as output:
        count = export_feedback(session, output, args.days)
    print(f"Exported {count} negative ratings to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
