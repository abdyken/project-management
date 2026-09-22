"""Load the admissions catalogue the front-end was built against.

Idempotent: a second run updates the same program rows and replaces their
document requirements. Management (7M04101) is stored without a checklist so
the API returns the missing-requirements warning.

    uv run python scripts/import_catalogue.py
"""
from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.catalogue.models import Program  # noqa: E402
from app.checklist.models import ProgramDocumentRequirement  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import get_session  # noqa: E402

BACHELOR_LOCAL = [
    ("Admission application form (admissions.sdu.edu.kz)", "original", False, False, "Before visiting the Admissions Office"),
    ("School certificate with transcript", "original", False, False, "Enrolment"),
    ("UNT certificate", "original", False, False, "Enrolment"),
    ("Medical certificate (Form 075)", "original", False, False, "Enrolment"),
    ("Chest fluorography with physician’s report", "original", False, False, "Enrolment"),
    ("Vaccination record (Form 063)", "original", False, False, "Enrolment"),
    ("Photographs 3×4 cm, 6 copies", "original", False, False, "Enrolment"),
    ("IELTS or SDU Language School certificate (if available)", "copy", False, False, "Application"),
]

BACHELOR_INTERNATIONAL = [
    ("Passport", "copy", False, True, "31 July 2026 (fall intake)"),
    ("School diploma / certificate and transcript", "original", True, True, "31 July 2026 (fall intake)"),
    ("Motivational letter", "copy", False, False, "Application"),
    ("Letter of recommendation", "copy", False, False, "Application"),
    ("Electronic photograph 3×4 cm", "copy", False, False, "Application"),
    ("IELTS 5.5 (min 5.0 per section) or SDU Extension Center B1", "copy", False, False, "Application / placement test waiver"),
    ("Student fee receipt (200 USD)", "copy", False, False, "Application"),
    ("Medical Form 075 and X-ray result (upon arrival)", "original", False, False, "20 August 2026"),
]

MASTER_LOCAL = [
    ("Bachelor’s diploma and transcript", "original", False, False, "Enrolment"),
    ("Photographs 3×4 cm, 6 copies", "original", False, False, "Enrolment"),
    ("Medical card No. 075 and X-ray result", "original", False, False, "Enrolment"),
    ("Copy of national ID", "copy", False, False, "Enrolment"),
    ("Complex Test (CT) certificate, if available", "copy", False, False, "Grant competition"),
]

MASTER_INTERNATIONAL = [
    ("Passport", "copy", False, True, "Application"),
    ("Bachelor’s diploma and transcript", "original", True, True, "Application"),
    ("IELTS 5.5 or SDU Extension Center B1", "copy", False, False, "Application"),
    ("Student fee receipt (200 USD)", "copy", False, False, "Application"),
    ("Electronic photograph 3×4 cm", "copy", False, False, "Application"),
]

PEDAGOGY_EXTRA = ("Pedagogical examination result", "original", False, False, "Application")

# program_id, title, faculty, degree_level, language, tuition_fee, deadline
PROGRAMS: list[tuple[str, str, str, str, str, int | None, str]] = [
    ("6B06102", "Computer Science", "School of Engineering and Natural Sciences", "bachelor", "English", 2200000, "2026-07-31"),
    ("6B06101", "Information Systems", "School of Engineering and Natural Sciences", "bachelor", "English", 2200000, "2026-07-31"),
    ("6B05402", "Statistics and Data Science", "School of Engineering and Natural Sciences", "bachelor", "English", 2200000, "2026-07-31"),
    ("6B06103", "Mathematical and Computer Modelling", "School of Engineering and Natural Sciences", "bachelor", "English", 2050000, "2026-07-31"),
    ("7M06101", "Computer Engineering and Software", "School of Engineering and Natural Sciences", "master", "English", 2100000, "2026-07-08"),
    ("6B02302", "Translation Studies", "School of Education and Humanities", "bachelor", "English", 1890000, "2026-07-31"),
    ("6B01701", "Kazakh Language and Literature", "School of Education and Humanities", "bachelor", "Kazakh", 1890000, "2026-07-31"),
    ("6B01702", "Two Foreign Languages", "School of Education and Humanities", "bachelor", "English", 1890000, "2026-07-31"),
    ("6B01101", "Pedagogy and Psychology", "School of Education and Humanities", "bachelor", "Kazakh", 1890000, "2026-07-31"),
    ("6B04201", "Applied Law", "School of Law and Social Sciences", "bachelor", "English", 2000000, "2026-07-31"),
    ("6B03101", "International Relations", "School of Law and Social Sciences", "bachelor", "English", 2000000, "2026-07-31"),
    ("7M04101", "Management", "SDU Business School", "master", "English", None, "2026-07-08"),
]

PROGRAMS_WITHOUT_CHECKLIST = {"7M04101"}


def documents_for(program_id: str, degree_level: str) -> dict[str, list[tuple[str, str, bool, bool, str]]] | None:
    if program_id in PROGRAMS_WITHOUT_CHECKLIST:
        return None
    if degree_level == "master":
        local, international = list(MASTER_LOCAL), list(MASTER_INTERNATIONAL)
    else:
        local, international = list(BACHELOR_LOCAL), list(BACHELOR_INTERNATIONAL)
    if program_id == "6B01101":
        local.append(PEDAGOGY_EXTRA)
    return {"local": local, "international": international}


def import_catalogue(session: Session) -> tuple[int, int]:
    requirement_count = 0
    for program_id, title, faculty, degree_level, language, tuition_fee, deadline in PROGRAMS:
        program = session.get(Program, program_id)
        if program is None:
            program = Program(program_id=program_id)
            session.add(program)
        program.title = title
        program.faculty = faculty
        program.degree_level = degree_level
        program.language = language
        program.tuition_fee = None if tuition_fee is None else Decimal(tuition_fee)
        program.application_deadline = date.fromisoformat(deadline)
        program.is_active = True

        session.execute(
            delete(ProgramDocumentRequirement).where(ProgramDocumentRequirement.program_id == program_id)
        )
        documents = documents_for(program_id, degree_level)
        if documents is None:
            continue
        for applicant_type, items in documents.items():
            for order, (name, document_format, translation, notarisation, item_deadline) in enumerate(items):
                session.add(
                    ProgramDocumentRequirement(
                        program_id=program_id,
                        applicant_type=applicant_type,
                        name=name,
                        document_format=document_format,
                        translation_required=translation,
                        notarisation_required=notarisation,
                        deadline=item_deadline,
                        display_order=order,
                    )
                )
                requirement_count += 1
    session.commit()
    return len(PROGRAMS), requirement_count


def main() -> int:
    settings = get_settings()
    session = get_session(settings)
    try:
        programs, requirements = import_catalogue(session)
    finally:
        session.close()
    print(f"Imported {programs} programs and {requirements} document requirements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
