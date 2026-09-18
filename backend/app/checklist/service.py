from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checklist.models import ProgramDocumentRequirement
from app.catalogue.models import Program


def get_active_program(session: Session, program_id: str) -> Program | None:
    program = session.get(Program, program_id)
    return program if program is not None and program.is_active else None


def get_requirements(
    session: Session, program_id: str, applicant_type: str
) -> list[ProgramDocumentRequirement]:
    query = (
        select(ProgramDocumentRequirement)
        .where(
            ProgramDocumentRequirement.program_id == program_id,
            ProgramDocumentRequirement.applicant_type == applicant_type,
        )
        .order_by(ProgramDocumentRequirement.display_order, ProgramDocumentRequirement.id)
    )
    return list(session.scalars(query))
