from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app

target = BACKEND_ROOT / "docs" / "api" / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {target.relative_to(BACKEND_ROOT)}")
