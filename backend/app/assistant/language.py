from __future__ import annotations

import re

from app.assistant.schemas import Language

_KAZAKH_LETTERS = re.compile(r"[әғқңөұүһі]", re.IGNORECASE)
_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)
_KAZAKH_WORDS = frozenset("қалай қанша керек бар ма ме ба бе па пе және мен үшін бойынша туралы".split())


def detect_language(text: str) -> Language:
    if _KAZAKH_LETTERS.search(text):
        return "kk"
    if not _CYRILLIC.search(text):
        return "en"
    words = set(re.findall(r"\w+", text.lower()))
    return "kk" if words & _KAZAKH_WORDS else "ru"
