---
name: SDU Admissions Portal
description: Almaty Mosaic, refined. A calm institutional document in one turquoise hue, serif headings, hairline ledgers and one stepped mosaic signature.
colors:
  smalt-turquoise: "#0a6c74"
  deep-turquoise: "#074f55"
  field-tint: "#e3efee"
  field-mist: "#cdebe9"
  ochre: "#e3a33a"
  ochre-hover: "#d2912a"
  terracotta: "#c5532f"
  terracotta-text: "#b0432a"
  glacier: "#19a7a8"
  slate-ink: "#17222a"
  cool-white: "#f5f7f6"
  card-white: "#ffffff"
  pale-turquoise: "#e4eeed"
  muted-surface: "#e9efee"
  accent-wash: "#d6ebea"
  muted-text: "#4a5553"
  hairline: "#c9d4d2"
  input-stroke: "#7e908d"
typography:
  display:
    fontFamily: "Source Serif 4 Variable, Source Serif 4, Georgia, serif"
    fontSize: "clamp(2.75rem, 5vw, 4.5rem)"
    fontWeight: 500
    lineHeight: 1.04
    letterSpacing: "-0.01em"
    fontVariation: "opsz auto"
  headline-page:
    fontFamily: "Source Serif 4 Variable, Source Serif 4, Georgia, serif"
    fontSize: "clamp(2.25rem, 4vw, 3.5rem)"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  headline-band:
    fontFamily: "Source Serif 4 Variable, Source Serif 4, Georgia, serif"
    fontSize: "clamp(2.5rem, 4.5vw, 4rem)"
    fontWeight: 500
    lineHeight: 1.06
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Source Serif 4 Variable, Source Serif 4, Georgia, serif"
    fontSize: "clamp(1.875rem, 3vw, 2.75rem)"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Source Serif 4 Variable, Source Serif 4, Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 500
    lineHeight: 1.15
  title-large:
    fontFamily: "Source Serif 4 Variable, Source Serif 4, Georgia, serif"
    fontSize: "clamp(1.75rem, 2.6vw, 2.25rem)"
    fontWeight: 500
    lineHeight: 1.15
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
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.08em"
  label-action:
    fontFamily: "Fira Sans Extra Condensed, Arial Narrow, ui-sans-serif, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.06em"
  numeral:
    fontFamily: "Fira Sans Extra Condensed, Arial Narrow, ui-sans-serif, sans-serif"
    fontSize: "clamp(2.25rem, 4.4vw, 3.25rem)"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tnum"
rounded:
  none: "0px"
  operate: "2px"
spacing:
  module: "8px"
  tessera: "16px"
  tile-gap: "8px"
  gutter-sm: "16px"
  gutter-md: "24px"
  gutter-lg: "32px"
  band: "80px"
  band-lg: "112px"
components:
  button-primary:
    backgroundColor: "{colors.ochre}"
    textColor: "{colors.slate-ink}"
    typography: "{typography.label-action}"
    rounded: "{rounded.none}"
    padding: "8px 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.ochre-hover}"
    textColor: "{colors.slate-ink}"
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
    textColor: "{colors.slate-ink}"
  input:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.slate-ink}"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "44px"
  filter-option:
    backgroundColor: "transparent"
    textColor: "{colors.muted-text}"
    typography: "{typography.body-small}"
    height: "44px"
  filter-check-checked:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.card-white}"
    size: "18px"
  badge-field:
    backgroundColor: "{colors.pale-turquoise}"
    textColor: "{colors.deep-turquoise}"
    rounded: "{rounded.none}"
    padding: "4px 8px"
  program-card:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.slate-ink}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
    padding: "24px"
  mosaic-tile-field:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.card-white}"
    typography: "{typography.title-large}"
    rounded: "{rounded.none}"
    padding: "32px"
  mosaic-tile-field-hover:
    backgroundColor: "{colors.deep-turquoise}"
  mosaic-tile-card:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.slate-ink}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
    padding: "32px"
  date-tile:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.card-white}"
    size: "104px"
  date-tile-closed:
    backgroundColor: "transparent"
    textColor: "{colors.muted-text}"
    size: "104px"
  compare-toggle-field-selected:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.smalt-turquoise}"
    height: "48px"
  header-bar:
    backgroundColor: "{colors.smalt-turquoise}"
    textColor: "{colors.field-mist}"
    height: "72px"
  menu-panel:
    backgroundColor: "{colors.deep-turquoise}"
    textColor: "{colors.card-white}"
  phone-action-bar:
    backgroundColor: "{colors.deep-turquoise}"
    textColor: "{colors.card-white}"
    padding: "8px 16px"
  ruled-row-hover:
    backgroundColor: "{colors.pale-turquoise}"
    textColor: "{colors.slate-ink}"
    padding: "20px 8px"
  footer:
    backgroundColor: "{colors.deep-turquoise}"
    textColor: "{colors.card-white}"
