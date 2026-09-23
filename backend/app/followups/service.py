from __future__ import annotations

from sqlalchemy.orm import Session

from app.followups.models import MISSING_DOCUMENTS, UNANSWERED_QUESTION, AdmissionsFollowup


def log_unanswered_question(
    session: Session, question: str, similarity_score: float | None, session_id: str | None
) -> None:
    session.add(
        AdmissionsFollowup(
            kind=UNANSWERED_QUESTION,
            question=question,
            similarity_score=similarity_score,
            session_id=session_id,
        )
    )
    session.commit()


def log_missing_documents(
    session: Session, program_id: str, applicant_type: str, question: str | None = None, session_id: str | None = None
) -> None:
    session.add(
        AdmissionsFollowup(
            kind=MISSING_DOCUMENTS,
            program_id=program_id,
            applicant_type=applicant_type,
            question=question,
            session_id=session_id,
        )
    )
    session.commit()
