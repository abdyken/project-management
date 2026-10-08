from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

import pytest

from app.followups.models import MISSING_DOCUMENTS, UNANSWERED_QUESTION, AdmissionsFollowup
from scripts.export_unanswered import group_unanswered, write_csv

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


def add(session, question, days_ago=1, score=0.3, kind=UNANSWERED_QUESTION):
    session.add(
        AdmissionsFollowup(
            kind=kind, question=question, similarity_score=score, session_id="s", created_at=NOW - timedelta(days=days_ago)
        )
    )
    session.flush()


def test_questions_are_grouped_counted_and_redacted(db_session):
    add(db_session, "Is there a hackathon?", days_ago=3, score=0.31)
    add(db_session, "is there a HACKATHON", days_ago=2, score=0.42)
    add(db_session, "Call me at +7 777 123 45 67 about parking", days_ago=1)
    add(db_session, "Old question", days_ago=40)
    add(db_session, None, kind=MISSING_DOCUMENTS)

    groups = group_unanswered(db_session, days=30, now=NOW)

    assert [(group.question, group.count) for group in groups] == [
        ("Is there a hackathon?", 2),
        ("Call me at [phone redacted] about parking", 1),
    ]
    assert groups[0].best_score == pytest.approx(0.42)

    output = io.StringIO()
    write_csv(groups, output)
    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert rows[0]["count"] == "2" and rows[0]["language"] == "en"
    assert "+7 777" not in output.getvalue()
    assert "session" not in output.getvalue()


def test_days_must_be_positive(db_session):
    with pytest.raises(ValueError):
        group_unanswered(db_session, days=0)
