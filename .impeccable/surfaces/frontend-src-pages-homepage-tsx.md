---
version: 1
slug: "frontend-src-pages-homepage-tsx"
primary_target: "frontend/src/pages/HomePage.tsx"
related_targets: ["frontend/src/pages/ProgramsPage.tsx","frontend/src/pages/ProgramDetailPage.tsx"]
---

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

THESIS: The admissions portal as a calm institutional document with one Almaty-mosaic
signature. Sections are white and cool-neutral pages structured by serif headings and
hairline ledgers; one turquoise field per group carries the main path. It refuses both the
category default (photo hero plus a row of equal cards) and the earlier multicolour tile wall.

OWN-WORLD (refined 21.11.2026 on Dimash's decision):
- Smalt turquoise #0A6C74 and deep #074F55 are the only brand fields, on cool neutral
  #F5F7F6 and white, with slate ink #17222A.
- Ochre #E3A33A only for the primary action (header Apply, hero Search). Terracotta only for
  errors. Glacier only for selection.
- Headings: Source Serif 4, sentence case, weight 500. Condensed caps (Fira Sans Extra
  Condensed) only for short labels, numerals and the primary action. Body: Golos Text.
- Square corners, 1px hairlines, no gradients, no soft shadows (overlays use a flat ink ring).
- Real SDU photography, including inside the main path tile.
- The mosaic is a monochrome signature, at most twice per page: a stepped edge of 16px
  turquoise tesserae (deep cap on a field body) where the hero band rises into the photo, and
  the same profile where the footer rises into the page.

STORY: The visitor sees SDU's campus, reads "Study at the foot of the Alatau" set as a calm serif
headline, and searches at once. They pick a path from one turquoise main tile and quiet white
cards, read the real dates and costs as ledgers, and always know the next step: apply, check
status or ask.

FIRST VIEWPORT:
- The full-bleed autumn campus photo fills the top ~55%.
- The turquoise band rises into it as a stepped 16px mosaic edge.
- Left: the serif headline (2 lines) and the catalogue tally.
- Right: a white search tile overlapping the photo, with "Find your program", the input and
  the ochre "Search 64 programs" action.
- The header above is a turquoise bar with the white lockup, the nav and the ochre Apply.

FORM:
- **World:** Almaty modernist mosaic panel, candidate 7 of 7, seed:1d9a155aafbb94bb.
- **Register:** refined on 21.11.2026 from bolder to restrained at the user's request,
  because "some places look like a kid website".
- **Signature interaction:** the stepped edge fades in once (static under reduced motion);
  filter changes re-lay the program grid.
- **Kept raises:**
  - fixed three-line program cards
  - one deciding fact per tile
  - real tallies on headings
  - state stated in words (unpublished = muted text)
- **Sanctioned exception:** Daniyar's shaded HeroGlobe, kept in the International band.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved
- Where the HeroGlobe sits in the International band (kept, moved out of the hero).
