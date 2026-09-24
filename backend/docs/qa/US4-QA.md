# US4 QA record (T4.4)

Run this on the deployed dev frontend after the Admissions Office supplies and approves the records. Do not mark a checklist verified from demo fixtures.

| Checklist to verify | Applicant type | Admissions Office verifier/date | API result | Page result | Chat result | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Programme 1 (local) | local | _pending_ | _pending_ | _pending_ | _pending_ | pending |
| Programme 2 (international) | international | _pending_ | _pending_ | _pending_ | _pending_ | pending |
| Programme 3 (missing-data case) | local or international | _pending_ | warning shown | warning shown | warning shown | pending |

For each populated checklist, compare every document name, format, translation/notarisation flag and deadline against the approved admissions source. For the missing-data case, confirm that no empty table is shown and that the user is directed to the Admissions Office.

## Local run — 2026-09-24

Docker stack, catalogue collected from sdu.edu.kz (pending Admissions Office approval, so the table above stays pending).

| Check | Result |
| --- | --- |
| Master program, local list (7M06101) | PASS — 7 documents with format and deadline |
| Bachelor program, international list (6B06102) | PASS — 16 documents (scans with the application, originals on arrival) |
| Chat returns the same list as the endpoint (6B06102, international) | PASS — same 16 documents in the same order |
| Programs sharing a title (Information Systems 6B06101 / 7M06101) | PASS — chat asks which program and names both codes; "Ask in chat" on the program page sends the code |
| Missing data (7M04115, international — SDU publishes no list) | PASS — page and chat show "The document list for this program is not published yet, please contact the admissions office." with the contact; case logged in `admissions_followup` |
| Phone width (375 px) | PASS — checklist shown as a list, no sideways scrolling |

Note: the QA sheet's US4-A uses a master program with international applicants; SDU publishes no international list for master's programs, so that case shows the missing-data warning.
