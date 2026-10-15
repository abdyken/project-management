from __future__ import annotations

import re
from datetime import date, datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.assistant.retrieval import reindex_item
from app.assistant.schemas import FaqItem
from app.faq.models import PUBLISHED, FaqRecord
from app.faq.schemas import TRANSLATED, FaqItemIn
from app.staff.models import StaffUser

_ID_NUMBER = re.compile(r"^faq-(\d+)$")


def to_faq_item(record: FaqRecord) -> FaqItem:
    return FaqItem(
        faq_id=record.faq_id,
        question=record.question,
        answer=record.answer,
        category=record.category,
        source_link=record.source_link,
        last_update=record.last_update,
        degrees=list(record.degrees),
        applicant_types=list(record.applicant_types),
        **{
            f"{field}_{language}": getattr(record, f"{field}_{language}")
            for language in TRANSLATED
            for field in ("question", "answer", "source_link")
        },
    )


def load_published(session: Session) -> list[FaqItem]:
    """The FAQ the assistant answers from: every published item."""
    records = session.scalars(select(FaqRecord).where(FaqRecord.status == PUBLISHED).order_by(FaqRecord.faq_id))
    return [to_faq_item(record) for record in records]


def published_by_id(session: Session, faq_ids: list[str]) -> dict[str, FaqItem]:
    records = session.scalars(
        select(FaqRecord).where(FaqRecord.faq_id.in_(faq_ids), FaqRecord.status == PUBLISHED)
    )
    return {record.faq_id: to_faq_item(record) for record in records}


def languages_of(record: FaqRecord) -> list[str]:
    return ["en", *(language for language in TRANSLATED if getattr(record, f"answer_{language}"))]


def list_items(
    session: Session, q: str | None = None, status: str | None = None, category: str | None = None
) -> list[FaqRecord]:
    query = select(FaqRecord).order_by(FaqRecord.faq_id)
    if status:
        query = query.where(FaqRecord.status == status)
    if category:
        query = query.where(FaqRecord.category == category)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                FaqRecord.faq_id.ilike(pattern),
                FaqRecord.question.ilike(pattern),
                FaqRecord.answer.ilike(pattern),
                FaqRecord.question_ru.ilike(pattern),
                FaqRecord.question_kk.ilike(pattern),
            )
        )
    return list(session.scalars(query))


def categories(session: Session) -> list[str]:
    return list(session.scalars(select(FaqRecord.category).distinct().order_by(FaqRecord.category)))


def get_item(session: Session, faq_id: str) -> FaqRecord | None:
    return session.get(FaqRecord, faq_id)


def _next_id(session: Session) -> str:
    numbers = [int(match.group(1)) for faq_id in session.scalars(select(FaqRecord.faq_id)) if (match := _ID_NUMBER.match(faq_id))]
    return f"faq-{max(numbers, default=0) + 1:03d}"


def _touch(record: FaqRecord, user: StaffUser) -> None:
    record.last_update = date.today().isoformat()
    record.updated_by_id = user.id
    record.updated_at = datetime.now(timezone.utc)


def _sync_index(session: Session, record: FaqRecord) -> None:
    reindex_item(session, record.faq_id, to_faq_item(record) if record.status == PUBLISHED else None)


def create_item(session: Session, data: FaqItemIn, user: StaffUser) -> FaqRecord:
    """New items start as drafts: the assistant uses them only after they are published."""
    record = FaqRecord(faq_id=_next_id(session), status="draft", **data.model_dump())
    _touch(record, user)
    session.add(record)
    session.commit()
    return record


def update_item(session: Session, record: FaqRecord, data: FaqItemIn, user: StaffUser) -> FaqRecord:
    for field, value in data.model_dump().items():
        setattr(record, field, value)
    _touch(record, user)
    _sync_index(session, record)
    session.commit()
    return record


def set_status(session: Session, record: FaqRecord, status: str, user: StaffUser) -> FaqRecord:
    record.status = status
    _touch(record, user)
    _sync_index(session, record)
    session.commit()
    return record


def editor_names(session: Session, records: list[FaqRecord]) -> dict[int, str]:
    ids = {record.updated_by_id for record in records if record.updated_by_id is not None}
    if not ids:
        return {}
    return dict(session.execute(select(StaffUser.id, StaffUser.name).where(StaffUser.id.in_(ids))).tuples().all())
