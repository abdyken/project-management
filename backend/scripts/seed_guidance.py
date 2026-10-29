"""Fill missing US27/28 records only; never overwrite staff changes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.catalogue.models import Program
from app.config import get_settings
from app.db import get_session
from app.guidance.models import ProgramGuidance
from app.guidance.schemas import Guidance

SOURCE = Path(__file__).resolve().parent.parent / "app/data/guidance.json"


def seed_guidance(session) -> int:
    programs = set(session.scalars(select(Program.program_id)))
    count = 0
    for code, data in json.loads(SOURCE.read_text(encoding="utf-8"))[
        "programs"
    ].items():
        payload = Guidance.model_validate(data).model_dump(mode="json")
        if code not in programs:
            continue
        inserted = session.scalar(
            insert(ProgramGuidance)
            .values(program_id=code, payload=payload)
            .on_conflict_do_nothing()
            .returning(ProgramGuidance.program_id)
        )
        count += int(inserted is not None)
    session.commit()
    return count


if __name__ == "__main__":
    with get_session(get_settings()) as session:
        print(f"Seeded {seed_guidance(session)} missing guidance records")
