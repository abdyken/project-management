from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Settings is process-cached (lru_cache); env vars changed by a test
    (e.g. monkeypatch.setenv) must not leak into the next one."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --- Database fixtures (catalogue tests; need the Postgres from docker compose) ---


@pytest.fixture(scope="session")
def db_engine():
    from alembic import command
    from alembic.config import Config

    from app.db import get_engine

    command.upgrade(Config(str(BACKEND_ROOT / "alembic.ini")), "head")
    return get_engine(get_settings())


@pytest.fixture
def db_session(db_engine):
    """Session inside a transaction that is rolled back after the test."""
    from sqlalchemy.orm import Session

    with db_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
