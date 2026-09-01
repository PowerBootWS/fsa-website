# Articles IA Restructure: level-first navigation, generated hubs, level-inclusive content

**Status:** approved design, not yet implemented
**Date:** 2026-09-01
**Scope:** `fsa-website` only. No changes to `fsa-agent`, the LMS, or any product surface.

---

## 1. Why

Two problems, one root cause.

**The corpus was written when FSA sold one level.** 3rd Class launched 2026-06-15 and 4th Class
2026-07-23, but the articles still read as a 2nd Class site. Measured across the 48 live articles:

- **18** carry `2nd-class` / `second-class` / `2a1`-style tokens in the slug
- **11** say "2nd Class" in the title
- **9** discuss 2nd Class and never once mention 3rd or 4th

Several of those are advice that is identical at every level. `active-recall-power-engineering`
mentions 2nd Class eight times, 3rd Class zero times, and 4th Class once, despite active recall
being a study method that does not vary by ticket.

**Navigation does not help anyone find what applies to them.** Five of the eight Resources
dropdown items are individual articles wearing category names, and three of those five are
2nd-Class-branded. A 4th Class candidate opening Resources is offered three 2nd Class destinations
and no route to anything scoped to them. The hub behind it is 48 cards in six sections on one
continuous scroll, with a 14-card "Jobs & Getting Hired" pile that contains two certification
articles that are not about jobs at all.

### Why now, with evidence

Search Console, 90 days (2026-06-01 to 2026-08-29):

| Metric | Value |
|---|---|
| All 48 articles, total clicks | **13** |
| Total impressions | 1,595 |
| Mean position | **22.8** |
| Articles ranking better than position 10 | **4** |
| Articles as share of site search clicks | **2.3 %** (13 of 577) |

For contrast `/library` alone took 85 clicks and 1,221 impressions in the same window.

**There is effectively no ranking equity at risk.** Renaming, retitling, reorganising and
rescoping are close to free right now. This will stop being true if any of it starts working, so
this is the window.

### A third problem found while surveying

`scripts/articles_manifest.json` has drifted badly in both directions:

- **20 live articles are absent from it**, including all six SOPEEC paper guides, all six
  provincial jobs pages, and the 3rd Class exam guide
- **6 manifest entries have no article**: `absa-exam-alberta-requirements`,
  `power-engineering-salary-by-class`, `4th-class-power-engineering-salary`,
  `process-operator-to-power-engineer`, `stationary-engineer-vs-power-engineer`,
  `pan-global-vs-ai-adaptive-learning`

It describes 34 articles, the site has 48, and only 28 overlap. Article-level category strings
have drifted too: seven distinct values ("Study Strategy", "Careers", "Career & Jobs",
"Career & Industry" and others) where the manifest claims five.

This is the same drift disease the nav had before `partials/` was introduced, in a different file.
Any design that generates the hub from the manifest would be building on sand. This is the single
biggest reason for the architecture chosen below.

---

## 2. Decisions

| # | Decision |
|---|---|
| 1 | **Certification level is the primary axis**, journey stage secondary. Articles are tagged with the levels they serve and appear under each; they are never duplicated. |
| 2 | **Three level buckets: 4th, 3rd, 2nd.** Exactly what FSA sells. 5th and 1st Class are acknowledged in copy where the ladder is explained, but get no bucket and no hub. |
| 3 | **Rename only slugs that actively mislead**, each with a 301. Genuinely level-specific slugs (the six paper guides, salary-by-level, chief-engineer-roles) keep their names. |
| 4 | **Five journey stages** inside each level: Choosing your ticket, Studying for it, Sitting the exam, Career paths and pay, Finding work. |
| 5 | **The article file is the source of truth for its own metadata.** Hub pages and the Resources dropdown are generated from scanning `articles/` at build time. The manifest is demoted to a forward-looking content plan and stops being a rendering input. |

### Correction to an earlier estimate

