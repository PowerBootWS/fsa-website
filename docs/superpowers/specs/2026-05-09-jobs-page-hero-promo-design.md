# Jobs Page — Hero Expansion, Promo Banner & Homepage Jobs Callout

**Date:** 2026-05-09  
**Status:** Approved  

## Overview

Four additions across two files:

1. **Title & meta description** — Replace the thin `<title>` and `<meta name="description">` on `jobs.html` with SEO-optimised versions targeting Power Engineering job search intent.
2. **Hero expansion** — Replace the single-line subtitle with a paragraph and a three-stat row, adding SEO-meaningful copy and positioning context.
3. **Promo banner** — A compact horizontal banner placed between the hero and the search bar, promoting the 2nd Class exam prep program to job board visitors.
4. **Homepage jobs callout** — A narrow, visually distinct strip on `index.html` placed immediately after the trust bar, directing visitors who arrive looking for the job board.

## Goals

- Improve SEO on `jobs.html` via a strong title tag, meta description, and increased body word count.
- Clearly communicate FSA's unique position: the only job board in Canada built exclusively for Power Engineers.
- Surface the exam prep program to a high-intent audience (engineers actively looking at job listings) without disrupting the job browsing experience.
- Capture visitors who land on the homepage looking for the job board and redirect them immediately — keeping the jobs board as a growth lever for the broader brand.

---

## 1. Title Tag & Meta Description (`jobs.html`)

### Current state

```html
<title>Power Engineering Jobs — Full Steam Ahead</title>
<meta name="description" content="Browse active Power Engineering job opportunities across Canada. Filter by class level and location.">
```

### New state

**Title tag (57 characters):**
```
Power Engineering Jobs in Canada | Full Steam Ahead
```

**Meta description (≤155 characters):**
```
Browse active Power Engineering job listings across Canada — every class, every province. Updated every 12 hours. The only board built exclusively for Power Engineers.
```

The title leads with the primary keyword phrase, adds geographic scope, and ends with the brand. The meta description reinforces uniqueness, freshness (12-hour updates), and breadth — all meaningful differentiators for a searcher scanning results.

---

## 2. Hero Section

### Current state

```html
<div class="section-label">Career Board</div>
<h1>Power Engineering Jobs</h1>
<p class="jobs-hero-sub">Active opportunities for ticketed Power Engineers across Canada. Updated daily.</p>
```

### New state

Replace the single `<p class="jobs-hero-sub">` with:

**Paragraph:**
> The only job board in Canada built exclusively for Power Engineers — every class, every province. Listings are pulled from active postings across the country every 12 hours, and each role includes an AI-generated summary so you can assess the opportunity before digging into the full posting.

**Stat row (three chips separated by vertical rules):**

| Stat | Label |
|------|-------|
| Every 12h | Updated |
| All Classes | 5th → 1st |
| Canada-Wide | Coverage |

### Markup pattern

```html
<p class="jobs-hero-sub">...</p>
<div class="jobs-hero-stats">
  <div class="jobs-hero-stat">
    <span class="jobs-hero-stat-value">Every 12h</span>
    <span class="jobs-hero-stat-label">Updated</span>
  </div>
  <div class="jobs-hero-stat-divider"></div>
  <div class="jobs-hero-stat">
    <span class="jobs-hero-stat-value">All Classes</span>
    <span class="jobs-hero-stat-label">5th → 1st</span>
  </div>
  <div class="jobs-hero-stat-divider"></div>
  <div class="jobs-hero-stat">
    <span class="jobs-hero-stat-value">Canada-Wide</span>
    <span class="jobs-hero-stat-label">Coverage</span>
  </div>
</div>
```

### CSS additions

