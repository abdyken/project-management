# US13 QA record — answer feedback

Date: 2026-10-02. The attached `US13QATest` sheet defines two dev scenarios: a thumbs-down rating with reason `Outdated` stored with its question, answer and sources; and a Product Owner CSV export of thumbs-down answers from the last seven days, after at least five answers have been rated.

| Environment | Check | Result |
| --- | --- | --- |
| Local isolated PostgreSQL with pgvector | Feedback API, unique answer rating, invalid input, stored context, seven-day export, migration metadata | PASS — `pytest tests/test_feedback.py tests/test_migrations.py -q`: 5 passed |
| Deployed dev | Rate an answer in the widget and confirm stored question, answer, sources and reason | PENDING — no deployed dev URL is recorded in this repository; the new branch has not been deployed |
| Deployed dev | Rate at least five answers; export the last seven days and verify the CSV has negative answers, reason and sources without applicant identifiers | PENDING — requires the deployed branch and access to its database |

## Update 2026-10-08

- Review fix: `POST /api/assistant/feedback` now requires the `session_id` of the chat the answer was given in. An answer of another session, or an id beyond the id range, returns `404 ANSWER_NOT_FOUND`, so sequential ids cannot be used to rate other applicants' answers. The widget sends its session id.
- The widget's reasons now match the story card: Wrong, Outdated, Unclear, Other, plus *Skip reason* (the reason is optional). A second rating of the same answer (`409 ALREADY_RATED`) is shown as rated instead of an error.
- `pytest tests/test_feedback.py`: 8 passed (cross-session rating, id range and required session id added).
- Local widget run (`frontend/e2e/widget-qa.mjs`, Chromium and Firefox at 360, 768 and 1280 px): thumbs down + Outdated disables both buttons, and the rating is still shown after navigating to `/programs` — PASS in all six runs.

The story cannot be accepted under the sprint Definition of Done until both dev scenarios pass. Run `uv run python scripts/export_negative_feedback.py --days 7 --output feedback.csv` in the dev backend environment and review free text for personal details before handing the file to the Product Owner.
