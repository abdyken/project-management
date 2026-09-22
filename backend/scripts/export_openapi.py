"""Write the OpenAPI description of the whole API to docs/api/openapi.json.

Run after changing any endpoint:  uv run python scripts/export_openapi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402

target = BACKEND_ROOT / "docs" / "api" / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {target.relative_to(BACKEND_ROOT)}")
