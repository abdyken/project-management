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