---

# Design System: SDU Admissions Portal

## Overview

**Creative North Star: "Almaty Mosaic, refined"**

The portal reads as a calm institutional document that carries one Almaty-mosaic signature. Sections are white and cool-neutral pages, structured by sentence-case serif headings and hairline ledgers. Every page starts at the same left edge as the header logo. One turquoise field per group carries the main path; everything around it is quiet. Neutrals outnumber the brand colour by a wide margin, so the turquoise reads as SDU's voice and not as wallpaper.

The mosaic survives as a signature, not a wall: the real skyline of the Trans-Ili Alatau as seen from the SDU campus, laid in turquoise tesserae. It appears at most twice per page: where the hero band rises into the campus photo, along the bottom of each inner page's title band, and where the footer rises into the page, named there in a small caption. The system is flat and square by conviction, with no gradients, no soft shadows and no rounded cards. Depth comes from field against neutral and from a flat 2px ink ring on floating overlays. Real SDU photography carries the warmth on the home page and the hub, including inside the main path tile; each programme page carries its own credited subject photograph. The official SDU navy and peach are not used, so the portal does not read as a copy of sdu.edu.kz.

Density follows the visitor mode. Persuade (home, programmes) uses full-bleed bands, a mosaic of unequal tiles and ledgers. Read (the admissions hub, planning guides and information pages) puts a turquoise title band over ruled lists, split ledgers and reading columns. Operate (account, application, staff) is quieter, with plain hairline containers. The world is light only, because applicants use it on phones in daylight.

**Key Characteristics:**
- One brand hue: smalt turquoise and its deep shade on cool white, white and a light tint.
- Source Serif 4 headings in sentence case at weight 500; Golos Text for everything you read.
- Condensed caps only for short labels, numerals and the large action label.
- Square corners, 1px hairlines, ledgers opened by a 2px ink rule.
- The mosaic is one stepped 16px edge, at most twice per page.
- One ochre action: Apply (and Search where the page is a search).

## Colors

One cold turquoise hue and its deep shade on calm cool neutrals, with three reserved accents that each have exactly one job.

### Primary
- **Smalt Turquoise** (smalt-turquoise): the brand field. Header bar, hero band, guide title bands, the one main path tile per group, published date tiles, the default working button, checked filter squares, the focus ring on light surfaces, links.
- **Deep Turquoise** (deep-turquoise): the footer, the cost ledger band, the phone action bar, the Menu panel, hover on turquoise buttons and tiles, completed stepper steps, inactive guide tabs, the cap tiles of the hero signature.
- **Field Tint** (field-tint): the one quiet band colour, used for the International band.
- **Field Mist** (field-mist): secondary text, inactive nav and footer column titles on turquoise fields.

### Secondary
- **Apricot Ochre** (ochre, hover ochre-hover): the primary action only. That is the one shared Apply action (header, mobile sheet, programme page, compare, the phone action bar) and the hero and finder Search. Text on ochre is always slate ink.

### Tertiary
- **Terracotta** (terracotta) and **Terracotta Text** (terracotta-text): errors and destructive actions only; terracotta-text is the legible form for error text and invalid input borders.
- **Glacier** (glacier): text selection only, with slate ink text.

