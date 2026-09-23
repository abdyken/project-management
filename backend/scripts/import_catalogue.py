from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, model_validator
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.catalogue.models import Program
from app.catalogue.schemas import DegreeLevel
from app.checklist.models import ProgramDocumentRequirement
from app.checklist.schemas import ApplicantType, DocumentFormat
from app.config import get_settings
from app.db import get_session

DEFAULT_SOURCE = BACKEND_ROOT / "app" / "data" / "catalogue.json"


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    format: DocumentFormat
    translation: bool
    notarisation: bool
    deadline: str = Field(min_length=1)


class SourceProgram(BaseModel):
    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    faculty: str = Field(min_length=1, max_length=255)
    degree_level: DegreeLevel
    language: str = Field(min_length=1, max_length=50)
    tuition_fee: NonNegativeInt | None
    application_deadline: date | None
    source_url: str | None
    documents: dict[ApplicantType, list[SourceDocument]] | None


class SourceFile(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    comment: str | None = Field(default=None, alias="_comment")
    programs: list[SourceProgram]

    @model_validator(mode="after")
    def unique_program_ids(self) -> SourceFile:
        ids = [program.program_id for program in self.programs]
        duplicates = sorted({program_id for program_id in ids if ids.count(program_id) > 1})
        if duplicates:
            raise ValueError(f"duplicate program_id in source file: {duplicates}")
        return self


@dataclass
class ImportResult:
    programs: int
    requirements: int
    deactivated: list[str]


def load_source(path: Path) -> SourceFile:
    return SourceFile.model_validate_json(path.read_text(encoding="utf-8"))


def import_catalogue(session: Session, source: SourceFile) -> ImportResult:
    requirement_count = 0
    for item in source.programs:
        program = session.get(Program, item.program_id)
        if program is None:
            program = Program(program_id=item.program_id)
            session.add(program)
        program.title = item.title
        program.faculty = item.faculty
        program.degree_level = item.degree_level
        program.language = item.language
        program.tuition_fee = None if item.tuition_fee is None else Decimal(item.tuition_fee)
        program.application_deadline = item.application_deadline
        program.is_active = True

        session.execute(
            delete(ProgramDocumentRequirement).where(ProgramDocumentRequirement.program_id == item.program_id)
        )
        for applicant_type, documents in (item.documents or {}).items():
            for order, document in enumerate(documents):
                session.add(
                    ProgramDocumentRequirement(
                        program_id=item.program_id,
                        applicant_type=applicant_type,
                        name=document.name,
                        document_format=document.format,
                        translation_required=document.translation,
                        notarisation_required=document.notarisation,
                        deadline=document.deadline,
                        display_order=order,
                    )
                )
                requirement_count += 1

    source_ids = [item.program_id for item in source.programs]
    deactivated = list(
        session.scalars(
            update(Program)
            .where(Program.program_id.not_in(source_ids), Program.is_active.is_(True))
            .values(is_active=False)
            .returning(Program.program_id)
        )
    )
    session.commit()
    return ImportResult(programs=len(source.programs), requirements=requirement_count, deactivated=sorted(deactivated))


DESCRIPTION = "Import app/data/catalogue.json into the database. Safe to re-run."


def main() -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    source = load_source(args.source)
    with get_session(get_settings()) as session:
        result = import_catalogue(session, source)

    print(f"Imported {result.programs} programs and {result.requirements} document requirements from {args.source.name}")
    if result.deactivated:
        print(f"Deactivated (no longer in the source file): {', '.join(result.deactivated)}")
    missing_links = [item.program_id for item in source.programs if not item.source_url]
    if missing_links:
        print(f"Warning: {len(missing_links)} programs have no source_url (T0.6 requires one per record)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
