from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

from app.catalogue.models import Program

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from export_catalogue import COLUMNS, export_catalogue


def test_export_includes_all_programs_with_unknown_values_blank(catalogue_session, tmp_path):
    catalogue_session.add_all(
        [
            Program(program_id="cs-bsc", title="Computer Science", faculty="Engineering",
                    degree_level="bachelor", language="English",
                    tuition_per_ects_kzt=33000, tuition_per_ects_usd=90,
                    deadline_local=date(2026, 8, 25), deadline_international=date(2026, 7, 31),
                    source_url="https://sdu.edu.kz/en/computer-science-3/"),
            Program(program_id="arch-old", title="Architecture", faculty="Engineering",
                    degree_level="bachelor", language="Қазақ тілі", is_active=False),
        ]
    )
    catalogue_session.flush()
    out = tmp_path / "export.csv"

    count = export_catalogue(catalogue_session, out)

    assert count == 2
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")
    with out.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    assert list(rows[0].keys()) == COLUMNS
    assert rows == [
        {"program_id": "arch-old", "title": "Architecture", "faculty": "Engineering",
         "degree_level": "bachelor", "language": "Қазақ тілі", "tuition_per_ects_kzt": "",
         "tuition_per_ects_usd": "", "deadline_local": "", "deadline_international": "",
         "source_url": "", "is_active": "False"},
        {"program_id": "cs-bsc", "title": "Computer Science", "faculty": "Engineering",
         "degree_level": "bachelor", "language": "English", "tuition_per_ects_kzt": "33000",
         "tuition_per_ects_usd": "90", "deadline_local": "2026-08-25", "deadline_international": "2026-07-31",
         "source_url": "https://sdu.edu.kz/en/computer-science-3/", "is_active": "True"},
    ]