### Neutral
- **Slate Ink** (slate-ink): all reading text, the 2px rule that opens a ledger, the 2px overlay ring, the hero search input stroke.
- **Cool White** (cool-white): page background.
- **Card White** (card-white): cards, inputs, the hero search tile, the date band, and text on fields.
- **Pale Turquoise** (pale-turquoise), **Muted Surface** (muted-surface), **Accent Wash** (accent-wash): badge boxes, removable filter chips, ghost and ruled-row hover (pale turquoise at 60%).
- **Muted Text** (muted-text): secondary text on light, unpublished and closed deadlines, closed date tiles, compare rows that are the same for every programme, unchecked filter options.
- **Hairline** (hairline): every 1px divider and card border. **Input Stroke** (input-stroke): 2px input borders and unchecked filter squares.

### Named Rules
**The One Hue Rule.** Turquoise and deep turquoise are the only brand fields, set solid on cool white, white or field tint. No other hue fills a section, a tile or a decoration.

**The One Job Rule.** Ochre is only the primary action (the shared Apply action, and the hero and finder Search). Terracotta is only errors and destructive actions. Glacier is only selection. An ochre, terracotta or glacier tile, band or decoration is a defect. The one sanctioned use beyond that is application state: in `Badge` and `ApplicationStepper`, ochre marks "changes requested" and terracotta marks "not accepted", always as a small tile plus words, because there the colour carries meaning the applicant must act on.

**The White Marker Rule.** On turquoise, emphasis is white: the active nav underline is a 2px white bar, the active quick link is white and underlined, the selected Compare toggle on the programme band is a filled white button with turquoise text, and the globe marker is a white square. Ochre is not used to mark position or selection.

**The Not-SDU-Navy Rule.** The official SDU navy and peach are not used anywhere.

## Typography

**Display Font:** Source Serif 4 Variable with optical sizing (with Source Serif 4, Georgia, serif)
**Body Font:** Golos Text 400/500/600/700 (with ui-sans-serif, system-ui)
**Label/Numeral Font:** Fira Sans Extra Condensed 600/700 (with Arial Narrow, sans-serif)

**Character:** A sober text serif for headings, set in sentence case like a university prospectus, over a plain, sturdy Cyrillic-native sans. Condensed capitals survive only as a small label voice and in figures, where they read as cast numbers. All three faces are self-hosted via @fontsource and cover Kazakh Cyrillic (ә ғ қ ң ө ұ ү һ і).

### Hierarchy
- **Display** (500, clamp(3rem, 5.8vw, 5.25rem), line-height 1.02, max 17ch): the home hero h1 only, the page's one loud moment. Under it, "SDU in figures": four condensed numerals (clamp(2.25rem, 3.4vw, 3rem), 700) with label captions: programs, schools and languages of study counted live from the catalogue, and the founding year.
- **Headline, page** (500, clamp(2.25rem, 4vw, 3.5rem), line-height about 1.1): page h1s on programmes, programme detail, account and staff. On turquoise band pages (the hub, planning guides and information pages) the h1 is clamp(2.5rem, 4.5vw, 4rem), line-height 1.06, max 20ch.
- **Headline** (500, clamp(1.75rem, 2.6vw, 2.5rem), line-height 1.1, max 20ch): section h2s, including the programme page sections. Information pages open their split sections at clamp(1.75rem, 2.6vw, 2.25rem); sub-groups (degree groups in the finder, hub and notes sub-heads) at clamp(1.5rem, 2vw, 1.875rem), line-height 1.15.
- **Title** (500, 1.25 to 2.25rem, line-height 1.15 to 1.18): mosaic tile titles (1.25 to 1.5rem, or clamp(1.75rem, 2.6vw, 2.25rem) on the large main tile), finder row titles (1.25rem, 1.375rem from sm), ruled-row titles (1.375rem in the hub, 1.25rem for related programmes, 1.125rem in compare headers), the hero search label, the footer tagline (1.875rem, weight 400), mobile menu links (1.5rem).
- **Body** (400, 1rem, line-height 1.55): running text; leads at 1.125rem, 46 to 52ch.
- **Body small** (500 to 600, 0.9375rem): nav links, default button text, card meta lines, filter options, form labels.
- **Label** (Fira Sans Extra Condensed 600, 0.875rem, +0.08em, uppercase): the "Admissions" lockup label, filter legends, footer column titles, date month abbreviations, the "From" mark above a fee, tile and hub-row facts, the degree-group count, the word "Closed" beside a passed date, "or" between requirement alternatives.
- **Action label** (Fira Sans Extra Condensed 600, 0.9375rem, +0.06em, uppercase): large buttons and the header Apply.
- **Numeral** (Fira Sans Extra Condensed 700, tabular): date-tile day numbers (3rem), the cost ledger (clamp(2.25rem, 4.4vw, 3.25rem)), steps-list numbers (1.875rem, turquoise), school counts (1.5rem), stepper numbers (1.125rem).

