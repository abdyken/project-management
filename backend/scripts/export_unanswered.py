from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.language import detect_language  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.exports import csv_cell  # noqa: E402
from app.db import get_session  # noqa: E402
from app.followups.inbox import Group, group_unanswered, normalize  # noqa: E402,F401

DESCRIPTION = """Export the questions the assistant could not answer (US18), grouped, for the admissions office
and the FAQ backlog.

    uv run python scripts/export_unanswered.py --days 30 --output unanswered.csv

Questions that differ only in case, spacing or punctuation are counted together. E-mail
addresses and phone numbers are redacted; no session ids are exported."""

HEADERS = ("question", "count", "language", "best_score", "first_asked", "last_asked")


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
