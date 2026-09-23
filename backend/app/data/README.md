# Data files

## Catalogue

- `catalogue.json` — official program catalogue and document requirements (T0.6),
  collected from sdu.edu.kz on 2026-09-23, pending admissions office review.
  Source of truth for `scripts/import_catalogue.py`, which the API container runs on
  every start: edit this file, never the database by hand. Fees are per ECTS credit
  from the 2026-2027 fee orders; `null` means not published. An applicant type left
  out of `documents` has no official list, so the API returns the missing-data warning.
- `catalogue_evidence.json` — for each program field and document list, the source page
  and the quote it was taken from, for the admissions office review.

## FAQ base

- `faq.json` — official FAQ (T3.1): 35 items collected from sdu.edu.kz on 2026-09-23,
  pending review by the admissions office. Each item has `faq_id, question, answer,
  category, source_link, last_update` and an `evidence` quote copied from the source page
  (kept for the review, not used by the API).
  After editing, run `scripts/reindex_faq.py` (the API container does it on start).
