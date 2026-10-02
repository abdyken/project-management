"""Server-sent events for POST /api/assistant/ask/stream (US14).

Event stream contract (docs/api/assistant-stream.md):

    event: chunk
    data: {"text": "Required documents for "}

    ... more chunks, in order; concatenated they are the full answer ...

    event: done
    data: {"answer_id": "42", "sources": [{"faq_id", "question", "link"}], "faq_id": ..., "source_link": ..., "similarity_score": ...}

    event: error            (only if the answer breaks off after streaming started)
    data: {"error_code": "...", "message": "..."}

The answer is produced first (same service, fallbacks and time budget as
/ask) and then sent in chunks. When answers come from a model (US10), the
model's own token stream replaces `chunk_text` as the source of chunks.
"""
from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator, Iterator
from typing import Any

from app.assistant.schemas import AskResponse

WORDS_PER_CHUNK = 3
# A long answer (a full document list) still finishes streaming within this time.
MAX_STREAM_SECONDS = 2.0
STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    # nginx in front of the API buffers responses by default, which would
    # deliver the whole stream at once at the end.
    "X-Accel-Buffering": "no",
}

_WORD_WITH_SPACE = re.compile(r"\s*\S+\s*")


def chunk_text(text: str, words_per_chunk: int = WORDS_PER_CHUNK) -> Iterator[str]:
    """Pieces of the text, a few words each, that join back to exactly the text."""
    words = _WORD_WITH_SPACE.findall(text)
    if not words:
        if text:
            yield text
        return
    for start in range(0, len(words), words_per_chunk):
        yield "".join(words[start : start + words_per_chunk])


def sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def done_payload(response: AskResponse) -> dict[str, Any]:
    """Everything of the /ask response except the answer text, which went out as chunks."""
    return response.model_dump(exclude={"answer"})


def pacing(chunk_count: int, chunk_delay_seconds: float, max_seconds: float = MAX_STREAM_SECONDS) -> float:
    """Pause after each chunk: the configured delay, shortened so the whole
    answer streams within max_seconds."""
    if chunk_count == 0 or chunk_delay_seconds <= 0:
        return 0.0
    return min(chunk_delay_seconds, max_seconds / chunk_count)


async def answer_events(
    response: AskResponse,
    chunk_delay_seconds: float,
) -> AsyncIterator[str]:
    pieces = list(chunk_text(response.answer))
    delay = pacing(len(pieces), chunk_delay_seconds)
    for piece in pieces:
        yield sse_event("chunk", {"text": piece})
        if delay > 0:
            await asyncio.sleep(delay)
    yield sse_event("done", done_payload(response))