During approach selection I estimated "roughly 8" slug renames. Close inspection of content
reduces that to **4**. The others turned out to be correctly scoped: `2nd-class-chief-engineer-roles`
is genuinely about what a 2nd Class ticket unlocks, `industries-2nd-class-power-engineers` and the
salary-by-level pages are genuinely level-specific, and the six SOPEEC paper guides describe actual
2nd Class papers. Renaming those would remove level signal that is correct. The four that survive
scrutiny are listed in section 6.

---

## 3. The five-stage taxonomy, with every article assigned

All 48 live articles are assigned below. The assignment was generated and validated
programmatically: no article is unassigned and no slug is invented.

Levels are the certification levels the article serves. **Action** is what happens to it:
`keep` (metadata only), `RETITLE` (title and H1 only), `REWRITE` (content made level-inclusive),
`RENAME` (slug change plus 301), or a combination.

### Choosing your ticket  (5)

| Slug | Levels | Action |
|---|---|---|
| `3rd-class-vs-2nd-class-power-engineering` | 3,2 | keep |
| `how-to-become-a-4th-class-power-engineer` | 4 | keep |
| `cost-of-2nd-class-power-engineering-exam-prep`<br>→ `cost-of-power-engineering-exam-prep` | 4,3,2 | RENAME+REWRITE |
| `how-long-to-prepare-2nd-class-exam`<br>→ `how-long-to-prepare-power-engineering-exam` | 4,3,2 | RENAME |
| `power-engineering-classes-canada` | 4,3,2 | keep |

### Studying for it  (8)

| Slug | Levels | Action |
|---|---|---|
| `active-recall-power-engineering` | 4,3,2 | REWRITE |
| `ai-tutoring-power-engineering-study` | 4,3,2 | REWRITE |
| `how-to-study-for-power-engineering-exams` | 4,3,2 | rewrite |
| `past-papers-2nd-class-power-engineering`<br>→ `past-papers-power-engineering` | 4,3,2 | RENAME+REWRITE |
| `power-engineering-practice-exam-comparison` | 4,3,2 | keep |
| `practice-questions-vs-full-course` | 4,3,2 | RETITLE |
| `spaced-repetition-power-engineering` | 4,3,2 | REWRITE |
| `study-schedule-power-engineering-job` | 4,3,2 | REWRITE |

### Sitting the exam  (16)

| Slug | Levels | Action |
|---|---|---|
| `2nd-class-power-engineering-exam-guide` | 2 | keep |
| `sopeec-2a1-exam-guide` | 2 | keep |
| `sopeec-2a2-exam-guide` | 2 | keep |
| `sopeec-2a3-exam-guide` | 2 | keep |
| `sopeec-2b1-exam-guide` | 2 | keep |
| `sopeec-2b2-exam-guide` | 2 | keep |
| `sopeec-2b3-exam-guide` | 2 | keep |
| `sopeec-2nd-class-exam-papers` | 2 | keep |
| `3rd-class-power-engineering-exam-guide` | 3 | keep |
| `shunt-generator-efficiency-calculation` | 3,2 | keep |
| `2nd-class-exam-day-what-to-expect`<br>→ `power-engineering-exam-day` | 4,3,2 | RENAME |
| `mental-prep-power-engineering-exam` | 4,3,2 | REWRITE |
| `multiple-choice-power-engineering-strategy` | 4,3,2 | REWRITE |
| `power-engineering-exam-stress` | 4,3,2 | REWRITE |
| `power-engineering-exam-time-management` | 4,3,2 | REWRITE |
| `sopeec-multiple-choice-traps` | 4,3,2 | keep |

### Career paths and pay  (7)

