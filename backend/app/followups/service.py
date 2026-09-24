from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
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


PAGE_VIEW_LOG_INTERVAL = timedelta(days=1)


def log_missing_documents(
    session: Session, program_id: str, applicant_type: str, question: str | None = None, session_id: str | None = None
) -> None:
    if question is None and _logged_recently(session, program_id, applicant_type):
        return
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


def _logged_recently(session: Session, program_id: str, applicant_type: str) -> bool:
    since = datetime.now(timezone.utc) - PAGE_VIEW_LOG_INTERVAL
    query = select(AdmissionsFollowup.id).where(
        AdmissionsFollowup.kind == MISSING_DOCUMENTS,
        AdmissionsFollowup.program_id == program_id,
        AdmissionsFollowup.applicant_type == applicant_type,
        AdmissionsFollowup.question.is_(None),
        AdmissionsFollowup.created_at >= since,
    )
    return session.scalar(query.limit(1)) is not None
