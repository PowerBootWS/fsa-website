# Free Practice Exam landing page

## Context

Companion to the already-merged (not yet deployed) `fsa-agent` migration of
the "Practice Preview" lead magnet from `fsachat.fullsteamahead.ca?mode=practice_preview`
(legacy client v1, still live) to `learn.fullsteamahead.ca/free-practice-exam`
(new client-v2 flow). This plan adds a dedicated marketing landing page for
the new flow and repoints the site's existing CTAs/links at it.

**Sequencing constraint, read before doing anything:** the new
`learn.fullsteamahead.ca/free-practice-exam` route will 404 (or fall
through to a default route) until `fsa-agent`'s merged branch is actually
deployed (Docker rebuild) — which has **not** happened yet. This plan
builds and commits the work to `fsa-website`'s git history exactly like
the other three repos in this effort, but **does not run the
`fsa-website-deploy` skill / actually publish to the live site**. Going
live (Docker rebuild, sitemap submission, Cloudflare purge) is a follow-up
step the human owner triggers once `fsa-agent`, `fsa-lead-capture`, and
`fsa-nurture` are all actually deployed and the new flow is verified
end-to-end. Say this explicitly in your task report so it isn't lost.

Existing live CTAs currently point to `https://fsachat.fullsteamahead.ca?mode=practice_preview`
(`library.html:527`, `library.html:616`) — copy there already says "Free
Practice Exam" (the naming is already correct in the marketing copy, only
the URL/backing flow needs to change). There is also one genuinely broken
link (`articles/sopeec-2nd-class-exam-papers/index.html:234`, pointing to
`https://learn.fullsteamahead.ca?mode=diagnostic` — a dead, unrelated
system, confirmed non-functional). The homepage currently has **no** CTA
to any practice-exam flow at all (checked, zero occurrences of `fsachat`/
`practice_preview` in `index.html`) — this plan adds one.

## Global Constraints

