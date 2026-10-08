from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.config import Settings, get_settings
from app.conversation.models import ChatTurn
from app.conversation.retention import purge_once
from app.db import get_session


def test_purge_deletes_only_turns_older_than_30_days(db_engine):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    with get_session(settings) as session:
        session.add_all(
            [
                ChatTurn(session_id="retention-old", role="user", text="old", created_at=now - timedelta(days=31)),
                ChatTurn(session_id="retention-new", role="user", text="new", created_at=now - timedelta(days=29)),
            ]
        )
        session.commit()
    try:
        assert purge_once(settings) >= 1
        with get_session(settings) as session:
            left = session.scalars(select(ChatTurn.session_id).where(ChatTurn.session_id.like("retention-%"))).all()
        assert left == ["retention-new"]
    finally:
        with get_session(settings) as session:
            session.execute(delete(ChatTurn).where(ChatTurn.session_id.like("retention-%")))
            session.commit()


def test_purge_failure_does_not_raise():
    settings = Settings(database_url="postgresql+psycopg://nobody:nothing@127.0.0.1:1/none")

    assert purge_once(settings) is None
