from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalogue.models import Program
from app.config import get_settings
from app.db import get_session

COLUMNS = [
    "program_id",
    "title",
    "faculty",
    "degree_level",
    "language",
    "tuition_per_ects_kzt",
    "tuition_per_ects_usd",
    "deadline_local",
    "deadline_international",
    "source_url",
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


DESCRIPTION = "Export the active catalogue to CSV for comparison with the official list."


def main() -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--out", type=Path, default=Path("catalogue-export.csv"))
    args = parser.parse_args()

    with get_session(get_settings()) as session:
        count = export_catalogue(session, args.out)
    print(f"Exported {count} programs to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
