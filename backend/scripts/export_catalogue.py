"""Export the program catalogue to CSV for the Product Owner (T1.6).

Reads the database directly (DATABASE_URL), so inactive programs are included
and can be compared with the official list too. The file is UTF-8 with BOM so
Excel shows non-Latin characters correctly.

Usage:
    uv run python scripts/export_catalogue.py
    DATABASE_URL=<dev database url> uv run python scripts/export_catalogue.py --out catalogue-dev.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.catalogue.models import Program  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import get_session  # noqa: E402

COLUMNS = [
    "program_id",
    "title",
    "faculty",
    "degree_level",
    "language",
    "tuition_fee",
    "application_deadline",
    "is_active",
]


def export_catalogue(session: Session, out: Path) -> int:
    programs = session.scalars(select(Program).order_by(Program.title, Program.program_id)).all()
    with out.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(COLUMNS)
        for program in programs:
            writer.writerow(["" if getattr(program, column) is None else getattr(program, column) for column in COLUMNS])
    return len(programs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path("catalogue-export.csv"))
    args = parser.parse_args()

    with get_session(get_settings()) as session:
        count = export_catalogue(session, args.out)
    print(f"Exported {count} programs to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