- `.jobs-hero-stats` — flex row, gap, margin-top
- `.jobs-hero-stat` — flex column, text-align
- `.jobs-hero-stat-value` — orange, Barlow Condensed, ~1.1rem, font-weight 700
- `.jobs-hero-stat-label` — gray-mid, uppercase, letter-spaced, ~0.55rem
- `.jobs-hero-stat-divider` — 1px wide, `var(--plate-edge)` background, self-stretch
- Responsive: hide dividers and switch to `flex-wrap` on small screens

---

## 3. Promo Banner

### Placement

Inside `.jobs-wrap`, immediately before `.jobs-search-bar`. It is always visible (not filtered out or hidden when a job detail is shown — the detail view already hides `.jobs-search-bar` and `#jobs-filters`, but the promo should be hidden in that view too for consistency).

### Copy

- **Eyebrow label:** `Advance your career`
- **Headline:** `Unlock higher-paying roles with a 2nd Class ticket`
- **Subline:** `Full Steam Ahead offers structured exam prep to get you there.`
- **CTA button:** `Learn More →` — links to `/enroll.html`

### Visual style

Horizontal banner with:
- Background: `var(--plate)` (`#1C2333`)
- Border: `1px solid var(--plate-edge)`, `border-left: 3px solid var(--orange)`
- Border-radius: 6px
- Layout: text block on the left, CTA button on the right (flex, space-between)
- CTA button: ghost style — transparent background, `1px solid var(--orange)` border, orange text

This is visually distinct from job cards (which have no left accent border) and from filter buttons, but stays within the site's design language.

### Markup pattern

```html
<div class="jobs-promo-banner">
  <div class="jobs-promo-text">
    <span class="jobs-promo-eyebrow">Advance your career</span>
    <strong class="jobs-promo-headline">Unlock higher-paying roles with a 2nd Class ticket</strong>
    <span class="jobs-promo-sub">Full Steam Ahead offers structured exam prep to get you there.</span>
  </div>
  <a href="/enroll.html" class="jobs-promo-cta">Learn More →</a>
</div>
```

### CSS additions

- `.jobs-promo-banner` — flex, space-between, align-center, gap, padding, background, border, border-left accent, border-radius, margin-bottom
- `.jobs-promo-text` — flex column, gap
- `.jobs-promo-eyebrow` — orange, uppercase, letter-spaced, ~0.55rem
- `.jobs-promo-headline` — white, ~0.9rem, font-weight 600
- `.jobs-promo-sub` — gray-mid, ~0.65rem
- `.jobs-promo-cta` — ghost button: transparent bg, orange border, orange text, padding, border-radius, white-space nowrap, flex-shrink 0
- Responsive: stack vertically on small screens, CTA becomes full-width

### Visibility in detail view

The `renderDetail()` function already hides `.jobs-search-bar` and `#jobs-filters`. Add `.jobs-promo-banner` to that hide/show logic so it disappears when viewing a single job and reappears when returning to the list.

---

---

## 4. Homepage Jobs Callout (`index.html`)

### Placement

A narrow strip inserted in `index.html` immediately after the `.trust-bar` div and before the `#who-for` section. This position catches visitors as they begin to scroll — just below the fold on most screens — without interrupting the primary exam prep conversion flow.

### Purpose

Visitors who arrive on the homepage already knowing about the FSA job board (via word of mouth, social, or brand recall) should get an immediate, low-friction redirect. The callout is not a feature pitch — it's a wayfinding strip. One sentence, one link.

### Copy

- **Label:** `Job Board`
- **Text:** `Looking for Power Engineering jobs in Canada?`
- **CTA:** `Browse the Job Board →` — links to `/jobs.html`

### Visual style

A full-width strip that sits between the trust bar and the Who It's For section. It should feel like a clearly different element from both — not a section, not a card — more like a pinned notice:

- Background: `var(--plate)` — slightly lighter than the page body, creates a visible band
- Border-top and border-bottom: `1px solid var(--plate-edge)`
- Single row: label chip on the left, sentence text in the centre-left, CTA link on the right
- No heavy padding — this should be compact (~50–60px tall), not a full section
- CTA link: orange text, no button chrome, arrow suffix — `Browse the Job Board →`
- Responsive: stack label + text above CTA on small screens