| Slug | Levels | Action |
|---|---|---|
| `2nd-class-chief-engineer-roles` | 2 | keep |
| `2nd-class-power-engineer-promotion-timeline` | 2 | keep |
| `2nd-class-power-engineering-certificate-careers` | 2 | keep |
| `2nd-class-power-engineering-salary-canada` | 2 | keep |
| `industries-2nd-class-power-engineers` | 2 | keep |
| `3rd-class-power-engineering-salary-canada` | 3 | keep |
| `power-engineer-salary-canada` | 4,3,2 | keep |

### Finding work  (12)

| Slug | Levels | Action |
|---|---|---|
| `how-to-find-power-engineering-jobs` | 4,3,2 | keep |
| `power-engineer-salary-negotiation` | 4,3,2 | keep |
| `power-engineering-interview-questions` | 4,3,2 | REWRITE |
| `power-engineering-job-application-follow-up` | 4,3,2 | keep |
| `power-engineering-jobs-alberta` | 4,3,2 | keep |
| `power-engineering-jobs-bc` | 4,3,2 | keep |
| `power-engineering-jobs-guide` | 4,3,2 | keep |
| `power-engineering-jobs-manitoba` | 4,3,2 | keep |
| `power-engineering-jobs-nova-scotia` | 4,3,2 | keep |
| `power-engineering-jobs-ontario` | 4,3,2 | keep |
| `power-engineering-jobs-saskatchewan` | 4,3,2 | keep |
| `power-engineering-resume-tips` | 4,3,2 | keep |

### What each level actually sees

Because articles are tagged rather than duplicated, a level view shows only what applies:

| Level view | Choosing | Studying | Exam | Career | Work | **Total** |
|---|---|---|---|---|---|---|
| 4th Class | 4 | 8 | 6 | **1** | 12 | 31 |
| 3rd Class | 4 | 8 | 8 | **2** | 12 | 34 |
| 2nd Class | 4 | 8 | 15 | 6 | 12 | 45 |

**This table is the gap analysis.** It shows the restructure alone does not fix the imbalance, it
makes it visible and measurable:

- **4th Class has one career article** (the generic Canada-wide salary page), no exam guide, and
  no paper guides for 4A or 4B
- **3rd Class has two career articles**, an exam guide, but no paper guides for 3A1/3A2/3B1/3B2
- **2nd Class holds 45 of 48**

Filling those gaps is Phase 4 and is deliberately out of scope for the restructure itself. The
restructure is what makes the gaps legible in the first place.

---

## 4. Architecture

### 4.1 Article metadata

Every article declares its own placement in its `<head>`:

```html
<meta name="fsa:levels" content="4,3,2">
<meta name="fsa:stage" content="studying">
```

`fsa:levels` is a comma-separated subset of `4,3,2`. `fsa:stage` is exactly one of
`choosing`, `studying`, `exam`, `career`, `work`.

The article file already owns its title, description, category label and breadcrumb. Adding these
two tags makes it own its placement too, which means the hub cannot disagree with reality.

### 4.2 Generation in `build_pages.py`

Extend the existing build step. It already stitches partials and writes `dist/`; it gains a
scan-and-generate pass:

1. Walk `articles/*/index.html`, read `fsa:levels`, `fsa:stage`, `<title>`, meta description and
   the H1
2. **Validate.** Any article missing either tag, or carrying an unknown stage or level, **fails
   the build**. This is the guardrail: metadata cannot silently go missing the way sitemap entries
   used to.
3. Emit four hub pages from one template: the full index plus three level views
4. Emit the Resources dropdown markup into `partials/nav.html`'s rendering

The card content (title, one-line description) comes from the article's own meta description, so
a card and its article cannot drift apart either.

### 4.3 URLs

| URL | What it is |
|---|---|
| `/articles/` | Full index, all 48, five stage sections, level badges on each card |
| `/articles/4th-class/` | 4th Class view, 31 articles |
| `/articles/3rd-class/` | 3rd Class view, 34 articles |
| `/articles/2nd-class/` | 2nd Class view, 45 articles |

