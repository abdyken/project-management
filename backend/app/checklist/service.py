from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checklist.models import ProgramDocumentRequirement

MISSING_REQUIREMENTS_WARNING = (
    "The document list for this program is not published yet, please contact the admissions office."
)


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