### Markup pattern

```html
<!-- Jobs callout strip -->
<div class="jobs-callout-strip">
  <span class="jobs-callout-label">Job Board</span>
  <span class="jobs-callout-text">Looking for Power Engineering jobs in Canada?</span>
  <a href="/jobs.html" class="jobs-callout-link">Browse the Job Board →</a>
</div>
```

### CSS additions (in `styles-v2.css`)

- `.jobs-callout-strip` — flex, align-center, gap, padding (0.85rem 3rem), background `var(--plate)`, border-top/bottom `1px solid var(--plate-edge)`
- `.jobs-callout-label` — small orange pill: background `rgba(232,114,12,0.12)`, border `1px solid rgba(232,114,12,0.3)`, color orange, font-size ~0.65rem, uppercase, letter-spaced, padding, border-radius, white-space nowrap, flex-shrink 0
- `.jobs-callout-text` — flex 1, color `var(--gray-light)`, font-size ~0.9rem
- `.jobs-callout-link` — color `var(--orange)`, font-weight 600, font-size ~0.9rem, white-space nowrap, flex-shrink 0, no underline by default, underline on hover
- Responsive (≤600px): wrap to two rows, label + text on row 1, link on row 2

---

---

## 5. OG Image for `jobs.html`

### Status: Manual asset — to be created separately

The existing `og-image.jpg` is a photo-composite designed for the exam prep homepage. `jobs.html` currently inherits it. A dedicated OG image should be created to match the style and drop in when ready — only a one-line `<meta>` change is needed once the file exists.

### Target file

`/assets/og-image-jobs.jpg` — 1200×630px, JPEG

### Design brief (matches existing OG image style)

**Layout:** Two-zone horizontal split, same as the homepage OG.

- **Left half:** Industrial/workplace photo — a plant control room, a boiler room, or a hard-hatted engineer reviewing equipment. Dark, moody, professional. The existing image uses warm-lit blueprints and exam papers; this should swap that for a plant operations scene.
- **Right half:** Dark navy blueprint-grid background (`#0D1117` to `#141A24`). Text stack:
  - Line 1 (white, condensed bold, large): `POWER ENGINEERING`
  - Line 2 (orange `#E8720C`, condensed bold, large): `JOBS`
  - Line 3 (white, condensed, medium): `CANADA`
- **Bottom-right icon strip** (same as homepage — 3–4 orange outline icons on dark pill background):
  - Suggested icons: hard hat, clipboard/posting, map pin (Canada), certificate/ticket
- **Bottom-left:** FSA logo (same position as homepage OG)

**Typography:** Barlow Condensed, uppercase, bold — matching the homepage OG weight and style.

**Tone:** Professional, industrial, authoritative — "this is where Power Engineers go for jobs."

### Wire-in step (once asset is ready)

In `jobs.html`, update the two OG image meta tags:

```html
<meta property="og:image" content="https://fullsteamahead.ca/assets/og-image-jobs.jpg">
<meta name="twitter:image" content="https://fullsteamahead.ca/assets/og-image-jobs.jpg">
```

This change is not part of the current implementation — it is blocked on the asset being created. The rest of the implementation proceeds without it.

---

## Files Changed

| File | Change |
|------|--------|
| `jobs.html` | Update `<title>`, `<meta name="description">`, add hero paragraph, stat row, and promo banner markup |
| `index.html` | Add `.jobs-callout-strip` immediately after `.trust-bar` |
| `styles-v2.css` | Add CSS for stats row, promo banner, and jobs callout strip |
| `assets/og-image-jobs.jpg` | New OG image — manual asset, created separately |

No JavaScript changes beyond the two-line visibility toggle in `renderDetail()` and the corresponding restore in `fetchJobs()`.
