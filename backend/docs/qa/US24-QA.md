# US24 QA record — saved programs

Date: 2026-10-22. Local API, PostgreSQL, Vite and Mailpit on `feature/sprint-5-applicant-area`. Live acceptance open.

| Check | Result |
| --- | --- |
| `tests/test_applicant.py` | PASS: idempotent saves, separate local/international rows, persistent lists, two-account isolation, wrong/missing/archived program rejection, removal clears only the selected checklist and its prepared flags, archived saves remain visible |
| Applicant browser matrix (part of **97/97**) | PASS in Chromium/Firefox at 360/768/1280 px: save from public program detail, reload, separate applicant types, remove and empty state; labels/layout in EN/RU/KK |
| Existing compare browser regression | **60/60** |

US24QATest pass and fail cases pass locally. The save action preserves the selected applicant type; a signed-out save sends the user to login with a validated local return path.
