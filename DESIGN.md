---
name: SDU Admissions Portal
description: Almaty Mosaic. Flat turquoise fields on one 8px tessera grid, square corners, monumental condensed caps.
colors:
  smalt-turquoise: "#0a6c74"
  deep-turquoise: "#074f55"
  glacier: "#19a7a8"
  ochre: "#e3a33a"
  ochre-hover: "#d2912a"
  terracotta: "#c5532f"
  terracotta-text: "#b0432a"
  ink: "#121417"
  cool-white: "#f5f7f6"
  card-white: "#ffffff"
  field-mist: "#cdebe9"
  pale-turquoise: "#e4eeed"
  muted-surface: "#e9efee"
  accent-wash: "#d6ebea"
  slate-ink: "#4a5553"
  hairline: "#c9d4d2"
  input-stroke: "#7e908d"
typography:
  display:
    fontFamily: "Fira Sans Extra Condensed, Arial Narrow, ui-sans-serif, sans-serif"
    fontSize: "clamp(3.25rem, 8.2vw, 6rem)"
    fontWeight: 800
    lineHeight: 0.86
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Fira Sans Extra Condensed, Arial Narrow, ui-sans-serif, sans-serif"
    fontSize: "clamp(2.25rem, 4.4vw, 3.75rem)"
    fontWeight: 800
    lineHeight: 0.9
    letterSpacing: "0em"
  title:
    fontFamily: "Fira Sans Extra Condensed, Arial Narrow, ui-sans-serif, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0em"
  body:
    fontFamily: "Golos Text, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  body-small:
    fontFamily: "Golos Text, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 500
    lineHeight: 1.55
  label:
    fontFamily: "Fira Sans Extra Condensed, Arial Narrow, ui-sans-serif, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "0.04em"
rounded:
  none: "0px"
  operate: "2px"
spacing:
  tessera: "8px"
  tile-gap: "4px"
  tile-gap-wide: "8px"
  gutter-sm: "16px"
  gutter-md: "24px"
  gutter-lg: "32px"
  band: "80px"
  band-lg: "112px"
  tessera-edge: "24px"
  tessera-edge-lg: "32px"
components:
  button-primary:
    backgroundColor: "{colors.ochre}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "8px 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.ochre-hover}"
    textColor: "{colors.ink}"
  button-default:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.card-white}"
    typography: "{typography.body-small}"
    rounded: "{rounded.none}"
    padding: "0 20px"
    height: "44px"
  button-default-hover:
    backgroundColor: "{colors.deep-turquoise}"
    textColor: "{colors.card-white}"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.smalt-turquoise}"
    rounded: "{rounded.none}"
    padding: "0 20px"
    height: "44px"
  button-outline-hover:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.card-white}"
  button-on-field:
    backgroundColor: "transparent"
    textColor: "{colors.card-white}"
    rounded: "{rounded.none}"
    padding: "0 20px"
    height: "44px"
  button-on-field-hover:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.smalt-turquoise}"
  button-ghost-hover:
    backgroundColor: "{colors.pale-turquoise}"
    textColor: "{colors.ink}"
  input:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "44px"
  badge-field:
    backgroundColor: "{colors.pale-turquoise}"
    textColor: "{colors.deep-turquoise}"
    rounded: "{rounded.none}"
    padding: "4px 8px"
  programme-tile:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
    padding: "28px 24px 24px"
  programme-tile-unpublished:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
  mosaic-tile-field:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.card-white}"
    rounded: "{rounded.none}"
    padding: "32px"
  mosaic-tile-field-hover:
    backgroundColor: "{colors.deep-turquoise}"
  header-bar:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.field-mist}"
    height: "72px"
  footer:
    backgroundColor: "{colors.deep-turquoise}"
    textColor: "{colors.card-white}"
---

# Design System: SDU Admissions Portal

## Overview

**Creative North Star: "Almaty Mosaic"**

The portal is set like an Almaty modernist mosaic panel. Every section is a flat colour field laid on one 8px tessera grid, so programmes, dates, costs and application steps read as tiles of one monumental wall. Smalt turquoise carries whole bands; small square tesserae of glacier, ochre and terracotta set the edges where fields meet, and the same colours mark state. Headlines are monumental condensed capitals; everything else is a sturdy text sans built for Kazakh, Russian and English at equal quality.

The system is flat and square by conviction: no gradients, no soft shadows, no rounded cards. Depth comes from field against field (turquoise on cool white, deep turquoise on turquoise) and from a single flat 2px ink ring on floating overlays. Real SDU campus photography sits inside the mosaic frame, and the SDU emblem appears in one colour only. The official SDU navy and peach are deliberately not used: the portal must not read as a copy of sdu.edu.kz.

