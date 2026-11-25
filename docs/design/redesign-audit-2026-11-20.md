# Redesign audit (after)

**Date:** 20.11.2026.
**Method:** the same ECC `design-system` audit as the baseline
(`baseline-audit-2026-11-20.md`), plus the impeccable finish review, which went through
three rounds and ended with the verdict "ship".
**Evidence:**
- **Screenshots:** `.impeccable/review/*.png`, at 360, 390, 1024 and 1440 px, in EN, KK and RU.
- **Lighthouse:** run on the production build.
- **Browser QA:** the seven `frontend/e2e/*.mjs` suites.
- **Layout probes (Playwright):** no horizontal overflow, no heading word split across
  lines, and the placeholder fits the phone search field.

**Direction:** Almaty Mosaic. Smalt turquoise #0A6C74 fields on one 8 px tessera grid,
Fira Sans Extra Condensed + Golos Text. See `DESIGN.md` and `PRODUCT.md`.

## Scores (0-10), before → after

| # | Dimension | Before | After | What changed |
| --- | --- | --- | --- | --- |
| 1 | Colour consistency | 5 | 9 | Every colour is a token. The real SDU logo is shown in one colour, white or ink. Chart colours come from the palette. One accepted exception: the shaded `HeroGlobe`, kept as a teammate's component. |
| 2 | Typography hierarchy | 4 | 9 | Display + text pairing with full Kazakh coverage. One type scale for page titles. 16 px body. No text under 12 px. KK/RU headings have line-height for diacritics. No heading word splits at 360/1024/1440 (measured). |
| 3 | Spacing rhythm | 5 | 8 | `PageShell` widths and one vertical rhythm. Band → tessera edge → content on every public page. Some staff forms keep their own containers. |
| 4 | Component consistency | 4 | 8 | Shared Button, Badge, Input, field styles, MosaicTile, Tesserae, ApplicationStepper. One card language (square tiles). |
| 5 | Responsive | 6 | 9 | No horizontal overflow from 360 to 1440 px in KK/RU/EN (measured). A finder layout replaces the 7,000 px card wall. A phone gutter keeps the chat launcher clear of the search tile. |
| 6 | Dark mode | 0 | 0 | Out of scope by decision. Applicants use it on phones in daylight. Recorded in DESIGN.md. |
| 7 | Animation | 6 | 7 | One authored moment: tesserae set in, with a short scattered stagger. 0.2 s state transitions; arrows slide 3 px. Static under reduced motion. |
| 8 | Accessibility | 8 | 9 | Lighthouse accessibility 97, and its one finding (footer heading contrast) is fixed. Status shown by icon + words. Skip link. Visible focus on every control. All earlier a11y behaviour kept. |
| 9 | Information density | 5 | 8 | The home page carries real dates, costs, paths and schools. Program tiles have three fixed lines. The checklist drops empty columns and states the shared deadline once. Hub tiles show live facts. |
| 10 | Polish | 5 | 8 | Arrow CTAs. A full footer with credits. Selection, caret, scrollbar and focus are themed. "program" spelling is consistent in EN. |

**Total: 48 → 75 / 100.** Excluding dark mode, which is out of scope: 75 / 90.

## AI-slop check, after

| Pattern | Before | After |
| --- | --- | --- |
| Generic hero (slogan + abstract visual) | yes | no: real campus photo, the official tagline, a working search |
| Personality-free sans everywhere | yes | no: condensed display caps + Golos Text |
| Numbered 01/02/03 steps | yes | no |
| Eyebrow labels above headings | yes (13) | no |
| Uniform identical card grids | yes | no: unequal mosaic tiles; program tiles grouped by state |
| Defensive AI-product copy | yes | no |
| Emoji as UI | yes | no: drawn icons with screen-reader labels |
| Off-brand identity | yes (placeholder logo) | no: SDU's own logo, credited photography |
| Gradients / glass / soft shadows | no | no (flat ink ring on overlays; one sanctioned globe exception) |

`impeccable detect --json frontend/src` returns no findings.

## Premium refinement (21.11.2026)

**Why:** Dimash said some places "look like a kid website" and asked for a premium,
institutional feel like Purdue's.

