# Jobs Page — Hero Expansion & Promo Banner

**Date:** 2026-05-09  
**Status:** Approved  

## Overview

Two additions to `jobs.html`:

1. **Hero expansion** — Replace the single-line subtitle with a paragraph and a three-stat row, adding SEO-meaningful copy and positioning context.
2. **Promo banner** — A compact horizontal banner placed between the hero and the search bar, promoting the 2nd Class exam prep program to job board visitors.

## Goals

- Increase word count in the hero section to improve SEO signal on a page that currently reads as thin content.
- Clearly communicate FSA's unique position: the only job board in Canada built exclusively for Power Engineers.
- Surface the exam prep program to a high-intent audience (engineers actively looking at job listings) without disrupting the job browsing experience.

---

## 1. Hero Section

### Current state

```
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

## 2. Promo Banner

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

## Files Changed

| File | Change |
|------|--------|
| `jobs.html` | Add hero paragraph, stat row, and promo banner markup |
| `styles-v2.css` | Add new CSS classes for stats row and promo banner |

No JavaScript changes beyond the two-line visibility toggle in `renderDetail()` and the corresponding restore in `fetchJobs()`.
