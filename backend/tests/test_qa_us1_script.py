"""scripts/qa_us1.py with programs whose language is not published (null since US16)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from qa_us1 import US1QA  # noqa: E402

CATALOGUE = [
    {"program_id": "7M01", "title": "Management", "faculty": "Business School", "degree_level": "master",
     "language": None, "is_active": True},
    {"program_id": "6B01", "title": "Computer Science", "faculty": "Engineering", "degree_level": "bachelor",
     "language": "English", "is_active": True},
    {"program_id": "6B02", "title": "Applied Law", "faculty": "Law", "degree_level": "bachelor",
     "language": "Kazakh, Russian", "is_active": True},
]


class FakeResponse:
    status_code = 200

    def __init__(self, programs: list[dict]):
        self._body = {"total": len(programs), "programs": programs}
        self.text = str(self._body)

    def json(self) -> dict:
        return self._body


class FakeCatalogueApi:
    """Filters like GET /api/programs: a language filter never matches an unpublished language."""

    def get(self, path: str, params: dict) -> FakeResponse:
        programs = [
            program for program in CATALOGUE
            if all(
                (value.lower() in [part.strip().lower() for part in (program["language"] or "").split(",") if part])
                if field == "language" else program[field].lower() == value.lower()
                for field, value in params.items()
            )
        ]
        return FakeResponse(programs)


def test_program_without_language_never_matches_a_language_filter():
    assert US1QA.matches(CATALOGUE[0], "language", "English") is False
    assert US1QA.matches(CATALOGUE[2], "language", "russian") is True


def test_combined_filters_skip_a_first_program_without_language():
    result = US1QA(FakeCatalogueApi()).combined_filters()

    assert result.startswith("7 combinations")
