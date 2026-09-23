# US1 QA run - results

- Environment: `http://localhost:8000`
- Executed: 2026-09-23 20:11 UTC
- Script: `backend/scripts/qa_us1.py`

| Scenario | Result | Details |
| -------- | ------ | ------- |
| US1-1 Full catalogue with total | PASS | 12 active programs listed, total matches |
| US1-2 Keyword search | PASS | q='Applied' -> 6; q='applied' -> 6; q='APPLIED' -> 6 |
| US1-3 Combined filters (AND) | PASS | 7 combinations (AND) match: faculty -> 3; degree_level -> 10; language -> 1; faculty+degree_level -> 2; faculty+language -> 1; degree_level+language -> 1; faculty+degree_level+language -> 1 |
| US1-4 No results -> 200, total 0 | PASS | HTTP 200, total=0, programs=[] for q='zzz-qa-no-such-program' |
| US1-6 Program detail and 404 | PASS | 6B04201 -> 200; unknown id -> 404 PROGRAM_NOT_FOUND |

- Environment: `http://localhost:8000`
- Executed: 2026-09-23 20:11 UTC
- Script: `backend/scripts/qa_us1.py`

| Scenario | Result | Details |
| -------- | ------ | ------- |
| US1-5 Database unavailable -> 503 | PASS | HTTP 503, error_code=DATABASE_UNAVAILABLE, Retry-After present |
