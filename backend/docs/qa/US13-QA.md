# US13 QA record — answer feedback

Date: 2026-10-02. The attached `US13QATest` sheet defines two dev scenarios: a thumbs-down rating with reason `Outdated` stored with its question, answer and sources; and a Product Owner CSV export of thumbs-down answers from the last seven days, after at least five answers have been rated.

| Environment | Check | Result |
| --- | --- | --- |
| Local isolated PostgreSQL with pgvector | Feedback API, unique answer rating, invalid input, stored context, seven-day export, migration metadata | PASS — `pytest tests/test_feedback.py tests/test_migrations.py -q`: 5 passed |
| Deployed dev | Rate an answer in the widget and confirm stored question, answer, sources and reason | PENDING — no deployed dev URL is recorded in this repository; the new branch has not been deployed |
| Deployed dev | Rate at least five answers; export the last seven days and verify the CSV has negative answers, reason and sources without applicant identifiers | PENDING — requires the deployed branch and access to its database |

The story cannot be accepted under the sprint Definition of Done until both dev scenarios pass. Run `uv run python scripts/export_negative_feedback.py --days 7 --output feedback.csv` in the dev backend environment and review free text for personal details before handing the file to the Product Owner.
