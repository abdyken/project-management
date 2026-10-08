from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PATH = BACKEND_ROOT / "app" / "data" / "catalogue.json"

DESCRIPTION = """US12 catalogue answer check against a running API.

    ASSISTANT_BASE_URL=<dev-url> uv run python scripts/check_catalogue_answers.py

Asks the fee, deadline and language of every program in catalogue.json and checks
each answer against the catalogue: every published number must appear, an
unpublished value must be answered as not published, and no answer may name a
fee or date the catalogue does not have."""

_THOUSANDS = re.compile(r"(?<=\d)[ ,  ](?=\d{3}\b)")
_NUMBER = re.compile(r"\d+")


@dataclass(frozen=True)
class Case:
    program_id: str
    topic: str
    question: str
    expected: tuple[str, ...]
    unpublished: bool


def load_programs(path: Path = CATALOGUE_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["programs"]


def cases(programs: list[dict]) -> list[Case]:
    result = []
    for program in programs:
        name = f"{program['title']} ({program['program_id']})"
        fees = [program["tuition_per_ects_kzt"], program["tuition_per_ects_usd"]]
        result.append(
            Case(
                program["program_id"],
                "fee",
                f"How much does one ECTS cost for {name}?",
                tuple(str(fee) for fee in fees if fee is not None),
                all(fee is None for fee in fees),
            )
        )
        deadlines = [program["deadline_local"], program["deadline_international"]]
        result.append(
            Case(
                program["program_id"],
                "deadline",
                f"When is the application deadline for {name}?",
                tuple(number for deadline in deadlines if deadline for number in _NUMBER.findall(deadline)),
                any(deadline is None for deadline in deadlines),
            )
        )
        result.append(
            Case(
                program["program_id"],
                "language",
                f"What is the language of instruction for {name}?",
                tuple(language.strip() for language in (program["language"] or "").split(",") if language.strip()),
                program["language"] is None,
            )
        )
    return result


def numbers(text: str) -> set[str]:
    return {match.lstrip("0") or "0" for match in _NUMBER.findall(_THOUSANDS.sub("", text))}


def check(case: Case, answer: str, program: dict) -> str | None:
    if case.topic == "language":
        if case.unpublished:
            return None if "not publish" in answer.lower() else "unpublished language not reported as not published"
        missing = [language for language in case.expected if language.lower() not in answer.lower()]
        return f"missing language {missing}" if missing else None

    found = numbers(answer)
    missing = [value for value in case.expected if (value.lstrip("0") or "0") not in found]
    if missing:
        return f"missing {missing}"
    if case.unpublished and "not publish" not in answer.lower():
        return "unpublished value not reported as not published"
    facts = {key: value for key, value in program.items() if key != "documents"}
    allowed = numbers(json.dumps(facts)) | numbers(case.question) | _contact_numbers()
    invented = sorted(found - allowed, key=int)
    return f"numbers not in the catalogue {invented}" if invented else None


def _contact_numbers() -> set[str]:
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.config import get_settings

    return numbers(get_settings().admissions_office_contact)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    base_url = os.environ.get("ASSISTANT_BASE_URL", "http://localhost:8000")
    programs = {program["program_id"]: program for program in load_programs()}
    failures = []
    all_cases = cases(list(programs.values()))
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for case in all_cases:
            body = client.post(
                "/api/assistant/ask", json={"question": case.question, "session_id": f"catalogue-{uuid.uuid4()}"}
            ).json()
            problem = check(case, body["answer"], programs[case.program_id])
            links = [source["link"] for source in body.get("sources", [])]
            if problem is None and not case.unpublished and programs[case.program_id]["source_url"] not in links:
                problem = "program page not linked"
            print(f"{'FAIL' if problem else 'PASS'} {case.program_id} {case.topic:<8} {problem or ''}")
            if problem:
                failures.append((case, problem, body["answer"]))

    print(f"\n{len(all_cases) - len(failures)}/{len(all_cases)} catalogue answers match the catalogue ({base_url})")
    for case, problem, answer in failures:
        print(f"- {case.question}: {problem}\n  {answer}")
    return 1 if failures else 0


if __name__ == "__main__":
    if "--help" in sys.argv:
        print(DESCRIPTION)
        raise SystemExit(0)
    raise SystemExit(main())
