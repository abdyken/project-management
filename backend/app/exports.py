from __future__ import annotations

import re

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\w)\+?\d[\d\s()\-]{7,}\d(?!\w)")
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def redact(text: str) -> str:
    return PHONE.sub("[phone redacted]", EMAIL.sub("[email redacted]", text))


def csv_cell(text: str) -> str:
    return f"'{text}" if text.startswith(FORMULA_START) else text


def safe_text(text: str) -> str:
    return csv_cell(redact(text))
