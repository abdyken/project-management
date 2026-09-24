from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.assistant import embeddings
from app.assistant.models import FaqEmbeddingRecord
from app.assistant.schemas import FaqItem


@dataclass
class SearchResult:
    faq_item: FaqItem
    similarity_score: float


def load_faq_base(path: str | Path) -> list[FaqItem]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [FaqItem(**item) for item in raw]


def rebuild_index(session: Session, faq_items: list[FaqItem]) -> None:
    vectors = embeddings.embed([f"{item.question} {item.answer}" for item in faq_items])
    session.execute(delete(FaqEmbeddingRecord))
    session.add_all(
        FaqEmbeddingRecord(**item.model_dump(), embedding=vector)
        for item, vector in zip(faq_items, vectors, strict=True)
    )
    session.commit()


def search(session: Session, question: str, limit: int = 5) -> list[SearchResult]:
    query_vector = embeddings.embed([question])[0]
    distance = FaqEmbeddingRecord.embedding.cosine_distance(query_vector)
    rows = session.execute(select(FaqEmbeddingRecord, distance).order_by(distance).limit(limit))
    return [_to_result(record, record_distance) for record, record_distance in rows]


def _to_result(record: FaqEmbeddingRecord, record_distance: float) -> SearchResult:
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
        ),
        similarity_score=1.0 - float(record_distance),
    )
