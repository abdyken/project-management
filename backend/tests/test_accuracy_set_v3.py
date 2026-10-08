from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from run_accuracy_test import TEST_SET_PATH, TEST_SETS  # noqa: E402

V2 = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
V3 = json.loads(TEST_SETS["v3"].read_text(encoding="utf-8"))


def test_v3_keeps_every_v2_case_unchanged():
    assert V3[: len(V2)] == V2


def test_v3_adds_new_items_kazakh_russian_and_catalogue_cases():
    added = V3[len(V2) :]
    kinds = [case["kind"] for case in added]
    assert len(V3) == 70
    assert kinds.count("new_item") >= 10
    assert kinds.count("kazakh") >= 5 and kinds.count("russian") >= 5
    assert kinds.count("catalogue") >= 3
    assert len({case["question"] for case in V3}) == len(V3)


def test_translated_cases_expect_items_with_that_translation(faq_items):
    by_id = {item.faq_id: item for item in faq_items}
    for case in V3[len(V2) :]:
        language = {"russian": "ru", "kazakh": "kk"}.get(case["kind"])
        for faq_id in case["expected_faq_ids"]:
            assert faq_id in by_id, case["question"]
            if language:
                assert by_id[faq_id].has(language), case["question"]
