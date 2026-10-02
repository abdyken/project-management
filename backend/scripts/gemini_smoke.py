"""US10 / T10.1: one test call to Gemini with the configured key and models.

    uv run python scripts/gemini_smoke.py

On Render: open the service Shell and run `python scripts/gemini_smoke.py`.
Prints which model answered, its tokens and latency; never prints the key.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.llm import LlmUnavailable, get_llm
from app.config import get_settings

SCHEMA = {"type": "object", "properties": {"reply": {"type": "string"}}, "required": ["reply"]}


def main() -> int:
    settings = get_settings()
    llm = get_llm(settings)
    if llm is None:
        print("GEMINI_API_KEY is not set: the assistant answers word for word from the FAQ.")
        return 1
    print(f"Models in order: {', '.join(settings.gemini_model_list)}")
    try:
        generation = llm.generate("Reply in JSON.", 'Say "ready" in the reply field.', SCHEMA)
    except LlmUnavailable as error:
        print(f"No model answered: {error}")
        return 1
    print(
        f"OK model={generation.model} prompt_tokens={generation.prompt_tokens} "
        f"output_tokens={generation.output_tokens} latency_ms={generation.latency_ms}"
    )
    print(generation.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
