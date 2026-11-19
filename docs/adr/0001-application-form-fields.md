# ADR 0001: Application form fields

**Date:** 19.11.2026. **Status:** accepted (Sprint 7, Product Owner Askhat).

## Context
US31 needs an online application form. The admissions office has not provided the
official form, and the portal runs on a free 1 GB server in the Oracle Dubai region
(see `../applicant-hosting.md`).

## Decision
One application per programme and applicant type, with these fields:
full name, date of birth, citizenship, phone, previous education
(school, college, bachelor, master), graduation year, UNT or CT total (optional) and
consent to processing personal data. No national ID (IIN) or passport numbers.

## Alternatives considered
- **Copy the full official form** (IIN, parents, address, military service): not
  provided by the office, and the most sensitive data on a free server.
- **No form, documents only**: staff could not review without basic facts.

## Consequences
The flow can be tested end to end without the most sensitive identifiers. When the
office provides the official form, fields are added in a new migration; existing
applications keep their data.
