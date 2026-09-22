"""T3.7 — Accuracy test set.

Local/dev mode (default): runs in-process against AssistantService, useful
while iterating.

Dev-environment mode (what actually counts for the Product Owner acceptance
rule — "executed ... on the deployed dev environment, not on a local
machine"): set ASSISTANT_BASE_URL to the deployed URL once T0.5 exists, e.g.

    ASSISTANT_BASE_URL=https://dev.example.com python scripts/run_accuracy_test.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.assistant.catalog_client import get_catalog_client  # noqa: E402
from app.assistant.checklist_client import get_checklist_client  # noqa: E402
from app.assistant.index_factory import load_retrieval_index  # noqa: E402
from app.assistant.providers import get_embedding_provider  # noqa: E402
from app.assistant.service import AssistantService  # noqa: E402
from app.config import get_settings  # noqa: E402

TEST_SET_PATH = Path(__file__).resolve().parent.parent / "tests" / "accuracy_test_set.json"


def run_in_process() -> list[dict]:
    settings = get_settings()
    service = AssistantService(
        settings=settings,
        index=load_retrieval_index(settings),
        embedder=get_embedding_provider(settings),
        catalog_client=get_catalog_client(settings),
        checklist_client=get_checklist_client(settings),
    )
    results = []
    for case in json.loads(TEST_SET_PATH.read_text(encoding="utf-8")):
        response = service.answer(case["question"], session_id="accuracy-test")
        results.append({**case, "actual_faq_id": response.faq_id, "similarity_score": response.similarity_score})
    return results


def run_against_deployment(base_url: str) -> list[dict]:
    results = []
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        for case in json.loads(TEST_SET_PATH.read_text(encoding="utf-8")):
            response = client.post(
                "/api/assistant/ask", json={"question": case["question"], "session_id": "accuracy-test"}
            )
            body = response.json()
            results.append(
                {**case, "actual_faq_id": body.get("faq_id"), "similarity_score": body.get("similarity_score")}
            )
    return results


def main() -> int:
    base_url = os.environ.get("ASSISTANT_BASE_URL")
    results = run_against_deployment(base_url) if base_url else run_in_process()

    correct = 0
    print(f"{'question':<60} {'expected':<10} {'actual':<10} {'score':<6} {'OK'}")
    for r in results:
        is_correct = r["actual_faq_id"] == r["expected_faq_id"]
        correct += is_correct
        print(
            f"{r['question'][:58]:<60} {str(r['expected_faq_id']):<10} "
            f"{str(r['actual_faq_id']):<10} {r['similarity_score']:.3f}  {'PASS' if is_correct else 'FAIL'}"
        )

    accuracy = correct / len(results)
    print(f"\nAccuracy: {correct}/{len(results)} ({accuracy:.0%})")
    print(f"Mode: {'deployed (' + base_url + ')' if base_url else 'in-process (local, NOT a QA run)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
