"""Admissions analytics (US9): counts over the stored chat turns, unanswered questions and
ratings. Only counts and redacted question texts leave this module, never session ids."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assistant.feedback import AnswerFeedback
from app.assistant.language import detect_language
from app.conversation.models import ASSISTANT, RETENTION_DAYS, USER, ChatTurn
from app.exports import redact
from app.faq.models import FaqRecord
from app.followups.inbox import normalize
from app.followups.models import UNANSWERED_QUESTION, AdmissionsFollowup

# Kazakhstan uses one time zone, UTC+5, since 2024: days are counted in local time.
LOCAL_TIME = timezone(timedelta(hours=5))
MAX_DAYS = RETENTION_DAYS
TOP = 10


@dataclass
class Report:
    days: int
    since: date
    questions: int = 0
    sessions: int = 0
    unanswered: int = 0
    per_day: list[dict] = field(default_factory=list)
    top_questions: list[dict] = field(default_factory=list)
    top_sources: list[dict] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    ratings: dict[str, int] = field(default_factory=dict)
    down_reasons: dict[str, int] = field(default_factory=dict)


def _local_day(moment: datetime) -> date:
    return moment.astimezone(LOCAL_TIME).date()


def build_report(session: Session, days: int, now: datetime | None = None) -> Report:
    if not 1 <= days <= MAX_DAYS:
        raise ValueError(f"days must be between 1 and {MAX_DAYS}")
    now = now or datetime.now(timezone.utc)
    today = _local_day(now)
    since = today - timedelta(days=days - 1)
    cutoff = datetime.combine(since, datetime.min.time(), tzinfo=LOCAL_TIME)
    report = Report(days=days, since=since)

    turns = session.scalars(select(ChatTurn).where(ChatTurn.created_at >= cutoff)).all()
    questions = [turn for turn in turns if turn.role == USER]
    unanswered = session.scalars(
        select(AdmissionsFollowup).where(
            AdmissionsFollowup.kind == UNANSWERED_QUESTION, AdmissionsFollowup.created_at >= cutoff
        )
    ).all()
    feedback = session.scalars(select(AnswerFeedback).where(AnswerFeedback.created_at >= cutoff)).all()

    report.questions = len(questions)
    report.sessions = len({turn.session_id for turn in questions})
    report.unanswered = len(unanswered)

    per_day_questions = Counter(_local_day(turn.created_at) for turn in questions)
    per_day_unanswered = Counter(_local_day(row.created_at) for row in unanswered)
    report.per_day = [
        {"date": day.isoformat(), "questions": per_day_questions[day], "unanswered": per_day_unanswered[day]}
        for day in (since + timedelta(days=offset) for offset in range(days))
    ]

    groups: dict[str, list[str]] = {}
    for turn in questions:
        text = redact(turn.text.strip())
        if text:
            groups.setdefault(normalize(text), []).append(text)
    ranked = sorted(groups.values(), key=lambda texts: (-len(texts), texts[0]))[:TOP]
    report.top_questions = [{"question": texts[0], "count": len(texts)} for texts in ranked]

    cited = Counter(
        source["faq_id"]
        for turn in turns
        if turn.role == ASSISTANT and turn.sources
        for source in turn.sources
        if source.get("faq_id")
    )
    titles = dict(
        session.execute(select(FaqRecord.faq_id, FaqRecord.question).where(FaqRecord.faq_id.in_(list(cited)))).tuples().all()
    )
    report.top_sources = [
        {"faq_id": faq_id, "question": titles.get(faq_id), "count": count}
        for faq_id, count in sorted(cited.items(), key=lambda pair: (-pair[1], pair[0]))[:TOP]
    ]

    languages = Counter(detect_language(turn.text) for turn in questions)
    report.languages = {language: languages[language] for language in ("en", "ru", "kk")}
    ratings = Counter(row.rating for row in feedback)
    report.ratings = {"up": ratings["up"], "down": ratings["down"]}
    report.down_reasons = dict(Counter(row.reason or "none" for row in feedback if row.rating == "down").most_common())
    return report
