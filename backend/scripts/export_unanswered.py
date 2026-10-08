from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.language import detect_language  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.exports import csv_cell, redact  # noqa: E402
from app.db import get_session  # noqa: E402
from app.followups.models import UNANSWERED_QUESTION, AdmissionsFollowup  # noqa: E402

DESCRIPTION = """Export the questions the assistant could not answer (US18), grouped, for the admissions office
and the FAQ backlog.

    uv run python scripts/export_unanswered.py --days 30 --output unanswered.csv

Questions that differ only in case, spacing or punctuation are counted together. E-mail
addresses and phone numbers are redacted; no session ids are exported."""

HEADERS = ("question", "count", "language", "best_score", "first_asked", "last_asked")
_PUNCTUATION = re.compile(r"[^\w\s]")


@dataclass
class Group:
    question: str
    count: int = 0
    best_score: float | None = None
    first_asked: datetime | None = None
    last_asked: datetime | None = None
    variants: set[str] = field(default_factory=set)


def normalize(text: str) -> str:
    return " ".join(_PUNCTUATION.sub(" ", text.lower()).split())


def group_unanswered(session: Session, days: int, now: datetime | None = None) -> list[Group]:
    if days < 1:
        raise ValueError("days must be positive")
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    rows = session.scalars(
        select(AdmissionsFollowup)
        .where(AdmissionsFollowup.kind == UNANSWERED_QUESTION, AdmissionsFollowup.created_at >= cutoff)
        .order_by(AdmissionsFollowup.created_at)
    ).all()
    groups: dict[str, Group] = {}
    for row in rows:
        question = redact((row.question or "").strip())
        if not question:
            continue
        group = groups.setdefault(normalize(question), Group(question=question))
        group.count += 1
        group.variants.add(question)
        if row.similarity_score is not None:
            group.best_score = (
                row.similarity_score if group.best_score is None else max(group.best_score, row.similarity_score)
            )
        group.first_asked = group.first_asked or row.created_at
        group.last_asked = row.created_at
    return sorted(groups.values(), key=lambda group: (-group.count, group.question))


def write_csv(groups: list[Group], output: TextIO) -> None:
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()
    for group in groups:
        writer.writerow(
            {
                "question": csv_cell(group.question),
                "count": group.count,
                "language": detect_language(group.question),
                "best_score": "" if group.best_score is None else f"{group.best_score:.2f}",
                "first_asked": group.first_asked.isoformat() if group.first_asked else "",
                "last_asked": group.last_asked.isoformat() if group.last_asked else "",
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")
    with get_session(get_settings()) as session, args.output.open("w", newline="", encoding="utf-8-sig") as output:
        groups = group_unanswered(session, args.days)
        write_csv(groups, output)
    print(f"Exported {len(groups)} unanswered questions ({sum(g.count for g in groups)} asks) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
