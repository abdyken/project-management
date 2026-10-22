# US7 QA record — deadline reminders

Date: 2026-10-22. Local PostgreSQL and real SMTP delivery to Mailpit on `feature/sprint-5-applicant-area`. Live SMTP and acceptance open.

| Check | Result |
| --- | --- |
| `tests/test_applicant.py` | PASS: opt-in default off; 7/1/0-day milestones; correct applicant-type date; no overdue or unpublished-date messages; localized subjects; current unprepared documents; repeated runs suppressed; failed SMTP retried; archived programs skipped; opt-out and cascading account deletion |
| Actual SMTP smoke | PASS: temporary verified Kazakh account, saved official Computer Science checklist, one prepared document; delivered message contains the official date and remaining documents, excludes the prepared document; second run sends zero; temporary account removed |
| Applicant browser matrix (part of **97/97**) | PASS: preference and language persist across reload, opt-in and opt-out work in both browsers/all widths |

The SMTP smoke uses the official program deadline minus seven days as the job's injected test date; it does not edit catalogue deadlines or send to external recipients. The API worker runs hourly in production; `scripts/send_reminders.py` invokes the same job manually.

US7QATest pass and fail cases pass locally. Delivery semantics and outage limitations are in `backend/docs/api/applicant.md`; an SMTP acceptance followed by a process crash before commit may be retried.