Density follows the visitor mode. Persuade (home, programmes) uses full-bleed bands and large tiles; Read (admissions planning guides) puts a turquoise title band over a reading column; Operate (account, application, staff) is quieter, with lighter containers and the display face in sentence case for staff headings. The world is light only: applicants use it on phones in daylight.

**Key Characteristics:**
- Smalt turquoise solid fields cover 30–60% of a public page.
- One 8px module; tesserae at 24px and 32px; tile gaps of 4–8px.
- Square corners everywhere on public surfaces.
- Fira Sans Extra Condensed 800 caps for display, Golos Text for text, both with full Kazakh Cyrillic.
- State as material: solid tiles are open or published, dashed outline tiles are closed or unpublished.
- One ochre action per band; ochre is never decoration.

## Colors

A cold turquoise wall with three warm-and-cool tesserae accents and ink-on-cool-white reading surfaces.

### Primary
- **Smalt Turquoise** (smalt-turquoise): the field colour. Header bar, hero band, guide title bands, the International band, the default working button, bachelor degree edges, focus ring on light surfaces. Carries 30–60% of a public page as solid fields.
- **Deep Turquoise** (deep-turquoise): the footer, the cost band, hover on turquoise buttons and tiles, completed stepper steps, inactive guide tabs, the mobile menu sheet.