### Named Rules
**The Sentence Case Rule.** Every heading is serif, sentence case, weight 500, letter-spacing −0.01em, line-height 1.04 to 1.15. No heading is set in capitals.

**The Small Caps Voice Rule.** Condensed caps appear only in the label utility, in numerals and in the large-button and Apply labels. Anything longer than three words is not a label.

**The Heading Order Rule.** A tile or card title is never larger than its own section heading.

**The Cyrillic Air Rule.** In Kazakh and Russian, h1 to h3 take line-height 1.16 so diacritics on capitals (Ң, Қ, Ұ, Ё, Й) clear the line above. This outranks the tight leading utilities.

**The Whole Word Rule.** Headings are never hyphenated and are balanced; sizes are set so whole words fit at 360, 1024 and 1440px in KK, RU and EN. overflow-wrap is a last-resort guard only.

**The Plain Heading Rule.** No eyebrow or kicker label above a heading, and no section numbers. A real count (for example the number of programs in a degree group) may sit below a heading as content.

**The Worded Range Rule.** A range is written in words, never with a dash: "19,000 to 41,500 ₸", "от 19 000 до 41 500 ₸". A large display figure shows the lowest value under a "From" mark, and the highest goes in the line below ("up to 41,500 ₸ per ECTS credit"). Official compound names that contain a dash (UNT subject pairs) keep it.

**The Full Sentence Rule.** Interface copy is written in short full sentences. No semicolons, and a ledger row has a title and one plain detail line, not a sentence packed with colons. Levels that have no published dates share one row (title "Master's and PhD", detail "Dates not published yet"), not a comma list.

## Layout

One 8px module governs spacing. Every page, band, header and footer sits in the same 84rem frame with the header's gutters (16, 24 and 32px at mobile, sm and lg), so every page starts at the logo's left edge. Reading widths are limits on the content inside the frame, left-aligned and never centred: reading and form columns stop at 48rem, default pages at 72rem, finders, tables, the hub and the information pages use the full frame. Public sections are full-bleed bands with 80px vertical padding, 96 to 112px on large screens.

On the home page the bands run: campus photo with the turquoise hero band rising into it, cool-white paths, the white date ledger between 2px ink rules, the deep turquoise cost ledger, light schools beside a student photo, the field-tint International band with the globe, the light ask band, then the deep turquoise footer. Two-column bands put the heading and lead left (1fr) and the evidence right (1.6fr); the hub and the information pages (apply, deadlines, application status, contact) use the same split from lg, with a 64px gap. Path tiles sit in a 12-column grid with 8px gaps on the home page only: one large field tile spans six columns and two rows, quiet card tiles fill the rest. The hub is not tiles: it is a campus photograph beside ruled lists of tools and information pages.

