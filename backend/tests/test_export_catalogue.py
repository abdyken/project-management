"""T1.6: catalogue export for the Product Owner (needs the database)."""
from __future__ import annotations

import csv
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.catalogue.models import Program

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from export_catalogue import COLUMNS, export_catalogue  # noqa: E402


def test_export_includes_all_programs_with_unknown_values_blank(catalogue_session, tmp_path):
    catalogue_session.add_all(
        [
            Program(program_id="cs-bsc", title="Computer Science", faculty="Engineering",
                    degree_level="bachelor", language="English",
                    tuition_fee=Decimal("2500000.00"), application_deadline=date(2026, 8, 1)),
            Program(program_id="arch-old", title="Architecture", faculty="Engineering",
                    degree_level="bachelor", language="Қазақ тілі", is_active=False),
        ]
    )
    catalogue_session.flush()
    out = tmp_path / "export.csv"

    count = export_catalogue(catalogue_session, out)

    assert count == 2
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")  # BOM, so Excel reads UTF-8
    with out.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    assert list(rows[0].keys()) == COLUMNS
    assert rows == [
        {"program_id": "arch-old", "title": "Architecture", "faculty": "Engineering",
         "degree_level": "bachelor", "language": "Қазақ тілі", "tuition_fee": "",
         "application_deadline": "", "is_active": "False"},
        {"program_id": "cs-bsc", "title": "Computer Science", "faculty": "Engineering",
         "degree_level": "bachelor", "language": "English", "tuition_fee": "2500000.00",
         "application_deadline": "2026-08-01", "is_active": "True"},
    ]
