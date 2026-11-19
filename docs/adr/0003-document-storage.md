# ADR 0003: Storing uploaded documents

**Date:** 19.11.2026. **Status:** accepted.

## Context
US32 stores scans of personal documents. The VM has 1 GB RAM and 35 GB free disk; the
team has no paid storage.

## Decision
- Files go to a Docker volume (`uploads`) on the VM under random names; the database
  keeps the original name, type, size and SHA-256.
- Accepted: PDF, JPEG and PNG, recognised by their first bytes, not by name or browser
  type. Up to 10 MB per file and 40 MB per application. Uploads are streamed to disk in
  chunks, never held in memory whole.
- Files are only served through the API, to the owner or staff, as attachments with
  `nosniff` and `no-store`. They are deleted with the document, the draft application
  or the account.
- Uploads are off in production (`APPLICATIONS_ENABLED=false`) until a daily backup of
  the database and the volume runs and the hosting decision is recorded.

## Alternatives considered
- **Oracle Object Storage (free 20 GB)**: credentials, signed URLs and a new SDK for no
  benefit at this volume.
- **Files in PostgreSQL**: bloats backups and the 1 GB server's database.

## Consequences
No antivirus on the free server: staff download files instead of opening them inline.
Backups must include the `uploads` volume.