### Secondary
- **Apricot Ochre** (ochre, hover ochre-hover): the primary action (Apply, Search, the band's one call to action), the active nav underline, PhD degree edges, "needs changes" state, footer column titles, and tesserae. Text on ochre is always ink.

### Tertiary
- **Glacier Turquoise** (glacier): tesserae, master degree edges, text selection, one path tile on the home page. Text on glacier is ink.
- **Terracotta** (terracotta): tesserae, the international path tile, the rejected stepper step. **Terracotta Text** (terracotta-text) is its darker, legible form for error and destructive text and "not published yet" notes.

### Neutral
- **Ink** (ink): all reading text; the 2px overlay ring; the heavy 2px rules that open lists and the date band.
- **Cool White** (cool-white): page background.
- **Card White** (card-white): tiles, inputs, the hero search tile, and text on fields.
- **Field Mist** (field-mist): secondary text and inactive nav on turquoise fields.
- **Pale Turquoise** (pale-turquoise), **Muted Surface** (muted-surface), **Accent Wash** (accent-wash): quiet badge boxes, ghost-button hover, list-row hover.
- **Slate Ink** (slate-ink): secondary text on light.
- **Hairline** (hairline): 1px dividers and borders. **Input Stroke** (input-stroke): 2px input and dashed-outline strokes.

### Named Rules
**The Field Rule.** Turquoise appears as solid fields, never as a tint wash or a gradient. Glacier, ochre and terracotta appear only as square tesserae and as state, never as a section background behind body text (the coloured path tiles are tesserae at tile scale, and they carry ink or white text only).

**The One Ochre Rule.** Ochre marks the one primary action in a band (Apply in the header, Search in the hero, one call to action per band). A second ochre button in the same band is a defect.

**The Not-SDU-Navy Rule.** The official SDU navy and peach are not used anywhere. The portal is SDU's admissions world, not a copy of sdu.edu.kz.

## Typography

**Display Font:** Fira Sans Extra Condensed 600/700/800 (with Arial Narrow, sans-serif)
**Body Font:** Golos Text 400/500/600/700 (with ui-sans-serif, system-ui)

**Character:** Monumental, narrow, all-caps display set tight like letters cast into a mosaic panel, paired with a plain, sturdy Cyrillic-native text sans. Both are self-hosted via @fontsource and were chosen for complete Kazakh Cyrillic coverage (ә ғ қ ң ө ұ ү һ і).

### Hierarchy
- **Display** (800, uppercase, clamp(3.25rem, 8.2vw, 6rem), line-height 0.86): the home hero headline only. Page h1s on programmes, programme detail and guides use the same face at clamp(2.5rem, 6–7vw, 5–5.5rem), line-height 0.88.
- **Headline** (800, uppercase, clamp(2.25rem, 4.4vw, 3.75rem), line-height 0.9): section h2s, max 16ch.
- **Title** (800, uppercase, 1.5rem to 1.75rem, line-height 1): programme tile titles; mosaic tile titles at clamp(1.375rem, 1.9vw, 2.125rem), line-height 0.9. Big facts and figures (dates, tuition) use the display face 700–800 with tabular numerals.
- **Body** (400, 1rem, line-height 1.55): running text; leads at 1.125rem, max 46–60ch.
- **Body small** (500–600, 0.9375rem): nav links, button text, tile meta lines, form labels.
- **Label** (display 700, 1.125rem, letter-spacing 0.04em, uppercase): large buttons and the header Apply; list and filter legends at 1.25rem without tracking.

### Named Rules
**The Cyrillic Air Rule.** In Kazakh and Russian, h1–h3 take line-height 1.04 so diacritics on capitals (Ң, Қ, Ұ, Ё, Й) clear the line above. This outranks the tight display leading.

**The Whole Word Rule.** Headings are never hyphenated. Sizes are set so whole words fit at 360, 1024 and 1440px in KK, RU and EN; overflow-wrap is a last-resort guard only.

**The Plain Heading Rule.** No eyebrow or kicker label above a heading, and no section numbers. A real tally (for example "2 published · 2 not published yet") may sit below a heading as content.

## Layout

One 8px tessera module governs everything. Three container widths: wide (84rem) for public bands, finders and the header and footer; content (72rem) for default pages and guide bodies; text (48rem) for forms and reading. Gutters step 16 / 24 / 32px at mobile / sm / lg. Public sections are full-bleed bands with 80px vertical padding, 112px on large screens.

Bands alternate field and light: turquoise hero band, cool-white paths, white date band between 2px ink rules, deep turquoise cost band, light schools, turquoise International band, light ask band, deep turquoise footer. Two-column bands put the heading and lead left (1fr) and the evidence right (1.6fr). Mosaic tiles sit in a 12-column grid with 8px gaps, one large tile spanning two rows.

Tessera edges mark where fields meet: two rows of `mosaicRow` tiles (a sparse upper row over a denser row touching the field) at 32px above the hero band, 24px under guide title bands and above the footer. Rows are seeded and deterministic, so the edge is identical on every render.

Filters are square tile groups that wrap on mobile and stack in a column beside the results from lg. The header is 64px tall on mobile and 72px from lg; full navigation shows from 1280px, a full-screen deep turquoise sheet below it.

## Elevation & Depth

The system is flat. There are no gradients and no soft shadows. Depth comes from field against field (white tile on turquoise band, deep turquoise against turquoise) and from heavy 2px ink rules. Only floating overlays get an edge, and that edge is a flat ring, not a shadow.

### Shadow Vocabulary
- **Overlay ring** (`box-shadow: 0 0 0 2px #121417`, token `--shadow-overlay`): the chat launcher and panel, the compare bar and sheets. Nothing in the page flow uses it.

### Named Rules
**The Flat Wall Rule.** No gradient and no blurred shadow on any surface, tile, button or image.

**The Globe Exception.** The shaded cobe `HeroGlobe` in the home International band is the one sanctioned departure from the Flat Wall Rule. It is kept because the team chose to preserve a teammate's component, and it is rendered as flat as cobe allows: diffuse 0, glow colour equal to the field so there is no halo. Nothing else may copy its shading.

## Shapes

Corners are square (0px) on every public surface: buttons, inputs, tiles, badges, tabs, overlays, tesserae. The quieter Operate areas may use a 2px corner on plain bordered containers; nothing rounder exists. Borders are 2px for interactive and stateful edges (inputs, outline buttons, filter tiles, dashed state outlines, hover outlines on tiles) and 1px hairlines for dividers.

State is a material change: a solid tile means open, published or done; a 2px dashed input-stroke outline tile on a transparent ground means closed, unpublished or not yet reached. The recurring silhouette is the square tessera: 10px status squares in badges, 8px degree bars on tile tops, 24–32px tiles at field edges, a 12px ochre square on the chat launcher's corner.

## Components

### Buttons
Square, solid and quick; the arrow is the only flourish.
- **Shape:** square corners (0px).
- **Primary (ochre):** ochre field, ink text, display label 700 caps with 0.04em tracking at 48px tall (large) or Golos 600 at 44px (default). One per band.
- **Default:** smalt turquoise field, white Golos 600 text, 44px tall, 20px side padding; hover deep turquoise.
- **Outline:** 2px turquoise border and text on transparent; hover fills turquoise with white text.
- **On field:** 2px white border and text on a turquoise field; hover fills white with turquoise text.
- **Ghost / Link:** ghost is ink text with a pale turquoise hover; link is turquoise text with a 2px underline that turns ochre on hover.
- **Hover / Focus:** 0.2s colour transitions; 1px press on active; a trailing arrow icon slides 3px right on hover. Focus is a 2px ring outline offset 2px (turquoise on light, white on fields). Disabled is 45% opacity.

### Chips (status badges)
- **Style:** a square box (4px 8px padding, 0.875rem semibold) holding a 10px tessera of colour plus the words.
- **State:** tones are neutral (an outlined tessera), field, glacier, ochre, terracotta and solid (turquoise box with an ochre tessera). Status is never colour alone: always tessera plus words.

### Cards / Containers
- **Programme tile:** three fixed lines. The full title in display caps (never truncated), then degree · language · code in small muted text (this line may truncate), then one deciding fact above a hairline: the local deadline, or tuition when the deadline is unpublished. A 6px degree bar sits on the top edge (bachelor turquoise, master glacier, PhD ochre). Published: white tile with a transparent 2px border that turns turquoise on hover. Unpublished: dashed 2px outline on transparent.
- **Mosaic tile:** a linked colour field (turquoise, glacier, ochre, terracotta or white) at least 224px tall with 24–32px padding, a display title, one line of purpose, and one hard fact with an arrow that slides on hover. Hover darkens the field.
- **Date tile:** a square turquoise tile holding the day number and month in display face; an unpublished date is a dashed outline tile with a dash and a terracotta "not published yet".
- **Background / Shadow:** card white or field colours; no shadow (see Elevation & Depth).

### Inputs / Fields
- **Style:** 44px tall, 2px input-stroke border, white ground, square corners; hover darkens the border to ink. Search fields on bands are 56px tall, joined flush to the ochre search button, with a turquoise search icon.
- **Focus:** border turns turquoise and a 2px ring outline sits 2px outside.
- **Error / Disabled:** aria-invalid turns the border terracotta text colour; disabled is 50% opacity.
- **Filters:** native radios inside 44px square tiles; checked is a solid turquoise tile with white semibold text, unchecked is a white tile with a hairline border that turns turquoise on hover.

### Navigation
- **Header:** a smalt turquoise bar with the white SDU lockup, a hairline divider and the "Admissions" label in display caps, four links in Golos 500 (field-mist, white when hovered or active, with a 4px ochre underline that scales in from the left on the active link), the language switcher, and the ochre Apply with an arrow.
- **Mobile:** below 1280px a square menu button opens a full-screen deep turquoise sheet with display-caps links (active in ochre), the Apply button, and a small tesserae cluster in the bottom corner.
- **Guide tabs:** square tiles on the turquoise band; active is white with turquoise text, inactive deep turquoise, hover ink.
- **Footer:** deep turquoise with a tessera edge, the white lockup and the tagline in display caps, ochre display-caps column titles.

### Application Stepper
Four equal square steps with 4px gaps: done is deep turquoise with a check, current is a solid tile (turquoise; ochre with ink text for changes requested; terracotta for not accepted) carrying the status word, upcoming is a dashed outline with its number. Only the current step names the status.

### Tesserae
A decorative, aria-hidden grid of square tiles in token colours (null cells are gaps), sized in multiples of 8px. Tiles set in once when their band enters the viewport: a short, scattered stagger (45ms steps in a loose order, never a sweep), 0.5s, expo-out (cubic-bezier(0.16, 1, 0.3, 1)), from 60% scale and transparent. Static under prefers-reduced-motion.

### Logo and Photography
The SDU emblem and lockup are SDU's own SVG paths in one colour: white on fields, ink on light (frontend/public/brand/). Photography is real SDU campus and student photography, credited in frontend/public/images/sdu/CREDITS.md, set square-cornered and framed by fields or a small tesserae cluster.

## Do's and Don'ts

### Do:
- **Do** lay public sections as full-bleed solid fields, with smalt turquoise covering 30–60% of the page.
- **Do** use one ochre action per band, with ink text.
- **Do** show every status as a tessera plus words; solid tile for open or published, dashed outline tile for closed or unpublished.
- **Do** keep programme tiles to three fixed lines with the degree colour as the top edge, and never truncate the title.
- **Do** give Kazakh and Russian headings line-height 1.04 and size headings so whole words fit at 360, 1024 and 1440px.
- **Do** use the flat 2px ink ring (`--shadow-overlay`) for floating overlays only.
- **Do** set the SDU logo in one colour: white on fields, ink on light.
- **Do** keep motion to the tesserae set-in, 0.2s colour transitions and the 3px arrow slide, all static under reduced motion.
- **Do** keep Operate areas quieter: plain hairline containers, staff headings in the display face in sentence case.

### Don't:
- **Don't** use gradients or soft shadows anywhere; the cobe HeroGlobe is the one sanctioned exception and nothing may copy its shading.
- **Don't** round corners on public surfaces.
- **Don't** put eyebrow or kicker labels above headings, or number sections.
- **Don't** use the official SDU navy or peach.
- **Don't** use glacier, ochre or terracotta as tint washes or as backgrounds behind body text.
- **Don't** hyphenate headings.
- **Don't** add a dark mode; the world is light only.
