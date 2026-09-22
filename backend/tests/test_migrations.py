"""Every table created by the migrations must be registered in migrations/env.py.

Otherwise `alembic revision --autogenerate` proposes dropping that table.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sqlalchemy import inspect

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def tables_known_to_env_py() -> set[str]:
    """Tables on Base.metadata after only migrations/env.py's imports - in a fresh
    interpreter, because the test session has already imported the whole app."""
    env_source = (BACKEND_ROOT / "migrations" / "env.py").read_text()
    imports = [line for line in env_source.splitlines() if line.startswith("from app.")]
    script = "\n".join(
        [*imports, "from app.db import Base", "import json", "print(json.dumps(sorted(Base.metadata.tables)))"]
    )
    output = subprocess.run(
        [sys.executable, "-c", script], cwd=BACKEND_ROOT, capture_output=True, text=True, check=True
    ).stdout
    return set(json.loads(output))


def test_every_migrated_table_is_known_to_autogenerate(db_engine):
    migrated = set(inspect(db_engine).get_table_names()) - {"alembic_version"}

    missing = migrated - tables_known_to_env_py()

    assert not missing, f"Import these tables' models in migrations/env.py: {sorted(missing)}"