**Evidence:** a read-only critique of the screenshots, plus research into Purdue, Stanford,
Yale, Cambridge, ETH and Tate (their CSS and brand guides). Both pointed at the same
causes:
- four saturated hues used as blocks side by side
- random multicolour "confetti" tile edges
- sticker tile clusters
- pop-in animation
- coloured and dashed program cards
- uppercase condensed headings everywhere

**Changes:**
- **Headings:** Source Serif 4 in sentence case. Condensed caps are kept only for short
  labels, numerals and the primary action.
- **Colour:** one brand hue (turquoise + deep) on cool neutrals. Ochre is used only for
  Apply and Search, terracotta only for errors, glacier only for selection.
- **Tiles:** path and hub tiles are one turquoise main tile carrying a real campus photo,
  plus quiet white cards.
- **Mosaic:** it is now a signature used twice per page: a stepped edge of 16 px tesserae
  with grout lines, where the hero band and the footer rise.
- **Program cards and filters:** cards are plain white with hairlines, and filters are a
  hairline checklist.
- **Photo:** the studio photo is replaced with the natural-light main-hall photo.

**Not changed:** program name casing ("Applied law" / "Applied Law") is SDU's official
catalogue data. It is left for the catalogue owner to clean up, not rewritten in the UI.

| Dimension | Before redesign | After redesign | After refinement |
| --- | --- | --- | --- |
| Colour consistency | 5 | 9 | 10 |
| Typography hierarchy | 4 | 9 | 10 |
| Spacing rhythm | 5 | 8 | 8 |
| Component consistency | 4 | 8 | 9 |
| Responsive | 6 | 9 | 9 |
| Dark mode (out of scope) | 0 | 0 | 0 |
| Animation | 6 | 7 | 8 |
| Accessibility | 8 | 9 | 9 |
| Information density | 5 | 8 | 8 |
| Polish | 5 | 8 | 9 |
| **Total** | **48** | **75** | **80** |

**Measured saturated share** (pixels within 6% of turquoise, deep turquoise or ochre in
full-page 1280 px captures):

| Page | Turquoise / deep | Ochre | Notes |
| --- | --- | --- | --- |
| Home | 27.5% | 0.5% | The hero band, the cost ledger and the footer. The path cards, the International band and the lists are neutral or a light tint. |
| Admissions hub | 56% | 0.3% | A short page, so the title band and the deep footer take a large share of its height. The tool tiles are white apart from the one photo tile. |

Before the refinement, the hub tiles alone were four saturated hues side by side.

## Independent audits, 21.11.2026

Two read-only auditors reviewed the live site in a browser. They were given the same brief before and after the changes and were not told what had changed.

| Audit | Before | After | What moved the score |
| --- | --- | --- | --- |
| Premium / AI-slop (design director) | 6/10 | 6.5/10 | No internal research notes and no stale "upcoming" dates shown to applicants; one page frame; hub as ruled lists; a phone action bar instead of floating buttons. Still held back by stock program photos (kept by decision), the cobe globe (kept, now centred on Almaty) and a 2026 cycle that is over. |
| Purdue fidelity (information architecture) | not scored; Apply, Deadlines, Status and Contact missing | 7.5/10 | New /apply, /deadlines, /application-status and /contact; quick links and search in the header; "Information for" in the footer; a program page with breadcrumb, Apply, entry requirements and related programs. |

Where both auditors say we already beat Purdue:
- real dates and fees on every program
- document checklists by applicant type, with save and PDF
- entry requirements with sources
- one deadlines page with a live status
- Compare
- KK/RU/EN

### Remaining, not done in this pass

These items need a decision or data we do not have:
- **2027 intake dates.** The site says when a cycle is over, but it cannot announce the next one before the office publishes it.
- **Site-wide search across programs, FAQ and pages.** The header search reaches the program finder only.
- **A cost-and-aid hub page.**
- **A footer legal bar** (privacy, accessibility, "catalogue last checked").
- **Catalogue wording for the catalogue owner.** Examples: "Applied law" / "Applied Law" casing; KK titles that differ between degrees, such as "Компьютерлік ғылымдар" and "Компьютер ғылымдары"; per-credit fees like 41,667 ₸ that come from annual fees.
- **Mixed Kazakh "өтініш" / "өтінім"** in older strings. A native speaker should settle the glossary.
