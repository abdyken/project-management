from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

TEST_SET_PATH = Path(__file__).resolve().parent.parent / "tests" / "accuracy_test_set.json"


def main() -> int:
    base_url = os.environ.get("ASSISTANT_BASE_URL", "http://localhost:8000")
    cases = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))

    correct = 0
    print(f"{'question':<60} {'expected':<10} {'actual':<10} {'score':<6} OK")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        for case in cases:
            response = client.post(
                "/api/assistant/ask", json={"question": case["question"], "session_id": "accuracy-test"}
            )
            response.raise_for_status()
            body = response.json()
            is_correct = body["faq_id"] == case["expected_faq_id"]
            correct += is_correct
            print(
                f"{case['question'][:58]:<60} {str(case['expected_faq_id']):<10} "
                f"{str(body['faq_id']):<10} {body['similarity_score']:.3f}  {'PASS' if is_correct else 'FAIL'}"
            )

    print(f"\nAccuracy: {correct}/{len(cases)} ({correct / len(cases):.0%}) against {base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