Static and crawlable, not a JS toggle. Each level view gets a real URL that can earn its own
rankings and works with JavaScript off. All four go in `sitemap.xml`; the three level hubs get
priority `0.7`, the full index stays as it is.

### 4.4 The new Resources dropdown

Replaces the current eight items, five of which point at individual articles:

```
Resources
  Guides for 4th Class        -> /articles/4th-class/
  Guides for 3rd Class        -> /articles/3rd-class/
  Guides for 2nd Class        -> /articles/2nd-class/
  ---
  Free Book Library           -> /library
  Free Practice Exam          -> /free-practice-exam
  ---
  All Guides                  -> /articles/
```

Three level doors, two free tools, one escape hatch. No individual article is promoted into the
nav, which removes the "why is *that* article in the menu" problem entirely.

The mobile menu gets the same three level entries in place of its current `Exam Guide`,
`Study Methods` and `2nd Class Papers` article links.

### 4.5 Nav em dash fix

`partials/nav.html` uses em dashes in the three Programs dropdown items ("4th Class — $99/paper,
per year" and the 3rd and 2nd equivalents). The style guide bans em dashes everywhere, and a
member of a 25,000-person Facebook group has called them out as an AI tell. Because the nav is a
shared partial these render on all 70 pages. Replace with a comma:

```
4th Class, $99/paper per year
3rd Class, $99/month
2nd Class, $149/month
```

---

## 5. Content rewrite scope

**9 articles** are level-agnostic advice written as if 2nd Class were the only level. They get a
content pass making them explicitly inclusive of 4th, 3rd and 2nd:

`active-recall-power-engineering`, `spaced-repetition-power-engineering`,
`study-schedule-power-engineering-job`, `ai-tutoring-power-engineering-study`,
`multiple-choice-power-engineering-strategy`, `power-engineering-exam-time-management`,
`mental-prep-power-engineering-exam`, `power-engineering-exam-stress`,
`power-engineering-interview-questions`

**Rules for the pass:**

- Where a 2nd Class example is used, either generalise it or add the 4th and 3rd equivalent
- Do not simply find-and-replace "2nd Class" with "your exam". The specificity is the credibility;
  replace a specific example with a different specific example, never with vagueness
- Prep timelines differ by level and must be stated as differing, not averaged
- **No em dashes**, per the style guide
- **Do not imply written-answer format.** Every SOPEEC exam from 5th through 2nd Class is multiple
  choice only. No "show your work", no "structure your answer", no "partial credit"

**1 article** gets a title-only change: `practice-questions-vs-full-course` is currently
"Are Practice Questions Enough to Pass 2nd Class?" and becomes level-neutral. Slug stays.

---

## 6. Slug renames and redirects

Four slugs actively mislead: the URL says 2nd Class, the content serves every level.

| From | To |
|---|---|
| `2nd-class-exam-day-what-to-expect` | `power-engineering-exam-day` |
| `how-long-to-prepare-2nd-class-exam` | `how-long-to-prepare-power-engineering-exam` |
| `past-papers-2nd-class-power-engineering` | `past-papers-power-engineering` |
| `cost-of-2nd-class-power-engineering-exam-prep` | `cost-of-power-engineering-exam-prep` |

The first three already have level-neutral H1s; only the URL is wrong. The fourth is genuinely
2nd-Class-only content today and needs a rewrite covering all three price points alongside the
rename.

Each gets a 301 in `nginx.conf.template`, which already does permanent rewrites:

```nginx
location = /articles/2nd-class-exam-day-what-to-expect/ {
    return 301 /articles/power-engineering-exam-day/;
}
```

Every internal reference must move with them: in-body links across the corpus, `related_cards`
blocks, the manifest, and `sitemap.xml`. A grep for each old slug must return zero hits outside
the redirect block before the phase is considered done.

---

## 7. The manifest becomes a content plan

`articles_manifest.json` stops being a rendering input. It keeps one job: recording what is
planned and not yet written.

- Add a `status` field: `published` or `planned`
- The 6 orphan entries become `planned` and are the seed of the article backlog. They are real
  ideas, not junk: an ABSA requirements guide, salary-by-class, a 4th Class salary page, two
  career-transition pieces and a competitor comparison
- **Do not backfill the 20 missing entries.** The filesystem is now the source of truth for what
  exists; duplicating it into the manifest would recreate the drift this decision exists to kill
- Update the header comment and `wiki/projects/fsa-website.md` to state the new contract, so the
  next person does not "fix" the manifest back into a half-index

---

## 8. Phases

Each phase ships and deploys independently. None depends on a later one.

**Phase 1: the IA.** Add metadata tags to all 48 articles. Extend `build_pages.py` with the scan,
validate and generate pass. Emit the four hub pages. Rewrite the Resources dropdown and mobile
menu. Fix the nav em dashes. Add the three level hubs to `sitemap.xml`. *No article content
changes.* This alone solves the navigation complaint.

**Phase 2: the renames.** Four slug changes, four 301s, all internal references updated, sitemap
updated.

**Phase 3: level-inclusive rewrite.** The 9 content passes plus the 1 retitle, plus the
`cost-of-*` rewrite carried over from Phase 2.

**Phase 4: fill the gaps.** New articles the coverage matrix exposes, in priority order:
a 4th Class exam guide, 4A and 4B paper guides, 3A1/3A2/3B1/3B2 paper guides, a 4th Class careers
page. Each gets its own scoping; this phase is a backlog, not a single task.

---

## 9. Verification

Per phase, before deploy:

- `python3 scripts/build_pages.py` succeeds, and **fails** when a test article has a missing or
  bad `fsa:stage` (prove the guardrail works, do not assume it)
- Every article appears in exactly one stage on the full index, and article count on the index is
  48
- Each level hub's count matches the coverage matrix: 31 / 34 / 45
- Sitemap folder-vs-`<loc>` parity check passes, XML validates
- Every internal link resolves to a directory that exists
- Rendered at 390px and 1280px: no page-level horizontal overflow, no console errors
- Phase 2 only: each old slug returns 301 to the new one, verified on the live URL through
  Cloudflare, not localhost
- Post-deploy: full-zone Cloudflare purge exits `0`, not `2`

---

## 10. Non-goals

- No change to `fsa-agent`, the LMS, course content or the question banks
- No redesign of article page layout or typography. This is information architecture, not visual
  design
- No new articles in Phases 1 to 3
- No 5th or 1st Class hub. They are acknowledged in ladder copy only
- No change to `/library`, `/jobs` or `/free-practice-exam`, which are working and are the site's
  actual traffic

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Slug renames break inbound links shared in Facebook groups | 301s, not deletions. Verified live before the phase closes. |
| Generated hub loses hand-tuned card copy | Cards are generated from each article's own meta description, which is already hand-written per article. Spot-check the generated index against the current one before deploy. |
| The rewrite pass flattens specificity into vagueness | Explicit rule in section 5: replace a specific example with a different specific example. Style guide's "Specificity Is Credibility" applies. |
| Someone later "repairs" the manifest back into a half-index | Contract documented in the manifest header and in `wiki/projects/fsa-website.md`. |
| Level tags rot as articles are added | Build fails without them. Cannot rot silently. |

---

## 12. Open question for Russ

`wiki/entities/sopeec.md` documents the ladder as 4th (entry) to 1st and never mentions 5th Class,
while `wiki/style-guide.md` states every exam from 5th through 2nd is multiple choice. You have
confirmed 5th Class is real in some provinces, so the entity page is the one that is wrong.

**Which provinces have a 5th Class ticket?** I will add it to the ladder in `sopeec.md` either
way, but I would rather name the jurisdictions than write "in some provinces" if you know them.
Not blocking: nothing in Phases 1 to 3 depends on the answer.
