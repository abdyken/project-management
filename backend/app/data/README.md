# Data files

## Real data

- `catalogue.json` — the official program catalogue and document requirements
  (T0.6). Source of truth for `scripts/import_catalogue.py`, which the API
  container runs on every start: edit this file, never the database by hand.
  Each program needs a `source_url` to the official page (to be filled by the
  Product Owner); `null` values mean "unknown in the official data".

# FAQ base

- `faq_sample.json` — stand-in for **T3.1** until the official FAQ is collected.
  Fields: `faq_id, question, answer, category, source_link, last_update`.
  After editing, run `scripts/reindex_faq.py` (the API container does it on start).
