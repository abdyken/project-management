"""T0.7 DoD check: "a test request from the deployed backend returns an answer".

Run after setting real keys in .env:

    python scripts/smoke_test_provider.py

With no keys set it runs against the mock providers (offline), so this also
works as a sanity check during local development.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant.providers import get_embedding_provider, get_llm_provider  # noqa: E402
from app.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    print(f"LLM provider:       {settings.llm_provider}")
    print(f"Embedding provider: {settings.embedding_provider}")

    try:
        llm = get_llm_provider(settings)
        reply = llm.generate("Reply with the single word: OK")
        print(f"LLM test call  -> {reply!r}")

        embedder = get_embedding_provider(settings)
        vectors = embedder.embed(["When is the application deadline?"])
        print(f"Embedding call -> vector of length {len(vectors[0])}")
    except Exception as exc:  # noqa: BLE001 — smoke test, want to print and fail loudly
        print(f"FAILED: {exc}")
        return 1

    print("OK — both providers responded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
