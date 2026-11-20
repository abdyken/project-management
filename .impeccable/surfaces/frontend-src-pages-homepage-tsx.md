---
version: 1
slug: "frontend-src-pages-homepage-tsx"
primary_target: "frontend/src/pages/HomePage.tsx"
related_targets: ["frontend/src/pages/ProgramsPage.tsx","frontend/src/pages/ProgramDetailPage.tsx"]
---

# Surface: public site (home first), SDU admissions portal

**Scope:** the home page, then the public pages that inherit it (programmes, programme
detail, compare, admissions planning).

**Visitor mode:**
- Persuade: home and programmes
- Read: planning guides
- Operate: the applicant and staff areas inherit the world in this mode

**Audience and job:** Kazakh school leavers and their parents, mostly on phones in KK/RU.
They decide on a programme, check deadlines, cost and documents, then apply.

**Primary action, in working form:** programme search plus Apply.

**Proof:** real catalogue data (64 programmes, deadlines, tuition per ECTS), the official
tagline, real campus photos.

**Constraints:** PRODUCT.md; the e2e role/label contract; KK/RU/EN parity; WCAG 2.2 AA.

**Pinned by the user (20.11.2026):**
- Purdue page structure
- campus photo hero
- not a copy of sdu.edu.kz, so navy/peach is dropped
- main colour: smalt turquoise
- extraordinary, bolder

## Direction contract

THESIS: The admissions portal set like an Almaty modernist mosaic panel. Every section is
a flat colour field laid on one tessera grid, so programmes, dates and steps read as tiles
of one monumental wall. It refuses the category default of a white page with a photo hero
and a row of equal cards.

OWN-WORLD:
- Smalt turquoise #0A6C74 owns 30–60% of the surface as solid fields.
- Glacier turquoise #19A7A8, apricot ochre #E3A33A (primary action) and terracotta #C5532F
  appear only as square tesserae and as state.
- Ink #121417 on cool white #F5F7F6 for reading.
- Square corners, an 8 px tessera module, tile bands at field edges, no gradients, no
  shadows beyond one flat offset.
- Monumental condensed caps for headlines; a sturdy text sans for everything else.
- SDU emblem in one colour: white on fields, ink on light.

STORY: The visitor sees SDU's campus inside a mosaic frame and reads "Making your dreams a
reality". They search for a programme at once, pick their path by certificate, see the
real dates and costs as tiles, and always know the next step: apply, check status or ask.

FIRST VIEWPORT:
- The full-bleed autumn campus photo fills the top ~60%.
- A turquoise mosaic band rises from the bottom edge, with a stepped tessera edge.
- Inside the band, left: the headline in white monumental caps (2–3 lines).
- Inside the band, right: a white search tile with the "Find your programme" input and the
  ochre "Search 64 programmes" action.
- The header above is a turquoise bar with the white emblem lockup, four links and an
  ochre Apply.

FORM:
- **World:** Almaty modernist mosaic panel, candidate 7 of 7 on the ordered list, built in
  the bolder register at the user's request. seed:1d9a155aafbb94bb.
- **Signature interaction:** tesserae set in place as a section enters (staggered; static
  under reduced motion), and filter changes re-lay the programme tiles.
- **Raises:**
  - fixed three-line programme tiles (pulp rack)
  - one marked deciding fact per guide step (zine)
  - real tallies on every section heading (cloud quarry)
  - state as material: solid when open, outline when closed or unpublished (akari)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved
- Display and text faces: pick after the Kazakh glyph test.
- Where the HeroGlobe sits in the International band (kept, moved out of the hero).
