from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def _no_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def db_engine():
    from alembic import command
    from alembic.config import Config

    from app.db import get_engine

    command.upgrade(Config(str(BACKEND_ROOT / "alembic.ini")), "head")
    return get_engine(get_settings())


@pytest.fixture
def db_session(db_engine):
    from sqlalchemy import delete
    from sqlalchemy.orm import Session

    from app.assistant.feedback import AnswerFeedback
    from app.followups.models import AdmissionsFollowup

    with db_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            session.execute(delete(AdmissionsFollowup))
            session.execute(delete(AnswerFeedback))
            yield session
        transaction.rollback()


@pytest.fixture
def catalogue_session(db_session):
    from sqlalchemy import delete

    from app.catalogue.models import Program

    db_session.execute(delete(Program))
    return db_session


@pytest.fixture(scope="session")
def faq_items():
    from app.assistant.retrieval import load_faq_base

    return load_faq_base(BACKEND_ROOT / get_settings().faq_data_path)


SPRINT2_CATALOGUE = BACKEND_ROOT / "tests" / "data" / "catalogue_sprint2.json"


def _catalogue_session(db_session, faq_items, source_path):
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
    from import_catalogue import import_catalogue, load_source

    from app.assistant.retrieval import rebuild_index

    from sqlalchemy import delete

    from app.conversation.models import ChatTurn

    import_catalogue(db_session, load_source(source_path))
    rebuild_index(db_session, faq_items)
    db_session.execute(delete(ChatTurn))
    return db_session


@pytest.fixture
def assistant_session(db_session, faq_items):
    return _catalogue_session(db_session, faq_items, SPRINT2_CATALOGUE)


@pytest.fixture
def full_catalogue_session(db_session, faq_items):
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
    from import_catalogue import DEFAULT_SOURCE

    return _catalogue_session(db_session, faq_items, DEFAULT_SOURCE)
