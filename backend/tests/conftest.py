from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.config import get_settings


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
    from sqlalchemy.orm import Session

    with db_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
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


@pytest.fixture
def assistant_session(db_session, faq_items):
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
    from import_catalogue import DEFAULT_SOURCE, import_catalogue, load_source

    from app.assistant.retrieval import rebuild_index

    import_catalogue(db_session, load_source(DEFAULT_SOURCE))
    rebuild_index(db_session, faq_items)
    return db_session