- **Reuse existing CSS components, don't invent new ones.** `.chapter-grid`/
  `.chapter-card` (styles-v2.css:895-929, in the "TEXTBOOK ACCORDION"
  section) is the right base for a paper-picker grid — already sized for
  many small clickable items. `.pillars`/`.pillar-card` (styles-v2.css:641-705)
  is the right base for the page's top-level pitch/intro section (2-4 large
  feature blocks), not the paper picker. `.practice-preview-band` (used
  in `library.html`'s existing CTA band) is a good reference for tone/copy
  but do not literally reuse that specific class for anything other than
  the existing CTA band it already styles.
- **Do not touch `.diagnostic-band`** (styles-v2.css:2437-2483) — unused,
  dead CSS from the old diagnostic tool, unrelated to this work, out of
  scope to clean up here.
- **No inline `<style>` block for reusable component styles** — component
  styles (the class/paper picker grid, CTA buttons) go in `styles-v2.css`
  as a new commented section (`/* ── FREE PRACTICE EXAM PAGE ── */`),
  following the file's existing section-header convention. Page-unique
  one-off styling (if any is truly needed beyond what's reusable) may go
  in an inline `<style>` block in the new page itself, matching the
  precedent set by `enroll.html`/`affiliate.html` — but prefer the shared
  stylesheet for anything that isn't truly one-off.
- **No shared nav/footer partial exists in this site** — every page
  copy-pastes the full `<nav>`/`.mobile-menu`/`<footer>` markup (47 files
  currently share it). **This plan does NOT attempt a site-wide nav rollout**
  — adding a "Free Practice Exam" link to the nav across all 47 files is a
  separate, larger consistency task explicitly out of scope here (the site
  already has known nav drift between pages, e.g. `library.html`'s mobile
  menu has a "Free Resources" link that `index.html`'s mobile menu lacks —
  this plan does not need to fix that either). The new landing page itself
  still needs a working nav/footer (copy `library.html`'s, since it's the
  most complete reference), but no other existing page's nav gets touched.
- **URL convention**: sitewide URLs are extension-less in `sitemap.xml`
  and internal links (`/library`, not `/library.html`) even though files
  on disk are `.html` (nginx rewrites). Use `/free-practice-exam` in every
  internal link and the sitemap entry; the file on disk is
  `free-practice-exam.html`.
- **CTA target URL format**: `https://learn.fullsteamahead.ca/free-practice-exam?class=<second|third>&paper=<code>`
  — paper codes are exactly `PAPERS_SECOND = ['2A1','2A2','2A3','2B1','2B2','2B3']`
  and `PAPERS_THIRD = ['3A1','3A2','3B1','3B2']` (matching `fsa-agent`'s
  `server/src/routes/preview.js` exports — hardcode these two arrays in
  the page's JS, this site has no shared JS module system to import from).
  Preserve any `?am_id=` affiliate query param already present on the
  landing page's own URL by appending it to the outbound CTA URL too (read
  it from `window.location.search`, forward it unchanged) — this is how
  affiliate attribution survives the click-through, matching the pattern
  `nav.js` already uses elsewhere on this site for affiliate cookie capture
  (check `nav.js` for the exact `am_id` handling convention before writing
  your own).

## Task 1 — new landing page

**Files:** `free-practice-exam.html` (new), `styles-v2.css` (append new
section only), `assets/ogimage-free-practice-exam.jpg` (new — see note
below).

Build `free-practice-exam.html` following `library.html`'s structure as
the closest reference (full `<head>` block with canonical/OG/Twitter tags
per its convention lines 1-30, full copy-pasted nav from `library.html`,
full copy-pasted footer from `library.html`).

**Page content, in order:**
1. Hero/intro section: headline + 2-3 sentence pitch. Reuse the existing
   `library.html` practice-preview-band copy as a starting point/tone
   reference (it already says "Pick any paper for your 2nd or 3rd Class
   certificate, take 25 or 50 questions, and get a chapter-by-chapter
   debrief with AI feedback" — adapt, don't necessarily copy verbatim,
   this is now the ONLY practice-exam CTA on the site so it can be more
   prominent/complete than the band was).
2. Class picker: two large buttons/cards, "2nd Class" / "3rd Class" —
   `.pillar-card`-based, 2-up.
3. Paper picker: revealed after class selection (or both grids present
   with one hidden via a class toggle — simple vanilla JS, no framework,
   matching this site's existing plain-JS convention, e.g. `nav.js`'s
   style). `.chapter-grid`/`.chapter-card`-based, one button per paper
   code, label each with the same human-readable names `client-v2/src/pages/LobbyPage.jsx`
   uses (e.g. "2A1: 1st Class Power Engineering" — check that file's exact
   mapping if available in this checkout, otherwise use a reasonable plain
   label like "Paper 2A1" if the source isn't accessible from this repo).
4. Single CTA per paper selection: clicking a paper button navigates (or
   a single "Start My Free Practice Exam" button appears once both class
   and paper are chosen) to
   `https://learn.fullsteamahead.ca/free-practice-exam?class=<second|third>&paper=<code>[&am_id=...]`.
5. Brief "how it works" / FAQ section (optional, keep it short — 2-3 items
   max, e.g. "How many questions?", "Do I need to pay?", "Can I do more
   than one paper?" — answer the last one honestly: yes, once each,
   verified by email).

**`<head>` requirements:**
- `<title>`: something like "Free Practice Exam – Power Engineering (2nd & 3rd Class) – Full Steam Ahead"
- Canonical: `https://fullsteamahead.ca/free-practice-exam.html` (match
  the pattern other pages use — check whether canonical tags use the
  `.html` extension or the clean URL; `library.html:9` uses `.html`, match
  that exact convention)
- Full OG block matching `library.html:20-30`'s pattern (`og:type`,
  `og:site_name`, `og:title`, `og:description`, `og:url`, `og:image`,
  `og:image:width`/`height`, `fb:app_id`, `twitter:card`, `twitter:image`)
- `og:image`/`twitter:image`: reference `https://fullsteamahead.ca/assets/ogimage-free-practice-exam.jpg`.
  **You do not need to generate a real image for this task** — if no image
  generation tool is available in your environment, either reuse
  `assets/ogimage-library.jpg` as a temporary placeholder (note this
  explicitly in your report as a follow-up) or check whether this repo's
  `fsa-image-gen` sibling project convention is reachable from here (it
  likely isn't, from this worktree) — a placeholder is acceptable, don't
  block on this.

**Verification:** open the file's HTML in a static syntax sense (no
linter required, just careful manual review — this is plain HTML/CSS/JS,
no build step), confirm the nav/footer match `library.html`'s markup
closely enough to look consistent, confirm the class/paper picker JS
correctly builds the CTA URL with `class`/`paper`/(optional)`am_id` query
params for all 10 paper codes across both classes, confirm no reference to
`.diagnostic-band` or the old `fsachat.*` domain appears anywhere in the
new file.

## Task 2 — repoint existing CTAs, fix broken link, add sitemap entry

**Files:** `library.html` (2 CTA link changes), `index.html` (add one new
CTA — homepage currently has none),
`articles/sopeec-2nd-class-exam-papers/index.html` (fix the one broken
link at line 234), `sitemap.xml` (add one new high-priority entry).

Depends on Task 1 existing first (these all link to the new page).

### `library.html`
Change both existing CTA hrefs (`library.html:527` and `library.html:616`)
from `https://fsachat.fullsteamahead.ca?mode=practice_preview` to
`/free-practice-exam` (the site's internal clean-URL convention — no
`https://fullsteamahead.ca` prefix needed for an internal same-site link,
check how other internal links on this page are written, e.g. the
`/library` links in the footer, and match that convention exactly). Leave
all surrounding copy/markup/classes untouched — this is a link-target-only
change in both places.

### `index.html`
Add a new CTA linking to `/free-practice-exam`. Since the homepage
currently has zero practice-exam CTAs, place it in a sensible existing
section — check `index.html:324` ("Practice Exams That Target Your Weak
Spots" outcome card) and `index.html:356` (descriptive paragraph) for the
most natural insertion point; a single button/link added near one of
those existing mentions is sufficient, do not build a whole new page
section for this. Match the site's existing button styling
(`.btn-primary`, used elsewhere) rather than inventing new button markup.

### `articles/sopeec-2nd-class-exam-papers/index.html:234`
Current broken text: `The diagnostic mode (available without a
subscription at <a href="https://learn.fullsteamahead.ca?mode=diagnostic">learn.fullsteamahead.ca</a>)
gives you a read on where you're sitting...`. Rewrite this sentence to
reference the new Free Practice Exam instead of the dead diagnostic mode
— e.g. "A free practice exam (no subscription required, at
[fullsteamahead.ca/free-practice-exam](/free-practice-exam)) gives you a
read on where you're sitting before you commit to a study plan." Keep the
surrounding sentence structure/tone consistent with the rest of the
article's voice — read a bit of surrounding context before editing.

### `sitemap.xml`
Add one new `<url>` entry for `/free-practice-exam`, following the exact
format of existing entries (see `sitemap.xml:5-10`'s homepage entry for
the format). Since this becomes "the primary funnel CTA" per this
project's stated priority, use `<priority>0.9</priority>` (just below the
homepage's `1.0`, above `library`'s `0.7`), `<changefreq>monthly</changefreq>`,
and today's date for `<lastmod>` (check today's actual date — don't
guess, use the system date if you have a way to check it, otherwise ask
in your report rather than fabricating one). Insert it near the top of
the file alongside the other highest-priority entries (homepage, etc.),
not buried in the alphabetical article list.

**Verification:** grep the whole repo (`grep -rn "fsachat.*practice_preview"`
and `grep -rn "mode=diagnostic"`) to confirm both are now gone from every
file this task was scoped to touch (library.html, sopeec article) — do
NOT touch the other files the earlier research found with prose-only
diagnostic mentions (`articles/ai-tutoring-power-engineering-study/index.html`,
`articles/past-papers-2nd-class-power-engineering/index.html`,
`articles/mental-prep-power-engineering-exam/index.html`,
`resources/power-engineering-exam-tips/index.html`) — those mention
"diagnostic" in passing prose with no link at all, rewriting them is a
larger content-editing task out of scope for this plan; only the one
file with an actual broken `<a href>` link is in scope. Confirm
`sitemap.xml` is still well-formed XML after your edit.

## Verification (whole plan)

- Do not run the `fsa-website-deploy` skill or any Docker rebuild — this
  plan's work stays committed-but-undeployed, matching the other three
  repos in this effort, until the human owner decides to coordinate a
  combined go-live.
- Confirm no reference to the old `fsachat.*`/`mode=practice_preview` URL
  remains in `library.html`.
- Confirm the new page's outbound CTA URLs are well-formed for all 10
  paper codes.
