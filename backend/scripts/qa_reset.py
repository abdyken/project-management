from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete  # noqa: E402

from app.catalogue.models import Program  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import get_session  # noqa: E402

DESCRIPTION = """Local browser QA only: remove the archived synthetic programmes that the guidance
suite (frontend/e2e/guidance-qa.mjs) creates and archives, so the suites can be re-run on the
same database. Only inactive rows with a QA code and the synthetic title are touched; real
catalogue rows never match.

    python scripts/qa_reset.py"""

SYNTHETIC_TITLE = "QA synthetic programme"


def main() -> int:
    if len(sys.argv) > 1:
        print(DESCRIPTION)
        return 0
    with get_session(get_settings()) as session:
        removed = session.execute(
            delete(Program).where(
                Program.program_id.like("QA%"),
                Program.title == SYNTHETIC_TITLE,
                Program.is_active.is_(False),
            )
        ).rowcount
        session.commit()
    print(f"Removed {removed} archived synthetic QA programme(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
