from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, defer

from app.assistant import embeddings
from app.assistant.models import FaqEmbeddingRecord
from app.assistant.schemas import FaqItem


LEXICAL_WEIGHT = 0.9
SEARCH_LANGUAGES = {"en": ("en",), "ru": ("ru", "en"), "kk": ("kk", "en")}
_TOKEN = re.compile(r"[a-zа-яёәғқңөұүһі0-9]+")
_STEM_LENGTH = 5
_STOPWORDS = frozenset(
    """
    what is the a an do i how can my me to for of in and are does at on with you your there be
    что как ли на в и для мне я есть по с
    ма ме ба бе па пе бар қалай не үшін және
    sdu university
    """.split()
)


@dataclass
class SearchResult:
    faq_item: FaqItem
    similarity_score: float


def load_faq_base(path: str | Path) -> list[FaqItem]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [FaqItem(**item) for item in raw]


def rebuild_index(session: Session, faq_items: list[FaqItem]) -> None:
    rows = [(item, language, text) for item in faq_items for language, text in item.texts().items()]
    vectors = embeddings.embed([text for _, _, text in rows])
    session.execute(delete(FaqEmbeddingRecord))
    session.add_all(
        FaqEmbeddingRecord(
            faq_id=item.faq_id,
            language=language,
            question=item.question,
            answer=item.answer,
            category=item.category,
            source_link=item.source_link,
            last_update=item.last_update,
            degrees=item.degrees,
            applicant_types=item.applicant_types,
            translations=item.translations(),
            embedding=vector,
        )
        for (item, language, _), vector in zip(rows, vectors, strict=True)
    )
    session.commit()


def search(session: Session, question: str, limit: int = 5, language: str = "en") -> list[SearchResult]:
    languages = SEARCH_LANGUAGES.get(language, ("en",))
    query_vector = embeddings.embed([question])[0]
    distance = FaqEmbeddingRecord.embedding.cosine_distance(query_vector)
    rows = session.execute(
        select(FaqEmbeddingRecord, distance)
        .where(FaqEmbeddingRecord.language.in_(languages))
        .order_by(distance)
        .limit(limit * 3)
    )
    results: dict[str, SearchResult] = {}
    for record, record_distance in rows:
        if record.faq_id not in results:
            results[record.faq_id] = _to_result(record, 1.0 - float(record_distance))
    for record, score in _lexical_matches(session, question, languages):
        weighted = LEXICAL_WEIGHT * score
        current = results.get(record.faq_id)
        if current is None or weighted > current.similarity_score:
            results[record.faq_id] = _to_result(record, weighted)
    ranked = sorted(results.values(), key=lambda result: result.similarity_score, reverse=True)
    return ranked[:limit]


def _stems(text: str) -> set[str]:
    return {word[:_STEM_LENGTH] for word in _TOKEN.findall(text.lower()) if word not in _STOPWORDS and len(word) > 1}


def _lexical_matches(
    session: Session, question: str, languages: tuple[str, ...]
) -> list[tuple[FaqEmbeddingRecord, float]]:
    query = _stems(question)
    if not query:
        return []
    records = session.scalars(
        select(FaqEmbeddingRecord)
        .where(FaqEmbeddingRecord.language.in_(languages))
        .options(defer(FaqEmbeddingRecord.embedding))
    ).all()
    documents = [(record, _stems(_question_in(record))) for record in records]
    frequency = Counter(stem for _, stems in documents for stem in stems)
    total = len(documents) + 1
    idf = {stem: math.log(total / (frequency.get(stem, 0) + 0.5)) for stem in query}
    weight = sum(idf.values())
    best: dict[str, tuple[FaqEmbeddingRecord, float]] = {}
    for record, stems in documents:
        score = sum(idf[stem] for stem in query & stems) / weight if weight > 0 else 0.0
        if score > best.get(record.faq_id, (record, -1.0))[1]:
            best[record.faq_id] = (record, score)
    return [match for match in best.values() if match[1] > 0]


def _question_in(record: FaqEmbeddingRecord) -> str:
    if record.language == "en":
        return record.question
    return (record.translations or {}).get(record.language, {}).get("question", record.question)


def _to_result(record: FaqEmbeddingRecord, similarity_score: float) -> SearchResult:
    translated = {
        f"{key}_{language}": value
        for language, fields in (record.translations or {}).items()
        for key, value in fields.items()
    }
    return SearchResult(
        faq_item=FaqItem(
            faq_id=record.faq_id,
            question=record.question,
            answer=record.answer,
            category=record.category,
            source_link=record.source_link,
            last_update=record.last_update,
            degrees=record.degrees,
            applicant_types=record.applicant_types,
            **translated,
        ),
        similarity_score=similarity_score,
    )
