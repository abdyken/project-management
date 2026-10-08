"""Evaluation set v2 (US10 / T10.5) against a running API.

    ASSISTANT_BASE_URL=<dev-url> uv run python scripts/run_accuracy_test.py

Every case is asked in its own chat session (a follow-up first asks its `after`
question in that session). A case passes when the FAQ items in `sources` are
exactly `expected_faq_ids` (empty = fallback or a catalogue answer), the answer
contains every `expected_in_answer` text and none of `must_not_contain`.
Independently, every number in a sourced answer must be in its cited FAQ items
or the question; anything else is counted as an invented fact.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections import defaultdict
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.assistant.grounding import check_grounding
from app.assistant.retrieval import load_faq_base

TEST_SET_PATH = BACKEND_ROOT / "tests" / "accuracy_test_set.json"
TEST_SETS = {"v2": TEST_SET_PATH, "v3": BACKEND_ROOT / "tests" / "accuracy_test_set_v3.json"}
FAQ_PATH = BACKEND_ROOT / "app" / "data" / "faq.json"


def ask(client: httpx.Client, question: str, session_id: str) -> dict:
    response = client.post("/api/assistant/ask", json={"question": question, "session_id": session_id})
    response.raise_for_status()
    return response.json()


def cited_faq_ids(body: dict) -> list[str]:
    if "sources" in body:
        return [source["faq_id"] for source in body["sources"] if source.get("faq_id")]
    return [body["faq_id"]] if body.get("faq_id") else []  # contract v1 API


def score(case: dict, body: dict, faq_by_id: dict) -> tuple[str, str | None]:
    """(result, invented) for one case; invented is the grounding check's reason, if any."""
    answer, cited = body["answer"], cited_faq_ids(body)
    invented = None
    if cited:
        _, reason = check_grounding(answer, cited, [faq_by_id[i] for i in cited if i in faq_by_id], case["question"])
        invented = reason if reason and reason.startswith("numbers") else None

    expected = set(case["expected_faq_ids"])
    if any(text not in answer for text in case.get("expected_in_answer", [])):
        return "WRONG", invented
    if any(text.lower() in answer.lower() for text in case.get("must_not_contain", [])):
        return "UNSAFE", invented
    if set(cited) == expected:
        return "PASS", invented
    if expected and not cited:
        return "FALLBACK", invented
    if expected and set(cited) < expected:
        return "PARTIAL", invented
    return "WRONG", invented


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=sorted(TEST_SETS), default="v2")
    args = parser.parse_args()
    base_url = os.environ.get("ASSISTANT_BASE_URL", "http://localhost:8000")
    cases = json.loads(TEST_SETS[args.set].read_text(encoding="utf-8"))
    faq_by_id = {item.faq_id: item for item in load_faq_base(FAQ_PATH)}

    results: list[tuple[dict, str, list[str], str | None]] = []
    print(f"{'kind':<11} {'question':<58} {'expected':<18} {'cited':<18} result")
    with httpx.Client(base_url=base_url, timeout=20.0) as client:
        for case in cases:
            session_id = f"eval-{uuid.uuid4()}"
            if "after" in case:
                ask(client, case["after"], session_id)
            body = ask(client, case["question"], session_id)
            result, invented = score(case, body, faq_by_id)
            cited = cited_faq_ids(body)
            results.append((case, result, cited, invented))
            expected = ",".join(case["expected_faq_ids"]) or "-"
            flag = "  INVENTED " + invented if invented else ""
            print(f"{case['kind']:<11} {case['question'][:56]:<58} {expected:<18} {','.join(cited) or '-':<18} {result}{flag}")

    passed = sum(result == "PASS" for _, result, _, _ in results)
    fallback_cases = [r for r in results if not r[0]["expected_faq_ids"] and r[0]["kind"] not in ("tuition", "catalogue")]
    by_kind: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for case, result, _, _ in results:
        by_kind[case["kind"]][0] += result == "PASS"
        by_kind[case["kind"]][1] += 1

    print(f"\nAccuracy ({args.set}): {passed}/{len(results)} ({passed / len(results):.0%}) against {base_url}")
    print(f"Correct fallbacks: {sum(r[1] == 'PASS' for r in fallback_cases)}/{len(fallback_cases)}")
    print(f"Invented facts: {sum(r[3] is not None for r in results)}")
    print("By kind: " + ", ".join(f"{kind} {ok}/{total}" for kind, (ok, total) in sorted(by_kind.items())))
    failures = [r for r in results if r[1] != "PASS" or r[3]]
    if failures:
        print("\nFailures:")
        for case, result, cited, invented in failures:
            print(f"- [{result}] {case['question']} (expected {case['expected_faq_ids'] or 'none'}, cited {cited or 'none'})"
                  + (f"; {invented}" if invented else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