Structure comes from lists, not boxes. Ledgers (dates, costs, schools, questions, documents, requirements, related programmes, steps, statuses, deadlines) open with a 2px ink rule and divide rows with 1px hairlines. A linked ruled row hangs its hover padding outside the text edge from sm (8px negative margin, 8px padding), so row text stays aligned with the headings above while the pale hover box extends past it. Band edges are clean cuts except the two signature edges.

The finder stacks filters in a column beside the results from lg; below lg they sit behind a single hairline toggle. Results are ruled rows, not boxes: the serif title, then degree · language · code · local deadline on one quiet line, and a borderless "+ Compare" text toggle; the whole row is the link. Two columns of rows from lg. Without a degree filter the results are grouped by degree under a 2px ink sub-head, and the local deadline most of the group shares is stated once there instead of on each row. The header is 64px tall on mobile and 72px from lg; it is one row: the lockup, the three main sections (from 1280px), search, language, Apply and a Menu button at every width. Everything else lives in the Menu panel (Purdue's pattern). The footer follows the same idea: the lockup, tagline and the admissions office's address, phone and e-mail on the left, then three columns (Explore, Apply, Information for) of four plain links each. Footer links take an underline only on hover and keyboard focus.

Below 640px a fixed deep turquoise action bar holds the ochre Apply and an outlined Ask button at the bottom of the screen, in place of a floating chat button, and the compare tray stacks directly above it as a full-width strip. From 640px the chat launcher and compare bar float in the corners.

## Elevation & Depth

The system is flat. There are no gradients and no soft shadows. Depth comes from a turquoise field against neutral pages, a white search tile overlapping the photo, and the 2px ink rule over a ledger. Only floating overlays get an edge, and that edge is a flat ring, not a shadow.

### Shadow Vocabulary
- **Overlay ring** (`box-shadow: 0 0 0 2px var(--ink)`, token `--shadow-overlay`): the chat launcher, chat bar and panel, the floating compare bar from 640px, sheets. Nothing in the page flow uses it. The phone action bar and the phone compare strip are docked, not floating, and take a top hairline instead of the ring.

### Named Rules
**The Flat Page Rule.** No gradient and no blurred shadow on any surface, tile, button or image.

**The Globe Exception.** The shaded cobe HeroGlobe in the home International band is the one sanctioned departure from the Flat Page Rule, kept as Daniyar's component. It is rendered as flat as cobe allows: diffuse 0, dark 0, glow equal to the field tint so there is no halo, and a white marker. It opens centred on Almaty and sways ±0.5 rad around it instead of spinning, so Almaty never turns away. Nothing else may copy its shading.

## Shapes

Corners are square (0px) on every public surface: buttons, inputs, tiles, cards, badges, tabs, overlays, bars, tesserae, date tiles. The quieter Operate areas may use a 2px corner on plain bordered containers; nothing rounder exists. Borders are 1px hairlines for cards, tiles and dividers, and 2px for inputs, outline buttons and the ink rule that opens a ledger.

The recurring silhouette is the square: 16px tesserae in the signature edge, 18px filter check squares, 10px status squares in badges, square date tiles, the 8px white globe marker.

## Components

### Buttons
Square, solid and quick; the arrow is the only flourish.
- **Shape:** square corners (0px).
- **Primary (ochre):** ochre with slate-ink text, action label (condensed 600 caps, 0.9375rem, +0.06em) at 48px or more. Only two jobs: the hero and finder Search, and Apply. Apply is one shared component (`ApplyAction`): it links to the online application when that feature is on, otherwise to the official portal with an outward arrow. It appears in the header, the mobile sheet, the programme band beside Compare, under the compare table and in the phone action bar; never a second ochre button in the same view.
- **Default:** turquoise with white Golos 600 text, 44px tall, 20px side padding; hover deep turquoise.
- **Outline:** 2px turquoise border and text on transparent; hover fills turquoise with white text.
- **On field:** 2px white border and text on turquoise; hover fills white with turquoise text.
- **Ghost / Link:** ghost is ink text with a pale turquoise hover; link is turquoise text with a 2px underline.
- **Large size:** any variant at the large size takes the action label and a 48px minimum height.
- **Compare toggle:** small; outline when not selected, default turquoise when selected on light. On the turquoise programme band it is the on-field button, 48px beside Apply, and its selected state is a filled white button with turquoise text, never ochre.
- **Hover / Focus:** 0.2s colour transitions, a 1px press on active, a trailing arrow that slides 3px right on hover. Focus is a 2px ring outline offset 2px (turquoise on light, white on fields). Disabled is 45% opacity.

### Chips (status badges and filter chips)
- **Badge:** a square box (4px 8px, 0.875rem semibold) holding a 10px colour square plus the words; status is never colour alone.
- **Filter chip:** a pale turquoise box with deep turquoise semibold text and a close icon, 36px tall; hover accent wash.

### Cards / Containers
- **Programme card:** white, 1px hairline that turns turquoise on hover, 20 to 24px padding, three fixed lines. The full serif title (never truncated), then degree · language · code in small muted text (this line may truncate), then the local deadline above a hairline. An upcoming deadline is semibold; a closed or unpublished one is stated in muted words ("25 August 2026, closed", "not published yet"). When a degree group already states the shared deadline, the card drops it and keeps only the Compare toggle. No colour stripe and no dashed state.
- **Mosaic tile (home page only):** a linked tile at least 192px tall with 24 to 32px padding, a serif title, one line of purpose and one fact set as a label with a sliding arrow. Two tones only. `field` is turquoise with white text, the one main path per group, hover deep turquoise, and may carry a real SDU photo bled across its top. `card` is white with a 1px hairline that turns turquoise on hover, muted purpose text and a turquoise fact.
- **Date tile:** a square in the home date ledger, in date order. Upcoming: turquoise, white condensed day number and label month. Closed: the same square outlined in a 1px hairline with muted figures, and the word "Closed" as a label beside the date. Unpublished levels get no tile; they collapse into one muted line of words. When every published date has passed, the ledger says in a semibold line that the cycle is over.
- **Ruled row:** a linked row in a ledger: serif or semibold title, one muted line, optional label fact, and a trailing turquoise arrow that slides 3px. Hover is pale turquoise at 60%, hanging 8px outside the text edge from sm. Used in the hub, the information pages, related programmes, schools and questions.
- **Steps list:** a ledger whose rows open with a turquoise condensed numeral (1.875rem) in a 2.5rem column, then a semibold title and a muted line; linked steps take the ruled-row hover and arrow. Used only for the real application sequence on /apply.
- **Deadline states:** every deadline is one of upcoming, closed or unpublished, judged on the calendar day in Almaty (the deadline day itself is still open). Closed and not published are words, never badges: in tables "Closed" is a label in ink and "Not published" is small muted text.
- **Background / Shadow:** card white, cool white, field tint or turquoise fields; no shadow (see Elevation & Depth).

### Inputs / Fields
- **Style:** 44px tall, 2px input-stroke border, white ground, square corners; hover darkens the border to ink. The hero search is 56px with a 2px ink border; the finder search is 56px, borderless on the turquoise band and joined flush to the ochre Search. Both carry a turquoise search icon.
- **Focus:** the border turns turquoise and a 2px ring outline sits 2px outside.
- **Error / Disabled:** aria-invalid turns the border terracotta-text; disabled is 50% opacity.
- **Filters:** a hairline list under a label legend. Each option is a 44px row with an 18px square check indicator: unchecked is white with an input-stroke border and muted text; checked is a turquoise square with a white tick, and the option text is set at 600 in ink. Hover turns the text turquoise. Native radios underneath.

### Navigation
- **Header:** a turquoise bar with the white SDU lockup, a hairline divider and the "Admissions" label, four links in Golos 500 (field mist, white when hovered or active, with a 2px white underline that scales in from the left on the active link), a 40px search icon button (sm and up) that opens the finder with the cursor in its search box, the language switcher and the ochre Apply with an arrow.
- **Menu panel (every width):** an outlined Menu button (icon, plus the word from lg) opens a full-screen deep turquoise panel in the 84rem frame: the three main sections as serif links (1.5rem, 1.875rem from lg) on hairlines, the active one underlined in white; then Apply, Search and Ask; then three labelled groups of plain rows on faint white hairlines: Applying to SDU (how to apply, deadlines, status, cost and aid, contact), Plan your admission (the tools, compare, questions) and Information for (school leavers, international, master's, PhD, parents). No strip above the header and no Ask in the bar: the chat launcher covers it.
- **Breadcrumb and on-page bar (programme page):** on the turquoise band, a field-mist semibold trail (Programmes / degree / title, the title hidden below sm) above the title, and below it an "On this page" row of underlined field-mist links to documents, requirements, next steps and related programmes.
- **Guide tabs:** square tiles on the turquoise band; active is white with turquoise text, inactive deep turquoise, hover ink.
- **Footer:** deep turquoise rising into the page through the Alatau edge, with the caption "The Trans-Ili Alatau as seen from the SDU campus" at the right. Then the white lockup with a serif tagline ("Founded in 1996", 1.875rem, weight 400) above the admissions office's address, phone and e-mail, and three columns of four plain links (Explore, Apply, Information for). Label column titles in field mist; links take an underline only on hover and focus.

### Application Stepper
Four equal square steps with 4px gaps and condensed numerals. Done is deep turquoise with a check; current is a solid tile carrying the status word; only the current step names the status.

### Mosaic Signature
The one decorative motif, and the portal's signature: the Alatau line. `alatau.ts` holds the real skyline of the Trans-Ili Alatau seen from the campus (the highest horizon angle for each bearing from 100° to 260°, computed from SRTM elevation data), and `ridgeSteps` lays a window of it in 8px tesserae, scaled to the part a laptop shows and snapped to whole tiles, each column a cap tile on a body that joins the band below. Left to right is east to west, as you see the range facing it from the campus. The hero band rises into the photo with ten rows (deep cap on field body) centred on the highest stretch (163°), so phones keep the summit; the search tile sits over it on desktop. Inner title bands end in a still, nine-row silhouette of the deeper turquoise, each page at its own bearing, so moving through the site walks along the range. The footer rises into the page with six rows (field cap on deep body). The grout line is a faint 1px inset (5% white at 8px). It is aria-hidden and monochrome turquoise: no snowcaps, no sun, no highlights.

### Logo and Photography
The SDU emblem and lockup are SDU's own SVG paths in one colour: white on fields, ink on light. Photography is set square-cornered. Real SDU campus and student photography, credited in frontend/public/images/sdu/CREDITS.md, carries the full-bleed hero, the main path tile (the big blue SDU letters in the main hall), the sunlit library entrance beside the schools ledger, the campus photo in the hub and the summer campus beside the login form. Photos show the campus itself, not posed students; the interior views are frames from SDU's official campus tour video. Each programme page has its own unique Unsplash subject photograph on the band (not an SDU photograph, so never presented as campus), credited to the photographer in a small field-mist caption below it; sources are in frontend/public/images/programs/CREDITS.md.

### Compare
A table in the full frame: each column header is the serif programme title with degree · code beneath. Rows that are the same for every programme are greyed to muted text (with a screen-reader note), and differing values are semibold ink, so the differences carry the weight. One shared Apply sits under the table.

## Motion

Researched against Purdue, Stanford, Yale and Fondation Beyeler (21.11.2026). One authored moment, quiet support, no bounce (`--ease-out-expo` = cubic-bezier(0.16, 1, 0.3, 1)).

- **Signature (the focal moment):** on the home page, the first time the Alatau edge enters view, its tiles are laid column by column from the left: each tile rises 6px from scale 0.6 with opacity, 280ms, delay `min(column × 12ms, 700ms)`. It then settles into the static brand edge. On every other page the footer edge is drawn already settled, with no laying. On fine pointers, tiles within three columns of the cursor over the hero catch the light (`brightness(1.32)`, 150ms in, 400ms out); they never move.
- **Hero photo:** settles once from scale 1.05 to 1 over 1.4s.
- **Hero entrance:** the headline, the figures and the search tile rise 24px and fade in once as the page opens (800ms, starting at 80, 200 and 300ms).
- **Photos:** the student photo beside the schools and the campus photo in the hub open from the bottom edge as they enter view (clip-path, 1.1s) while the image settles from 1.05 to 1.
- **Finder results:** program rows rise in 40ms apart, capped at 200ms; only cards new to the list animate, so filtering never replays the whole grid.
- **Compare bar:** slides up into place (360ms) when the first program is added.
- **Scroll reveals:** section headings and lists (`data-reveal`, `data-reveal-list`) rise 24px and fade in over 600ms once, at 12% in view; list items arrive 70ms apart, capped at 350ms. Only lists stagger.
- **Figures:** only the school counts count up once in view (750ms, ease-out cubic); screen readers get the final number. Tuition figures are static.
- **Globe:** the HeroGlobe sways ±0.5 rad around Almaty (a slow sine), never a full spin; dragging moves the centre of the sway.
- **Hover and feedback:** cards lift 4px over 200ms and their border turns turquoise; photos inside tiles zoom to 1.04 over 500ms; arrows slide 3px; the active nav underline grows from the left; buttons press 1px.
- **Overlays and routes:** the mobile menu panel enters over 320ms and its links follow 40ms apart; route changes cross-fade over 150ms.
- **Never:** bounce or overshoot curves, hover scales of 1.1 or more, autoplaying carousels, parallax stacks, cursor followers, infinite ambient loops.
- **Reduced motion:** everything renders in its final state; the 150ms route fade and colour transitions remain.

## Do's and Don'ts

### Do:
- **Do** keep turquoise and deep turquoise as the only brand fields, on cool white, white and the field tint.
- **Do** reserve ochre for the shared Apply action and the hero and finder Search, terracotta for errors and destructive actions, glacier for selection.
- **Do** start every page in the 84rem header frame and limit reading widths left-aligned inside it.
- **Do** set headings in Source Serif 4, sentence case, weight 500, letter-spacing −0.01em, and keep tile titles smaller than their section heading.
- **Do** use the label utility (condensed 600, 0.875rem, +0.08em, caps) for labels of three words or fewer, and condensed tabular figures for numerals.
- **Do** keep the mosaic tile grid to the home page, with one turquoise `field` main path per group, optionally with a real SDU photo across its top; the rest are white `card` tiles. Elsewhere use ruled rows.
- **Do** derive every deadline state from the Almaty calendar day (upcoming, closed, unpublished), state closed and unpublished deadlines in words, and say so plainly when the whole cycle is over.
- **Do** build structure from ledgers: a 2px ink rule over 1px hairline rows, with linked-row hover hanging outside the text edge.
- **Do** use the flat 2px ink ring (`--shadow-overlay`) for floating overlays only.
- **Do** give Kazakh and Russian headings line-height 1.16.
- **Do** keep motion to the set below; every spatial movement is gated on `prefers-reduced-motion: no-preference`, and hidden states only apply under `html.motion-ready`, so content never disappears without scripts.

### Don't:
- **Don't** use the mosaic signature more than twice per page, or as random, multicoloured edges or sticker clusters.
- **Don't** make glacier, ochre or terracotta tiles, bands or decorations.
- **Don't** set headings in capitals or in the condensed face.
- **Don't** add colour stripes or dashed outlines to cards to show state, or show "Closed" and "Not published" as badges.
- **Don't** add a second ochre button to a view, or use ochre for a selected state on turquoise.
- **Don't** float a chat button over content on phones; use the bottom action bar.
- **Don't** use gradients or soft shadows; the cobe HeroGlobe is the one sanctioned exception and nothing may copy its shading.
- **Don't** round corners on public surfaces.
- **Don't** put eyebrow or kicker labels above headings, or number sections.
- **Don't** use the official SDU navy or peach.
- **Don't** add a dark mode; the world is light only.
