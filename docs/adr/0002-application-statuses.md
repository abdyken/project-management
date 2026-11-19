# ADR 0002: Application statuses

**Date:** 19.11.2026. **Status:** accepted.

## Context
US33 lets an officer review submitted applications; US6 tells the applicant the stage
and the next step.

## Decision
`draft` → `submitted` → `in_review` → `needs_changes` (applicant edits and submits
again) → `accepted` or `rejected`. Only `draft` and `needs_changes` are editable by the
applicant. Staff may move `submitted` or `in_review` to any later status and must write
a note for `needs_changes` and `rejected`. `accepted` means the documents are complete;
it is not an admission decision. An applicant can delete only a `draft`, and can apply
again after `rejected`.

E-mails go out for `needs_changes`, `accepted` and `rejected` only: immediately after
the change, with the hourly worker as retry (same pattern as US30). They contain a link
to the account, not the note.

## Alternatives considered
- **Free-text status set by staff**: no reliable "next step" for US6.
- **Separate document-level approval**: more work than one sprint; the note covers it.

## Consequences
Each status has one fixed next step, so US6 answers are deterministic and translated.
