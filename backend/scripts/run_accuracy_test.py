from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

TEST_SET_PATH = Path(__file__).resolve().parent.parent / "tests" / "accuracy_test_set.json"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    base_url = os.environ.get("ASSISTANT_BASE_URL", "http://localhost:8000")
    cases = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))

    correct = wrong = 0
    print(f"{'question':<60} {'expected':<10} {'actual':<10} {'score':<6} result")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        for case in cases:
            response = client.post(
                "/api/assistant/ask", json={"question": case["question"], "session_id": "accuracy-test"}
            )
            response.raise_for_status()
            body = response.json()
            expected, actual = case["expected_faq_id"], body["faq_id"]
            score = "-" if body["similarity_score"] is None else f"{body['similarity_score']:.3f}"
            if actual == expected:
                result = "PASS"
                correct += 1
            elif actual is None:
                result = "FALLBACK"
            else:
                result = "WRONG"
                wrong += 1
            print(f"{case['question'][:58]:<60} {str(expected):<10} {str(actual):<10} {score:<6} {result}")

    print(f"\nAccuracy: {correct}/{len(cases)} ({correct / len(cases):.0%}), wrong answers: {wrong}, against {base_url}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
