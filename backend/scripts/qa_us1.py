from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

NO_MATCH_KEYWORD = "zzz-qa-no-such-program"


@dataclass
class Result:
    scenario: str
    status: str
    details: str


class QAFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise QAFailure(message)


class US1QA:
    def __init__(self, client: httpx.Client):
        self.client = client
        self._catalogue: list[dict] | None = None

    def get_programs(self, **params) -> dict:
        response = self.client.get("/api/programs", params=params)
        check(response.status_code == 200, f"GET /api/programs {params} -> HTTP {response.status_code}: {response.text[:200]}")
        body = response.json()
        check("total" in body, f"'total' missing in response to {params}")
        check(body["total"] == len(body["programs"]), f"total={body['total']} but {len(body['programs'])} programs for {params}")
        return body

    @property
    def catalogue(self) -> list[dict]:
        if self._catalogue is None:
            self._catalogue = self.get_programs()["programs"]
        check(len(self._catalogue) > 0, "catalogue is empty - import the program data first (T1.2)")
        return self._catalogue

    @staticmethod
    def ids(programs: list[dict]) -> list[str]:
        return sorted(program["program_id"] for program in programs)

    def expect_same(self, params: dict, expected: list[dict]) -> int:
        body = self.get_programs(**params)
        check(
            self.ids(body["programs"]) == self.ids(expected),
            f"{params}: got {self.ids(body['programs'])}, expected {self.ids(expected)}",
        )
        return body["total"]


    def full_catalogue(self) -> str:
        programs = self.catalogue
        check(all(program["is_active"] for program in programs), "an inactive program is listed")
        return f"{len(programs)} active programs listed, total matches"

    def keyword_search(self) -> str:
        title = self.catalogue[0]["title"]
        keyword = max(title.split(), key=len)
        checked = []
        for variant in (keyword, keyword.lower(), keyword.upper()):
            expected = [
                program for program in self.catalogue
                if any(variant.lower() in program[field].lower() for field in ("title", "faculty", "program_id"))
            ]
            total = self.expect_same({"q": variant}, expected)
            checked.append(f"q={variant!r} -> {total}")
        return "; ".join(checked)

    def combined_filters(self) -> str:
        sample = self.catalogue[0]
        combinations = [
            {"faculty": sample["faculty"]},
            {"degree_level": sample["degree_level"]},
            {"language": sample["language"]},
            {"faculty": sample["faculty"], "degree_level": sample["degree_level"]},
            {"faculty": sample["faculty"], "language": sample["language"]},
            {"degree_level": sample["degree_level"], "language": sample["language"]},
            {"faculty": sample["faculty"], "degree_level": sample["degree_level"], "language": sample["language"]},
        ]
        checked = []
        for params in combinations:
            expected = [
                program for program in self.catalogue
                if all(program[field].lower() == value.lower() for field, value in params.items())
            ]
            check(expected, f"{params} should match at least {sample['program_id']}")
            total = self.expect_same(params, expected)
            checked.append(f"{'+'.join(params)} -> {total}")
        return f"{len(combinations)} combinations (AND) match: " + "; ".join(checked)

    def no_results(self) -> str:
        body = self.get_programs(q=NO_MATCH_KEYWORD)
        check(body == {"total": 0, "programs": []}, f"expected empty result, got {body}")
        if not self.get_programs()["programs"]:
            return f"HTTP 200, total=0, programs=[] for q={NO_MATCH_KEYWORD!r} (filter case skipped: catalogue empty)"
        other_level = next(
            (level for level in ("bachelor", "master", "phd")
             if not any(p["degree_level"] == level and p["faculty"] == self.catalogue[0]["faculty"] for p in self.catalogue)),
            None,
        )
        if other_level:
            body = self.get_programs(faculty=self.catalogue[0]["faculty"], degree_level=other_level)
            check(body["total"] == 0, f"faculty + degree_level={other_level} should be empty, got {body['total']}")
        return f"HTTP 200, total=0, programs=[] for q={NO_MATCH_KEYWORD!r}"

    def program_detail(self) -> str:
        sample = self.catalogue[0]
        response = self.client.get(f"/api/programs/{sample['program_id']}")
        check(response.status_code == 200, f"detail -> HTTP {response.status_code}")
        check(response.json() == sample, "detail differs from the list entry")
        response = self.client.get(f"/api/programs/{NO_MATCH_KEYWORD}")
        check(response.status_code == 404, f"unknown id -> HTTP {response.status_code}, expected 404")
        check(response.json().get("error_code") == "PROGRAM_NOT_FOUND", f"unknown id body: {response.text[:200]}")
        return f"{sample['program_id']} -> 200; unknown id -> 404 PROGRAM_NOT_FOUND"

    def database_unavailable(self) -> str:
        response = self.client.get("/api/programs", params={"q": "computer"})
        check(response.status_code == 503, f"HTTP {response.status_code}, expected 503 (is the database really stopped?)")
        body = response.json()
        check(body.get("error_code") == "DATABASE_UNAVAILABLE", f"error_code={body.get('error_code')!r}")
        check("Retry-After" in response.headers, "Retry-After header missing")
        return "HTTP 503, error_code=DATABASE_UNAVAILABLE, Retry-After present"


def run(scenarios: list[tuple[str, Callable[[], str]]]) -> list[Result]:
    results = []
    for name, scenario in scenarios:
        try:
            results.append(Result(name, "PASS", scenario()))
        except QAFailure as failure:
            results.append(Result(name, "FAIL", str(failure)))
        except httpx.HTTPError as error:
            results.append(Result(name, "FAIL", f"request failed: {error!r}"))
    return results


def render_report(base_url: str, results: list[Result]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# US1 QA run - results",
        "",
        f"- Environment: `{base_url}`",
        f"- Executed: {timestamp}",
        "- Script: `backend/scripts/qa_us1.py`",
        "",
        "| Scenario | Result | Details |",
        "| -------- | ------ | ------- |",
    ]
    for result in results:
        details = result.details.replace("|", "\\|")
        lines.append(f"| {result.scenario} | {result.status} | {details} |")
    return "\n".join(lines) + "\n"


DESCRIPTION = "Run the US1 QA scenarios against a running API."


def main() -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--db-down", action="store_true", help="only run the database-unavailable scenario")
    parser.add_argument("--report", type=Path, help="write the results as a Markdown table")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds; high default because a sleeping free-tier server can take ~50 s to wake up")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
        qa = US1QA(client)
        if args.db_down:
            scenarios = [("US1-5 Database unavailable -> 503", qa.database_unavailable)]
        else:
            scenarios = [
                ("US1-1 Full catalogue with total", qa.full_catalogue),
                ("US1-2 Keyword search", qa.keyword_search),
                ("US1-3 Combined filters (AND)", qa.combined_filters),
                ("US1-4 No results -> 200, total 0", qa.no_results),
                ("US1-6 Program detail and 404", qa.program_detail),
            ]
        results = run(scenarios)

    width = max(len(result.scenario) for result in results)
    for result in results:
        print(f"{result.status:4}  {result.scenario:<{width}}  {result.details}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if args.db_down and args.report.exists() else "w"
        with args.report.open(mode, encoding="utf-8") as report:
            report.write(render_report(args.base_url, results) if mode == "w" else "\n" + render_report(args.base_url, results).split("\n", 2)[2])
        print(f"Report written to {args.report}")

    return 0 if all(result.status == "PASS" for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
