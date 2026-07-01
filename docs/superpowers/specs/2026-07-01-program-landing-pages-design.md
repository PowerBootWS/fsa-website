# Design Spec: Program-Specific Landing Pages

**Date:** 2026-07-01
**Status:** Approved
**Scope:** fsa-website

---

## Problem

When Russ receives DMs on social media from people asking for study help, he currently sends them to the generic homepage and expects them to navigate to the enroll page. These visitors are frustrated operators looking for any help — not actively shopping for a paid course. The conversion path is too long and the copy is generic. Two dedicated landing pages will let Russ drop a direct link that does the persuasion work the DM conversation may not have finished.

---

## Goals

- One page per program: 3rd Class Complete and 2nd Class Complete
- Page must stand alone — persuasive enough even if the DM was brief
- Address the "why pay when free resources exist" objection directly on-page
- Include the fail-proof guarantee as a risk reversal
- Form locked to the page's program (no program picker)
- Fast on mobile (most traffic will be from DM links on phones)

---

## Pages

| Page | URL | Program | Price |
|------|-----|---------|-------|
| 3rd Class Complete | `/3rd-class-complete` | 3rd Class (3A1, 3A2, 3B1, 3B2) | $99/month (launch, was $149) |
| 2nd Class Complete | `/2nd-class-complete` | 2nd Class (2A1, 2A2, 2A3, 2B1, 2B2, 2B3) | $149/month (launch, was $199) |

Both pages share the same five-section layout and CSS. Class-specific copy is hard-coded per page.

---

## Page Structure

### Section 1 — Hero

Full-width hero that speaks to frustration first, product second. No product pitch in the headline.

**3rd Class headline:**
> You've Been Studying. The Exam Still Isn't Clicking.

**2nd Class headline:**
> Six Papers. One Shot at Each. Let's Make Them Count.

**Sub-headline (shared tone, class-specific details):**
> Most operators who struggle on the exam aren't lacking knowledge — they're lacking reps under exam conditions. Guided lessons get you ready. Practice exams get you through the door.

**CTA button:** "Get Started — $99/month →" (or $149 for 2nd Class). Anchors to the enrollment form below.

---

### Section 2 — Free-vs-paid reframe

Short prose block. Honest, not preachy. Names the real problem with free resources (no feedback loop, not exam-condition reps), then introduces FSA as the solution with a price anchor.

> There's no shortage of notes, textbooks, or scattered practice questions online. The problem is that the exam doesn't test your notes — it tests your ability to perform under pressure with no prompts. That takes repetition at scale, and it takes feedback that tells you *why* you got it wrong, not just that you did.
>
> FSA gives you adaptive practice exams for every paper in your program, an AI tutor available at 2am when you're on nights, and step-by-step calculation coaching that mirrors exactly how SOPEEC marks the paper. Less than $3.30 a day. [Less than $5 a day for 2nd Class.]

---

### Section 3 — What's included

Checklist mirroring the enroll.html style (orange checkmarks, Barlow font).

**3rd Class:**
- All four 3rd Class papers — 3A1, 3A2, 3B1, 3B2
- Adaptive practice exams that focus on your weak spots
- AI tutoring available anytime, including nights and weekends
- Step-by-step calculation coaching that mirrors how exams are marked
- Progress saved — pause and resume on any device
- Study at your own pace — no cohorts, no deadlines, no classroom

**2nd Class:**
- All six 2nd Class papers — 2A1, 2A2, 2A3, 2B1, 2B2, 2B3
- (same remaining bullets)

---

### Section 4 — The guarantee

Full-width callout block with strong visual treatment (border, distinct background). Personal voice from Russ.

> **If you fail, I've got you.**
>
> Bring me your exam result and I'll give you an extra month — on me. No questions asked. I'm confident enough in what this program does that I'm willing to put that behind it. And honestly? I don't expect to be paying out many of these.
>
> — Russ

How to claim: contact support@fullsteamahead.ca with the exam result. One claim per student.

---

### Section 5 — Enrollment form

Identical mechanics to `enroll.html`:
1. Name + email form
2. POST to `https://fsa-lead-capture.powerboot.workers.dev/checkout` with `{ firstName, lastName, email, affiliateCode? }`
3. On success, redirect to Stripe checkout link with `prefilled_email`
4. Refgrow affiliate attribution applied before redirect

**Differences from enroll.html:**
- No program picker UI (`<div class="program-picker">` omitted)
- Stripe URL hard-coded to the page's program (no switching logic)
- The `__fsaSelectedStripeUrl` function returns the fixed program URL
- Form heading updated to reference the specific class

**Stripe URLs:**
- 3rd Class: `https://buy.stripe.com/00w9AVgmY4d95VU1k11B602`
- 2nd Class: `https://buy.stripe.com/3cI14peeQ395ckie6N1B600`

---

## Design / Styling

- Inherits `styles-v2.css` — no new stylesheet needed
- Uses existing CSS variables: `--orange`, `--surface`, `--border`, `--text-primary`, `--gray-mid`
- Fonts: Barlow Condensed (headings) + Barlow (body), same as rest of site
- Guarantee block: uses `.papers-note`-style callout or a new `.guarantee-block` with a subtle border and background tint
- Layout: single-column on mobile, hero section uses full-width with centered content; form section uses the same two-column grid as enroll.html on desktop (copy left, form right)
- Scroll reveal: same `.reveal` + `IntersectionObserver` pattern as enroll.html
- GTM, Refgrow, and GHL external tracking scripts carried over from enroll.html

---

## Navigation

- Pages are not linked from the main nav (they are social DM landing pages, not discovery pages)
- Footer is included (standard)
- Nav is included but "Start Today →" button in the nav links to the page's own form anchor (`#enroll-form`)

---

## SEO / Sitemap

- `<meta name="robots" content="noindex">` on both pages — these are direct-link pages, not for organic search
- Not added to `sitemap.xml`
- Canonical omitted (noindex)

---

## Fail-Proof Guarantee — Operational Note

The guarantee is a real commitment: one free month per student upon submission of a failed exam result to support@fullsteamahead.ca. Applied manually. No automated redemption flow needed at this stage.

---

## Files to Create

| File | Notes |
|------|-------|
| `fsa-website/3rd-class-complete.html` | 3rd Class landing page |
| `fsa-website/2nd-class-complete.html` | 2nd Class landing page |

No new CSS file. No new JS file. No backend changes.
