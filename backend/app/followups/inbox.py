"""Unanswered questions grouped for the admissions office: the CSV export (US18) and the
staff inbox (US22) group them the same way."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exports import redact
from app.followups.models import NEW, UNANSWERED_QUESTION, AdmissionsFollowup

_PUNCTUATION = re.compile(r"[^\w\s]")


@dataclass
class Group:
    question: str
    count: int = 0
    best_score: float | None = None
    first_asked: datetime | None = None
    last_asked: datetime | None = None
    variants: set[str] = field(default_factory=set)
    row_ids: list[int] = field(default_factory=list)
    # The FAQ item an answered group was answered with.
    faq_id: str | None = None

    @property
    def key(self) -> str:
        return normalize(self.question)


def normalize(text: str) -> str:
    return " ".join(_PUNCTUATION.sub(" ", text.lower()).split())


def _clean_question(row: AdmissionsFollowup) -> str:
    return redact((row.question or "").strip())


def group_unanswered(
    session: Session, days: int, now: datetime | None = None, status: str | None = None
) -> list[Group]:
    """Questions that differ only in case, spacing or punctuation are one group. E-mail
    addresses and phone numbers are redacted; session ids are never returned."""
    if days < 1:
        raise ValueError("days must be positive")
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    query = (
        select(AdmissionsFollowup)
        .where(AdmissionsFollowup.kind == UNANSWERED_QUESTION, AdmissionsFollowup.created_at >= cutoff)
        .order_by(AdmissionsFollowup.created_at)
    )
    if status is not None:
        query = query.where(AdmissionsFollowup.status == status)
    groups: dict[str, Group] = {}
    for row in session.scalars(query).all():
        question = _clean_question(row)
        if not question:
            continue
        group = groups.setdefault(normalize(question), Group(question=question))
        group.count += 1
        group.variants.add(question)
        group.row_ids.append(row.id)
        group.faq_id = row.faq_id or group.faq_id
        if row.similarity_score is not None:
            group.best_score = (
                row.similarity_score if group.best_score is None else max(group.best_score, row.similarity_score)
            )
        group.first_asked = group.first_asked or row.created_at
        group.last_asked = row.created_at
    return sorted(groups.values(), key=lambda group: (-group.count, group.question))


def rows_of_group(session: Session, key: str) -> list[AdmissionsFollowup]:
    """Every new unanswered question of the group, whatever its age: dismissing or answering
    a group handles all of them."""
    rows = session.scalars(
        select(AdmissionsFollowup).where(
            AdmissionsFollowup.kind == UNANSWERED_QUESTION, AdmissionsFollowup.status == NEW
        )
    ).all()
    return [row for row in rows if normalize(_clean_question(row)) == key]
