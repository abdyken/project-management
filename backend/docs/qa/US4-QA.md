# US4 QA record (T4.4)

Run this on the deployed dev frontend after the Admissions Office supplies and approves the records. Do not mark a checklist verified from demo fixtures.

| Checklist to verify | Applicant type | Admissions Office verifier/date | API result | Page result | Chat result | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Programme 1 (local) | local | _pending_ | _pending_ | _pending_ | _pending_ | pending |
| Programme 2 (international) | international | _pending_ | _pending_ | _pending_ | _pending_ | pending |
| Programme 3 (missing-data case) | local or international | _pending_ | warning shown | warning shown | warning shown | pending |

For each populated checklist, compare every document name, format, translation/notarisation flag and deadline against the approved admissions source. For the missing-data case, confirm that no empty table is shown and that the user is directed to the Admissions Office.
