# Articles IA Restructure Implementation Plan (Phases 1 and 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganise the 48-article corpus around certification level as the primary axis, with hub pages and level views generated from each article's own metadata at build time, so the hub can never drift from what actually exists.

**Architecture:** Each article declares `fsa:levels` and `fsa:stage` meta tags in its own `<head>`. `scripts/build_pages.py` gains a scan-and-validate pass that fails the build if any article is missing or malforms those tags, then generates four hub pages (full index plus one per level) from a new `partials/article-hub.html` template. The hand-maintained `articles/index.html` is deleted and replaced by generated output. `articles_manifest.json` is demoted to a content plan and stops being a rendering input.

**Tech Stack:** Python 3.11 (stdlib only, no new dependencies), pytest 9.0.3 (already available, not currently used by this repo), nginx (config template), Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-01-articles-ia-restructure-design.md`

## Scope of this plan

This plan covers **Phase 1 (the IA) and Phase 2 (the slug renames)** from the spec. Those two phases are code and configuration and produce working, testable software.

**Phase 3 (level-inclusive rewrite of 9 articles) and Phase 4 (gap-fill articles) are deliberately excluded.** They are content authoring, not software: each article needs individual editorial judgement against the style guide, and wrapping prose edits in a TDD task cycle would be theatre. They get their own plans once Phase 1 ships and we can see the level views.

## Global Constraints

Copied verbatim from the spec and the FSA style guide. Every task's requirements implicitly include this section.

- **No em dashes anywhere.** Use a comma, a period, a plain hyphen, or rewrite. This is a hard rule: a member of a 25,000-person Facebook group publicly called out FSA content for em dash use as an AI tell.
- **No new runtime dependencies.** `build_pages.py` is stdlib-only and runs inside a `python:3.11-slim` Docker build stage with no pip install step. Adding an import that is not in the standard library will break the container build.
- **Levels are exactly `4`, `3`, `2`** as strings. Never `fourth`, never `4th`, never integers. Note this differs from the database, where `subscriptions.class_code` is `second | third | fourth_a | fourth_b`. These metadata values are site-only and do not need to match.
- **Stages are exactly** `choosing`, `studying`, `exam`, `career`, `work`.
- **Never hand-edit a `<nav>` or `<footer>` block into a source page.** Edit `partials/` once.
- **Never hardcode a price.** Use `data-price="plan.field"` with the literal as a no-JS fallback, per `pricing.js`.
- **Every article gets its own `<url>` block in `sitemap.xml`.** So does every new hub page.
- **Do not run `git add -A`.** Stage named files only.
- **Do not deploy without the user saying so.** Every task ends at a commit; deployment is a separate explicit instruction.

## File Structure

| File | Responsibility |
|---|---|
| `scripts/build_pages.py` | Modified. Gains `Article`, `scan_articles()`, `render_article_hub()`, and hub generation inside `build()`. |
| `scripts/test_build_pages.py` | **Create.** First test file in this repo. Covers scanning, validation and hub rendering against fixtures, never against the real `articles/` tree. |
| `scripts/add_article_metadata.py` | **Create.** One-off migration that inserts the two meta tags into all 48 articles from a mapping table. Kept in the repo as the record of what was assigned. |
| `partials/article-hub.html` | **Create.** Full page template for the four hub pages. Placeholders `{{TITLE}}`, `{{DESCRIPTION}}`, `{{CANONICAL}}`, `{{H1}}`, `{{INTRO}}`, `{{LEVEL_NAV}}`, `{{SECTIONS}}`. |
| `partials/nav.html` | Modified. Resources dropdown rewritten to three level links; Programs dropdown em dashes removed; mobile menu updated. |
| `articles/index.html` | **Deleted.** Replaced by generated output. |
| `articles/*/index.html` | Modified. Two meta tags added to each of the 48. |
| `nginx.conf.template` | Modified. Four 301 redirect blocks (Phase 2). |
| `sitemap.xml` | Modified. Three level hub entries; four renamed article locs (Phase 2). |
| `scripts/articles_manifest.json` | Modified. `status` field added; header comment rewritten to state it is no longer a rendering input. |

---

## Task 1: Article scanning and validation

**Files:**
- Modify: `scripts/build_pages.py` (add constants and two functions after the `QUOTED_FAMILY_RE` block, around line 108)
- Test: `scripts/test_build_pages.py` (create)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `LEVELS: list[str]`, `LEVEL_LABELS: dict[str,str]`, `LEVEL_SLUGS: dict[str,str]`, `STAGES: list[tuple[str,str]]`, `STAGE_KEYS: set[str]`
  - `@dataclass Article` with fields `slug: str`, `title: str`, `description: str`, `levels: list[str]`, `stage: str`
  - `parse_article(slug: str, html: str) -> Article`. Raises `ValueError` on bad or missing metadata
  - `scan_articles(articles_dir: pathlib.Path) -> list[Article]`. Returns articles sorted by slug, raises `SystemExit` listing every problem found

- [ ] **Step 1: Write the failing test**

Create `scripts/test_build_pages.py`:

```python
"""Tests for scripts/build_pages.py.

First test file in this repo. Run with:
    python3 -m pytest scripts/test_build_pages.py -v
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_pages as bp


def article_html(levels="4,3,2", stage="studying", title="A Test Article",
                 description="A test description.", include_levels=True,
                 include_stage=True):
    """Minimal article HTML with the pieces the scanner reads."""
    meta = ""
    if include_levels:
        meta += f'  <meta name="fsa:levels" content="{levels}">\n'
    if include_stage:
        meta += f'  <meta name="fsa:stage" content="{stage}">\n'
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        f'  <meta name="description" content="{description}">\n'
        f"{meta}"
        "</head>\n<body>\n"
        f"  <h1>{title}</h1>\n"
        "</body>\n</html>\n"
    )


def test_parse_article_reads_all_fields():
    art = bp.parse_article("my-slug", article_html())
    assert art.slug == "my-slug"
    assert art.title == "A Test Article"
    assert art.description == "A test description."
    assert art.levels == ["4", "3", "2"]
    assert art.stage == "studying"


def test_parse_article_preserves_level_order_as_declared():
    art = bp.parse_article("s", article_html(levels="2"))
    assert art.levels == ["2"]


def test_parse_article_tolerates_whitespace_in_levels():
    art = bp.parse_article("s", article_html(levels="4, 3 ,2"))
    assert art.levels == ["4", "3", "2"]


def test_parse_article_unescapes_html_entities_in_title():
    html = article_html(title="Boilers &amp; Pumps")
    assert bp.parse_article("s", html).title == "Boilers & Pumps"


def test_parse_article_rejects_missing_levels():
    with pytest.raises(ValueError, match="fsa:levels"):
        bp.parse_article("s", article_html(include_levels=False))


def test_parse_article_rejects_missing_stage():
    with pytest.raises(ValueError, match="fsa:stage"):
        bp.parse_article("s", article_html(include_stage=False))


def test_parse_article_rejects_unknown_stage():
    with pytest.raises(ValueError, match="nonsense"):
        bp.parse_article("s", article_html(stage="nonsense"))


def test_parse_article_rejects_unknown_level():
    with pytest.raises(ValueError, match="5"):
        bp.parse_article("s", article_html(levels="5,4"))


def test_parse_article_rejects_empty_levels():
    with pytest.raises(ValueError, match="fsa:levels"):
        bp.parse_article("s", article_html(levels=""))


def test_scan_articles_finds_all_and_sorts_by_slug(tmp_path):
    for slug in ("zebra", "alpha", "middle"):
        d = tmp_path / slug
        d.mkdir()
        (d / "index.html").write_text(article_html(title=slug))
    arts = bp.scan_articles(tmp_path)
    assert [a.slug for a in arts] == ["alpha", "middle", "zebra"]


def test_scan_articles_skips_underscore_and_dot_dirs(tmp_path):
    for slug in ("real", "_template", ".impeccable"):
        d = tmp_path / slug
        d.mkdir()
        (d / "index.html").write_text(article_html())
    assert [a.slug for a in bp.scan_articles(tmp_path)] == ["real"]


def test_scan_articles_ignores_loose_files(tmp_path):
    (tmp_path / "articles.css").write_text("body{}")
    d = tmp_path / "real"
    d.mkdir()
    (d / "index.html").write_text(article_html())
    assert [a.slug for a in bp.scan_articles(tmp_path)] == ["real"]


def test_scan_articles_reports_every_bad_article_not_just_the_first(tmp_path):
    for slug in ("bad-one", "bad-two"):
        d = tmp_path / slug
        d.mkdir()
        (d / "index.html").write_text(article_html(include_stage=False))
    good = tmp_path / "good"
    good.mkdir()
    (good / "index.html").write_text(article_html())
    with pytest.raises(SystemExit) as exc:
        bp.scan_articles(tmp_path)
    msg = str(exc.value)
    assert "bad-one" in msg
    assert "bad-two" in msg
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest scripts/test_build_pages.py -v`
Expected: every test FAILS with `AttributeError: module 'build_pages' has no attribute 'parse_article'`

- [ ] **Step 3: Write the implementation**

In `scripts/build_pages.py`, add `import html as html_mod` and `from dataclasses import dataclass` to the imports at the top, then insert this block immediately after the `QUOTED_FAMILY_RE = ...` line:

```python
# ── Article metadata (added 2026-09-01, articles IA restructure) ──
#
# Each article declares which certification levels it serves and which journey
# stage it belongs to, in its own <head>:
#
#     <meta name="fsa:levels" content="4,3,2">
#     <meta name="fsa:stage" content="studying">
#
# The hub pages are generated from these, so an article cannot be missing from
# the hub and a card cannot drift from its article. A missing or malformed tag
# FAILS THE BUILD -- that is the point. The articles manifest used to be the
# index and had drifted to describing 34 articles against 48 live; the fix is
# to have one source of truth, not two that must agree.

LEVELS = ["4", "3", "2"]
LEVEL_LABELS = {"4": "4th Class", "3": "3rd Class", "2": "2nd Class"}
LEVEL_SLUGS = {"4": "4th-class", "3": "3rd-class", "2": "2nd-class"}
STAGES = [
    ("choosing", "Choosing your ticket"),
    ("studying", "Studying for it"),
    ("exam", "Sitting the exam"),
    ("career", "Career paths and pay"),
    ("work", "Finding work"),
]
STAGE_KEYS = {key for key, _ in STAGES}

META_LEVELS_RE = re.compile(r'<meta\s+name="fsa:levels"\s+content="([^"]*)"\s*/?>')
META_STAGE_RE = re.compile(r'<meta\s+name="fsa:stage"\s+content="([^"]*)"\s*/?>')
META_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"\s*/?>')
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)


@dataclass
class Article:
    slug: str
    title: str
    description: str
    levels: list[str]
    stage: str


def _text(raw: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", raw)).strip()


def parse_article(slug: str, html: str) -> Article:
    """Read one article's metadata. Raises ValueError on anything wrong."""
    m = META_LEVELS_RE.search(html)
    if not m or not m.group(1).strip():
        raise ValueError(f"{slug}: missing or empty <meta name=\"fsa:levels\">")
    levels = [v.strip() for v in m.group(1).split(",") if v.strip()]
    for lv in levels:
        if lv not in LEVEL_LABELS:
            raise ValueError(
                f"{slug}: fsa:levels contains '{lv}', expected some of {','.join(LEVELS)}"
            )

    m = META_STAGE_RE.search(html)
    if not m or not m.group(1).strip():
        raise ValueError(f"{slug}: missing or empty <meta name=\"fsa:stage\">")
    stage = m.group(1).strip()
    if stage not in STAGE_KEYS:
        raise ValueError(
            f"{slug}: fsa:stage is '{stage}', expected one of "
            + ", ".join(sorted(STAGE_KEYS))
        )

    m = H1_RE.search(html)
    title = _text(m.group(1)) if m else slug
    m = META_DESC_RE.search(html)
    description = html_mod.unescape(m.group(1)).strip() if m else ""

    return Article(slug=slug, title=title, description=description,
                   levels=levels, stage=stage)


def scan_articles(articles_dir: pathlib.Path) -> list[Article]:
    """Scan articles/ for article directories. Reports ALL problems at once."""
    articles: list[Article] = []
    errors: list[str] = []
    for child in sorted(articles_dir.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        index = child / "index.html"
        if not index.exists():
            errors.append(f"{child.name}: has no index.html")
            continue
        try:
            articles.append(parse_article(child.name, index.read_text()))
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        raise SystemExit(
            "Article metadata check failed:\n  "
            + "\n  ".join(errors)
            + "\n\nEvery article needs <meta name=\"fsa:levels\" content=\"...\"> and "
            "<meta name=\"fsa:stage\" content=\"...\"> in its <head>. "
            "See docs/superpowers/specs/2026-09-01-articles-ia-restructure-design.md"
        )
    return articles
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest scripts/test_build_pages.py -v`
Expected: 13 passed

- [ ] **Step 5: Verify the existing build is unaffected**

Run: `python3 scripts/build_pages.py`
Expected: `Built /home/debian/fsa-website/dist: 70 HTML pages stitched, 12 files/dirs copied through`

Nothing calls `scan_articles` yet, so the build output must be byte-identical to before.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_pages.py scripts/test_build_pages.py
git commit -m "feat(build): scan and validate article level/stage metadata

Adds parse_article() and scan_articles() to build_pages.py plus the repo's
first test file. Not yet wired into build(); the articles do not carry the
tags yet. Task 2 adds them."
```

---

## Task 2: Add the metadata tags to all 48 articles

**Files:**
- Create: `scripts/add_article_metadata.py`
- Modify: all 48 `articles/*/index.html`

**Interfaces:**
- Consumes: `bp.scan_articles`, `bp.LEVEL_LABELS`, `bp.STAGE_KEYS` from Task 1.
- Produces: every article in `articles/` carries valid `fsa:levels` and `fsa:stage`, so `scan_articles(ROOT/"articles")` returns 48 articles.

The assignment below is the spec's section 3 table. It was derived by reading each article, not by keyword matching. Do not re-derive it.

- [ ] **Step 1: Write the migration script**

Create `scripts/add_article_metadata.py`:

```python
#!/usr/bin/env python3
"""One-off migration: insert fsa:levels and fsa:stage into every article.

Kept in the repo as the record of what was assigned and why, and so the
assignment can be re-applied if an article head is ever rebuilt from the
template. Safe to re-run: it replaces existing tags rather than duplicating.

Assignment source: docs/superpowers/specs/2026-09-01-articles-ia-restructure-design.md

Usage:
    python3 scripts/add_article_metadata.py [--check]

--check reports what would change and exits non-zero if anything would, so
it can be used as a drift check without writing.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent

# slug -> (stage, levels)
ASSIGNMENT = {
    # Choosing your ticket
    "power-engineering-classes-canada": ("choosing", "4,3,2"),
    "how-to-become-a-4th-class-power-engineer": ("choosing", "4"),
    "3rd-class-vs-2nd-class-power-engineering": ("choosing", "3,2"),
    "cost-of-2nd-class-power-engineering-exam-prep": ("choosing", "4,3,2"),
    "how-long-to-prepare-2nd-class-exam": ("choosing", "4,3,2"),
    # Studying for it
    "how-to-study-for-power-engineering-exams": ("studying", "4,3,2"),
    "active-recall-power-engineering": ("studying", "4,3,2"),
    "spaced-repetition-power-engineering": ("studying", "4,3,2"),
    "study-schedule-power-engineering-job": ("studying", "4,3,2"),
    "ai-tutoring-power-engineering-study": ("studying", "4,3,2"),
    "past-papers-2nd-class-power-engineering": ("studying", "4,3,2"),
    "power-engineering-practice-exam-comparison": ("studying", "4,3,2"),
    "practice-questions-vs-full-course": ("studying", "4,3,2"),
    # Sitting the exam
    "2nd-class-power-engineering-exam-guide": ("exam", "2"),
    "3rd-class-power-engineering-exam-guide": ("exam", "3"),
    "multiple-choice-power-engineering-strategy": ("exam", "4,3,2"),
    "sopeec-multiple-choice-traps": ("exam", "4,3,2"),
    "shunt-generator-efficiency-calculation": ("exam", "3,2"),
    "power-engineering-exam-time-management": ("exam", "4,3,2"),
    "mental-prep-power-engineering-exam": ("exam", "4,3,2"),
    "power-engineering-exam-stress": ("exam", "4,3,2"),
    "2nd-class-exam-day-what-to-expect": ("exam", "4,3,2"),
    "sopeec-2nd-class-exam-papers": ("exam", "2"),
    "sopeec-2a1-exam-guide": ("exam", "2"),
    "sopeec-2a2-exam-guide": ("exam", "2"),
    "sopeec-2a3-exam-guide": ("exam", "2"),
    "sopeec-2b1-exam-guide": ("exam", "2"),
    "sopeec-2b2-exam-guide": ("exam", "2"),
    "sopeec-2b3-exam-guide": ("exam", "2"),
    # Career paths and pay
    "2nd-class-power-engineering-certificate-careers": ("career", "2"),
    "2nd-class-chief-engineer-roles": ("career", "2"),
    "2nd-class-power-engineering-salary-canada": ("career", "2"),
    "3rd-class-power-engineering-salary-canada": ("career", "3"),
    "2nd-class-power-engineer-promotion-timeline": ("career", "2"),
    "industries-2nd-class-power-engineers": ("career", "2"),
    "power-engineer-salary-canada": ("career", "4,3,2"),
    # Finding work
    "power-engineering-jobs-guide": ("work", "4,3,2"),
    "how-to-find-power-engineering-jobs": ("work", "4,3,2"),
    "power-engineering-resume-tips": ("work", "4,3,2"),
    "power-engineering-interview-questions": ("work", "4,3,2"),
    "power-engineer-salary-negotiation": ("work", "4,3,2"),
    "power-engineering-job-application-follow-up": ("work", "4,3,2"),
    "power-engineering-jobs-alberta": ("work", "4,3,2"),
    "power-engineering-jobs-bc": ("work", "4,3,2"),
    "power-engineering-jobs-manitoba": ("work", "4,3,2"),
    "power-engineering-jobs-nova-scotia": ("work", "4,3,2"),
    "power-engineering-jobs-ontario": ("work", "4,3,2"),
    "power-engineering-jobs-saskatchewan": ("work", "4,3,2"),
}

EXISTING_RE = re.compile(r'[ \t]*<meta\s+name="fsa:(?:levels|stage)"[^>]*>\n?')
# Anchor: insert directly after the canonical link, which every article has.
CANONICAL_RE = re.compile(r'(\n[ \t]*<link rel="canonical"[^>]*>\n)')


def apply(slug, stage, levels, check):
    path = ROOT / "articles" / slug / "index.html"
    if not path.exists():
        return f"{slug}: no such article"
    html = path.read_text()
    stripped = EXISTING_RE.sub("", html)
    block = (f'  <meta name="fsa:levels" content="{levels}">\n'
             f'  <meta name="fsa:stage" content="{stage}">\n')
    m = CANONICAL_RE.search(stripped)
    if not m:
        return f"{slug}: no <link rel=\"canonical\"> to anchor the insert to"
    new = stripped[:m.end()] + block + stripped[m.end():]
    if new == html:
        return None
    if not check:
        path.write_text(new)
    return f"{slug}: {'would update' if check else 'updated'} -> {stage} / {levels}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    on_disk = {d.name for d in (ROOT / "articles").iterdir()
               if d.is_dir() and not d.name.startswith(("_", "."))}
    missing = on_disk - set(ASSIGNMENT)
    ghost = set(ASSIGNMENT) - on_disk
    if missing:
        sys.exit(f"Articles on disk with no assignment: {sorted(missing)}")
    if ghost:
        sys.exit(f"Assignments with no article on disk: {sorted(ghost)}")

    changes = [r for slug, (stage, lv) in sorted(ASSIGNMENT.items())
               if (r := apply(slug, stage, lv, args.check))]
    for line in changes:
        print(" ", line)
    print(f"{len(changes)} of {len(ASSIGNMENT)} articles "
          f"{'would change' if args.check else 'changed'}")
    if args.check and changes:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run it**

Run: `python3 scripts/add_article_metadata.py --check`
Expected: 48 lines of `would update`, then `48 of 48 articles would change`, exit code 1.

If it instead exits with "Articles on disk with no assignment", an article was added since this plan was written. Add it to `ASSIGNMENT` with a stage and levels chosen by reading it, and note the addition in the commit message.

- [ ] **Step 3: Apply it**

Run: `python3 scripts/add_article_metadata.py`
Expected: 48 lines of `updated`, then `48 of 48 articles changed`.

- [ ] **Step 4: Verify the scanner accepts the whole real tree**

Run:
```bash
python3 -c "
import sys, pathlib; sys.path.insert(0,'scripts')
import build_pages as bp
arts = bp.scan_articles(pathlib.Path('articles'))
print('scanned', len(arts))
from collections import Counter
print(dict(Counter(a.stage for a in arts)))
for lv in bp.LEVELS:
    print(lv, sum(1 for a in arts if lv in a.levels))
"
```
Expected exactly:
```
scanned 48
{'choosing': 5, 'studying': 8, 'exam': 16, 'career': 7, 'work': 12}
4 31
3 34
2 45
```

Those counts are the spec's coverage matrix. If any number differs, the assignment table was mistyped. Fix it before continuing; every later task depends on these being right.

- [ ] **Step 5: Verify idempotency**

Run: `python3 scripts/add_article_metadata.py --check`
Expected: `0 of 48 articles would change`, exit code 0. Re-running must not duplicate tags.

- [ ] **Step 6: Verify no article HTML was otherwise damaged**

Run: `git diff --stat articles/ | tail -1`
Expected: 48 files changed, 96 insertions, 0 deletions. Any deletion means the regex removed something it should not have.

- [ ] **Step 7: Commit**

```bash
git add scripts/add_article_metadata.py articles/
git commit -m "feat(articles): tag all 48 articles with level and stage metadata

Assignment from the approved spec, derived by reading each article rather
than keyword matching. Coverage: 4th 31, 3rd 34, 2nd 45 of 48.

Migration script kept in-repo as the record of the assignment and as a
--check drift guard."
```

---

## Task 3: Hub rendering functions

**Files:**
- Modify: `scripts/build_pages.py` (add after `scan_articles`)
- Test: `scripts/test_build_pages.py` (append)

**Interfaces:**
- Consumes: `Article`, `STAGES`, `LEVELS`, `LEVEL_LABELS`, `LEVEL_SLUGS` from Task 1.
- Produces:
  - `render_card(a: Article) -> str`
  - `render_sections(articles: list[Article], level: str | None) -> str`
  - `render_level_nav(current: str | None) -> str`
  - `HUB_PAGES: list[tuple[str|None, str, str, str, str]]` of `(level, out_path, title, h1, intro)`

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_build_pages.py`:

```python
def art(slug, stage="studying", levels=("4", "3", "2"), title=None, desc="D."):
    return bp.Article(slug=slug, title=title or slug, description=desc,
                      levels=list(levels), stage=stage)


def test_render_card_links_to_the_article():
    out = bp.render_card(art("my-slug", title="My Title", desc="My description."))
    assert 'href="/articles/my-slug/"' in out
    assert "My Title" in out
    assert "My description." in out


def test_render_card_escapes_html_in_title_and_description():
    out = bp.render_card(art("s", title="A & B", desc='He said "hi" & left'))
    assert "A &amp; B" in out
    assert "&amp;" in out
    assert '<h3>A & B</h3>' not in out


def test_render_card_shows_a_badge_per_level():
    out = bp.render_card(art("s", levels=("3", "2")))
    assert "3rd Class" in out
    assert "2nd Class" in out
    assert "4th Class" not in out


def test_render_sections_unfiltered_includes_every_article():
    arts = [art("a", "choosing"), art("b", "work"), art("c", "exam")]
    out = bp.render_sections(arts, None)
    for slug in ("a", "b", "c"):
        assert f'href="/articles/{slug}/"' in out


def test_render_sections_orders_stages_as_the_journey():
    arts = [art("w", "work"), art("c", "choosing"), art("e", "exam")]
    out = bp.render_sections(arts, None)
    assert out.index("Choosing your ticket") < out.index("Sitting the exam")
    assert out.index("Sitting the exam") < out.index("Finding work")


def test_render_sections_filters_by_level():
    arts = [art("only2", "exam", levels=("2",)), art("all", "exam")]
    out = bp.render_sections(arts, "4")
    assert 'href="/articles/all/"' in out
    assert 'href="/articles/only2/"' not in out


def test_render_sections_omits_a_stage_with_no_articles_for_that_level():
    arts = [art("only2", "career", levels=("2",)), art("all", "exam")]
    out = bp.render_sections(arts, "4")
    assert "Sitting the exam" in out
    assert "Career paths and pay" not in out


def test_render_sections_shows_a_count_per_stage():
    arts = [art("a", "exam"), art("b", "exam"), art("c", "work")]
    out = bp.render_sections(arts, None)
    assert "Sitting the exam" in out
    assert 'data-count="2"' in out


def test_render_level_nav_marks_the_current_view():
    out = bp.render_level_nav("3")
    assert 'href="/articles/3rd-class/"' in out
    assert "hub-level-active" in out
    assert out.count("hub-level-active") == 1


def test_render_level_nav_on_the_full_index_marks_all_guides():
    out = bp.render_level_nav(None)
    assert 'href="/articles/"' in out
    assert out.count("hub-level-active") == 1


def test_hub_pages_covers_the_full_index_and_three_levels():
    outs = [p[1] for p in bp.HUB_PAGES]
    assert outs == ["articles/index.html", "articles/4th-class/index.html",
                    "articles/3rd-class/index.html", "articles/2nd-class/index.html"]


def test_no_em_dashes_in_any_rendered_output():
    """Style guide bans em dashes everywhere. Guard the generated markup."""
    arts = [art("a", "choosing"), art("b", "exam")]
    blob = bp.render_sections(arts, None) + bp.render_level_nav(None)
    blob += "".join(p[2] + p[3] + p[4] for p in bp.HUB_PAGES)
    assert "—" not in blob
    assert "&mdash;" not in blob
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest scripts/test_build_pages.py -v -k "render or hub or em_dash"`
Expected: FAIL with `AttributeError: module 'build_pages' has no attribute 'render_card'`

- [ ] **Step 3: Write the implementation**

Append to `scripts/build_pages.py`, after `scan_articles`:

```python
def render_card(a: Article) -> str:
    badges = "".join(
        f'<span class="article-card-level">{LEVEL_LABELS[lv]}</span>'
        for lv in a.levels
    )
    title = html_mod.escape(a.title)
    desc = html_mod.escape(a.description)
    return (
        f'        <a href="/articles/{a.slug}/" class="article-card">\n'
        f'          <div class="article-card-levels">{badges}</div>\n'
        f"          <h3>{title}</h3>\n"
        f"          <p>{desc}</p>\n"
        f'          <span class="article-card-read">Read &rarr;</span>\n'
        f"        </a>\n"
    )


def render_sections(articles: list[Article], level: str | None) -> str:
    """Five stage sections. A stage with nothing in it for this level is omitted."""
    out = []
    for key, label in STAGES:
        rows = [a for a in articles
                if a.stage == key and (level is None or level in a.levels)]
        if not rows:
            continue
        rows.sort(key=lambda a: a.title)
        out.append(
            f'    <section class="articles-section">\n'
            f'      <h2 class="articles-section-title" id="{key}" '
            f'data-count="{len(rows)}">{label}</h2>\n'
            f'      <div class="articles-grid">\n\n'
        )
        out.extend(render_card(a) + "\n" for a in rows)
        out.append("      </div>\n    </section>\n\n")
    return "".join(out)


def render_level_nav(current: str | None) -> str:
    items = [(None, "/articles/", "All Guides")]
    items += [(lv, f"/articles/{LEVEL_SLUGS[lv]}/", f"For {LEVEL_LABELS[lv]}")
              for lv in LEVELS]
    links = []
    for lv, href, label in items:
        cls = "hub-level-link hub-level-active" if lv == current else "hub-level-link"
        aria = ' aria-current="page"' if lv == current else ""
        links.append(f'      <a href="{href}" class="{cls}"{aria}>{label}</a>\n')
    return ('    <nav class="hub-level-nav" aria-label="Filter guides by '
            'certification level">\n' + "".join(links) + "    </nav>\n")


# (level, output path, <title>, <h1>, intro paragraph)
HUB_PAGES = [
    (None, "articles/index.html",
     "Power Engineering Guides and Exam Resources",
     "Power Engineering Guides",
     "Every guide we have written, organised by where you are in your "
     "certification. Pick your class above to see only what applies to you."),
    ("4", "articles/4th-class/index.html",
     "4th Class Power Engineering Guides",
     "Guides for 4th Class",
     "Everything we have for operators working toward their 4th Class ticket, "
     "from choosing the path through to landing the job."),
    ("3", "articles/3rd-class/index.html",
     "3rd Class Power Engineering Guides",
     "Guides for 3rd Class",
     "Everything we have for operators upgrading to 3rd Class, from study "
     "method through exam technique to what the ticket is worth."),
    ("2", "articles/2nd-class/index.html",
     "2nd Class Power Engineering Guides",
     "Guides for 2nd Class",
     "Everything we have for operators working toward 2nd Class, including "
     "a guide to each of the six SOPEEC papers."),
]
```

- [ ] **Step 4: Run the full test file to verify it passes**

Run: `python3 -m pytest scripts/test_build_pages.py -v`
Expected: 25 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/build_pages.py scripts/test_build_pages.py
git commit -m "feat(build): hub card, stage section and level nav rendering

Pure functions with tests, not yet wired into build(). Includes a guard
test asserting no em dashes appear in any generated markup."
```

---

## Task 4: The hub template, CSS, and wiring generation into the build

**Files:**
- Create: `partials/article-hub.html`
- Delete: `articles/index.html`
- Modify: `scripts/build_pages.py` (`build()`), `articles/articles.css`
- Test: `scripts/test_build_pages.py` (append)

**Interfaces:**
- Consumes: `HUB_PAGES`, `render_sections`, `render_level_nav`, `scan_articles`, `stitch` from Tasks 1 and 3.
- Produces: `dist/articles/index.html` plus three level hubs, generated. No source `articles/index.html` exists after this task.

- [ ] **Step 1: Create the template from the existing hub**

```bash
cp articles/index.html partials/article-hub.html
```

Then edit `partials/article-hub.html`:

1. In `<head>`, replace the `<title>` contents with `{{TITLE}} &ndash; Full Steam Ahead`, the meta description content with `{{DESCRIPTION}}`, the canonical `href` with `{{CANONICAL}}`, and the `og:title` / `og:description` / `og:url` contents with `{{TITLE}}` / `{{DESCRIPTION}}` / `{{CANONICAL}}`.
2. In the `<section class="articles-header">` block, replace the `<h1>` contents with `{{H1}}` and the intro paragraph contents with `{{INTRO}}`. **Leave the "Most of this is built from primary sources" paragraph exactly as it is** on all four pages; it is a trust signal and applies everywhere.
3. Immediately after the closing `</section>` of `articles-header`, insert a single line containing `{{LEVEL_NAV}}`.
4. Delete everything between `<main class="articles-main">` and `<section class="articles-cta">` (that is, all six hand-written `<section class="articles-section">` blocks) and replace it with a single line containing `{{SECTIONS}}`.
5. Leave the `articles-cta` section, the closing tags, the `INCLUDE:footer` marker and all the `<script>` blocks untouched.

Verify the result:

```bash
for ph in TITLE DESCRIPTION CANONICAL H1 INTRO LEVEL_NAV SECTIONS; do
  printf "%-11s %s\n" "$ph" "$(grep -c "{{$ph}}" partials/article-hub.html)"
done
echo "article-card: $(grep -c 'article-card' partials/article-hub.html)"
echo "INCLUDE:     $(grep -c 'INCLUDE:' partials/article-hub.html)"
```
Expected: TITLE, DESCRIPTION and CANONICAL each appear 2 or more times (they are in both the head and the OG block); H1, INTRO, LEVEL_NAV and SECTIONS each appear exactly 1; `article-card` is **0** (every hand-written card is gone); `INCLUDE:` is 3.

Do not chase an exact total. What matters is that no placeholder is 0 and no hand-written card survives.

- [ ] **Step 2: Write the failing integration test**

Append to `scripts/test_build_pages.py`:

```python
HUB_RELS = ("articles/index.html", "articles/4th-class/index.html",
            "articles/3rd-class/index.html", "articles/2nd-class/index.html")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Build the real site ONCE for all integration tests.

    assets/ is about 1 GB and build() copytrees it. Copying that per test would
    move 4 GB per run and can fill /tmp, so passthrough dirs are disabled for
    the duration. Nothing asserted below touches assets.
    """
    out = tmp_path_factory.mktemp("dist")
    saved = bp.ROOT_PASSTHROUGH_DIRS
    bp.ROOT_PASSTHROUGH_DIRS = []
    try:
        bp.build(out)
    finally:
        bp.ROOT_PASSTHROUGH_DIRS = saved
    return out


def test_build_generates_four_hub_pages(built):
    for rel in HUB_RELS:
        assert (built / rel).exists(), f"{rel} was not generated"


def test_generated_full_index_lists_every_article(built):
    html = (built / "articles/index.html").read_text()
    for a in bp.scan_articles(pathlib.Path(bp.ROOT) / "articles"):
        assert f'href="/articles/{a.slug}/"' in html, f"{a.slug} missing from hub"


def test_generated_hubs_have_no_placeholders_left(built):
    for rel in HUB_RELS:
        html = (built / rel).read_text()
        assert "{{" not in html, f"unsubstituted placeholder in {rel}"
        assert "INCLUDE:" not in html, f"unstitched include in {rel}"


def test_generated_level_hub_excludes_other_levels(built):
    html = (built / "articles/4th-class/index.html").read_text()
    # A 2nd-Class-only article must not appear on the 4th Class hub.
    assert 'href="/articles/sopeec-2a1-exam-guide/"' not in html
    # A level-agnostic one must.
    assert 'href="/articles/sopeec-multiple-choice-traps/"' in html
```

`build()` reads `ROOT_PASSTHROUGH_DIRS` as a module global at call time, so the
fixture's temporary reassignment is enough. Do not change `build()` for this.

- [ ] **Step 3: Run to verify it fails**

Run: `python3 -m pytest scripts/test_build_pages.py -v -k "generated or four_hub"`
Expected: FAIL, because `build()` does not generate hubs yet and `articles/index.html` no longer exists as a source.

- [ ] **Step 4: Wire generation into `build()`**

In `scripts/build_pages.py`, inside `build()`, immediately after the `for tree in STITCHED_DIRS:` loop finishes and before the `for sheet in (...)` font check, insert:

```python
    # Generated hub pages. These have no source file: articles/index.html was
    # deleted on 2026-09-01 because a hand-maintained index drifts. The index
    # is derived from the articles that actually exist.
    articles = scan_articles(ROOT / "articles")
    hub_template = (ROOT / "partials" / "article-hub.html").read_text()
    for level, rel, title, h1, intro in HUB_PAGES:
        page = hub_template
        page = page.replace("{{TITLE}}", title)
        page = page.replace("{{DESCRIPTION}}", intro)
        page = page.replace("{{CANONICAL}}",
                            "https://fullsteamahead.ca/"
                            + rel.replace("index.html", ""))
        page = page.replace("{{H1}}", h1)
        page = page.replace("{{INTRO}}", intro)
        page = page.replace("{{LEVEL_NAV}}", render_level_nav(level))
        page = page.replace("{{SECTIONS}}", render_sections(articles, level))
        page = stitch(page, nav_template, footer_template, fonts_template)
        font_errors += check_fonts(rel, page, allowed)
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page)
        stitched += 1
```

- [ ] **Step 5: Delete the hand-maintained hub**

```bash
git rm articles/index.html
```

The `STITCHED_DIRS` walk over `articles/` will no longer find it, and the generated one is written afterwards, so there is no collision.

- [ ] **Step 6: Add the hub CSS**

Append to `articles/articles.css`:

```css
/* ── Hub level nav and card level badges (2026-09-01, IA restructure) ── */

.hub-level-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  max-width: 1200px;
  margin: 0 auto 2rem;
  padding: 0 1.5rem;
}

.hub-level-link {
  font-family: var(--font-display);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.82rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--plate-edge);
  border-radius: 999px;
  color: var(--gray-light);
  text-decoration: none;
  transition: border-color var(--duration-fast) var(--ease),
              color var(--duration-fast) var(--ease);
}

.hub-level-link:hover { border-color: var(--steel-light); color: var(--white); }

.hub-level-active {
  background: var(--orange);
  border-color: var(--orange);
  color: var(--white);
}

.hub-level-active:hover { border-color: var(--orange-glow); color: var(--white); }

.article-card-levels {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.6rem;
}

.article-card-level {
  font-family: var(--font-display);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.68rem;
  padding: 0.15rem 0.5rem;
  border: 1px solid var(--plate-edge);
  border-radius: 3px;
  color: var(--gray-mid);
}
```

- [ ] **Step 7: Run the tests**

Run: `python3 -m pytest scripts/test_build_pages.py -v`
Expected: 29 passed

- [ ] **Step 8: Build and check the counts against the spec's coverage matrix**

Run:
```bash
python3 scripts/build_pages.py
for f in index 4th-class 3rd-class 2nd-class; do
  p="dist/articles/$f/index.html"; [ "$f" = index ] && p="dist/articles/index.html"
  printf "%-12s %s cards\n" "$f" "$(grep -c 'class="article-card"' $p)"
done
```
Expected exactly:
```
index        48 cards
4th-class    31 cards
3rd-class    34 cards
2nd-class    45 cards
```

- [ ] **Step 9: Prove the guardrail actually fires**

Do not assume it works. Break one article and watch the build fail:

```bash
sed -i 's/<meta name="fsa:stage" content="exam">/<meta name="fsa:stage" content="bogus">/' \
  articles/sopeec-multiple-choice-traps/index.html
python3 scripts/build_pages.py; echo "exit=$?"
git checkout articles/sopeec-multiple-choice-traps/index.html
python3 scripts/build_pages.py; echo "exit=$?"
```
Expected: first run prints `Article metadata check failed:` naming `sopeec-multiple-choice-traps` and exits non-zero; second run succeeds. If the first run succeeds, the validation is not wired in and the whole guarantee is fake.

- [ ] **Step 10: Commit**

```bash
git add scripts/build_pages.py scripts/test_build_pages.py partials/article-hub.html articles/articles.css
git add -u
git commit -m "feat(articles): generate the hub and three level views at build time

articles/index.html is deleted and replaced by generated output from
partials/article-hub.html. The hub is now derived from the articles that
exist, so it cannot drift. Counts: 48 / 31 / 34 / 45.

A missing or malformed fsa:stage or fsa:levels tag now fails the build."
```

---

## Task 5: Rewrite the Resources dropdown, fix the nav em dashes

**Files:**
- Modify: `partials/nav.html`
- Test: `scripts/test_build_pages.py` (append)

**Interfaces:**
- Consumes: the three level hub URLs produced by Task 4.
- Produces: a Resources dropdown that points at level hubs and free tools only, never at an individual article.

This is a single-file change that applies to all 70 pages, which is the whole point of the partials architecture. Do not edit any page directly.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_build_pages.py`:

```python
NAV = pathlib.Path(bp.ROOT) / "partials" / "nav.html"


def test_nav_has_no_em_dashes():
    """Style guide: never. Called out publicly as an AI tell in a 25k-member group."""
    text = NAV.read_text()
    assert "—" not in text
    assert "&mdash;" not in text


def test_resources_dropdown_points_at_level_hubs():
    text = NAV.read_text()
    for slug in ("4th-class", "3rd-class", "2nd-class"):
        assert f'href="/articles/{slug}/"' in text


def test_resources_dropdown_promotes_no_individual_article():
    """The old menu sent people to five specific articles, three of them
    2nd-Class-branded. A 4th Class candidate had no route to anything."""
    text = NAV.read_text()
    for gone in ("2nd-class-power-engineering-exam-guide",
                 "how-to-study-for-power-engineering-exams",
                 "2nd-class-power-engineering-certificate-careers",
                 "power-engineering-jobs-guide",
                 "sopeec-2nd-class-exam-papers"):
        assert gone not in text, f"nav still links directly to {gone}"


def test_mobile_menu_also_carries_the_level_hubs():
    text = NAV.read_text()
    mobile = text[text.index('class="mobile-menu"'):]
    for slug in ("4th-class", "3rd-class", "2nd-class"):
        assert f'href="/articles/{slug}/"' in mobile


def test_nav_still_has_the_free_tools_and_the_escape_hatch():
    text = NAV.read_text()
    assert 'href="/library"' in text
    assert 'href="/free-practice-exam"' in text
    assert 'href="/articles/"' in text
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m pytest scripts/test_build_pages.py -v -k "nav or dropdown or mobile"`
Expected: `test_nav_has_no_em_dashes` FAILS (three in the Programs menu), `test_resources_dropdown_points_at_level_hubs` FAILS, `test_resources_dropdown_promotes_no_individual_article` FAILS.

- [ ] **Step 3: Fix the Programs dropdown em dashes**

In `partials/nav.html`, replace these three lines:

```html
        <li role="none"><a href="/4th-class-complete" role="menuitem">4th Class — $<span data-price="fourthClass.current">99</span>/paper, per year</a></li>
        <li role="none"><a href="/3rd-class-complete" role="menuitem">3rd Class — $<span data-price="thirdClass.current">99</span>/month</a></li>
        <li role="none"><a href="/2nd-class-complete" role="menuitem">2nd Class — $<span data-price="secondClass.current">149</span>/month</a></li>
```

with:

```html
        <li role="none"><a href="/4th-class-complete" role="menuitem">4th Class, $<span data-price="fourthClass.current">99</span>/paper per year</a></li>
        <li role="none"><a href="/3rd-class-complete" role="menuitem">3rd Class, $<span data-price="thirdClass.current">99</span>/month</a></li>
        <li role="none"><a href="/2nd-class-complete" role="menuitem">2nd Class, $<span data-price="secondClass.current">149</span>/month</a></li>
```

The `data-price` spans are preserved exactly. Never hardcode a price.

- [ ] **Step 4: Replace the Resources dropdown**

Replace the entire `<ul class="nav-dropdown-menu nav-dropdown-menu-left" role="menu">` block that follows the Resources trigger button (the one containing "Exam Guide", "Study Methods", "Career &amp; Industry", "Jobs &amp; Getting Hired", "2nd Class Papers", "Free Book Library", "Free Practice Exam", "All Guides") with:

```html
      <ul class="nav-dropdown-menu nav-dropdown-menu-left" role="menu">
        <li role="none"><a href="/articles/4th-class/" role="menuitem">Guides for 4th Class</a></li>
        <li role="none"><a href="/articles/3rd-class/" role="menuitem">Guides for 3rd Class</a></li>
        <li role="none"><a href="/articles/2nd-class/" role="menuitem">Guides for 2nd Class</a></li>
        <li role="none" class="nav-dropdown-sep"><a href="/library" role="menuitem">Free Book Library</a></li>
        <li role="none"><a href="/free-practice-exam" role="menuitem">Free Practice Exam</a></li>
        <li role="none" class="nav-dropdown-sep"><a href="/articles/" role="menuitem">All Guides &rarr;</a></li>
      </ul>
```

- [ ] **Step 5: Update the mobile menu**

In the `<div class="mobile-menu">` block, replace these three list items:

```html
      <li><a href="/articles/2nd-class-power-engineering-exam-guide/">Exam Guide</a></li>
      <li><a href="/articles/how-to-study-for-power-engineering-exams/">Study Methods</a></li>
      <li><a href="/articles/sopeec-2nd-class-exam-papers/">2nd Class Papers</a></li>
```

with:

```html
      <li><a href="/articles/4th-class/">Guides for 4th Class</a></li>
      <li><a href="/articles/3rd-class/">Guides for 3rd Class</a></li>
      <li><a href="/articles/2nd-class/">Guides for 2nd Class</a></li>
```

- [ ] **Step 6: Add the separator style**

Append to `styles-v2.css`:

```css
/* Visual grouping inside the Resources dropdown (2026-09-01) */
.nav-dropdown-menu .nav-dropdown-sep {
  border-top: 1px solid var(--plate-edge);
  margin-top: 0.35rem;
  padding-top: 0.35rem;
}
```

- [ ] **Step 7: Run the tests**

Run: `python3 -m pytest scripts/test_build_pages.py -v`
Expected: 34 passed

- [ ] **Step 8: Verify it propagated to every page**

Run:
```bash
python3 scripts/build_pages.py
echo "pages with a level hub link: $(grep -rl 'articles/4th-class/' dist --include=index.html --include=*.html | wc -l)"
echo "em dashes anywhere in dist nav: $(grep -rc '—' dist/index.html)"
```
Expected: the level hub link appears on all 68 nav-bearing pages; the homepage reports 0 em dashes.

- [ ] **Step 9: Commit**

```bash
git add partials/nav.html styles-v2.css scripts/test_build_pages.py
git commit -m "feat(nav): Resources dropdown points at level hubs, not articles

Five of the eight Resources items were individual articles wearing category
names, three of them 2nd-Class-branded, so a 4th Class candidate had no route
to anything scoped to them. Replaced with three level hubs, the two free
tools and All Guides.

Also removes the three em dashes from the Programs dropdown, which rendered
on all 70 pages. Style guide bans them; a member of a 25k-person Facebook
group called FSA content out for them specifically."
```

---

## Task 6: Sitemap, manifest demotion, and Phase 1 deploy

**Files:**
- Modify: `sitemap.xml`, `scripts/articles_manifest.json`, `wiki/projects/fsa-website.md` (separate repo)
- Test: `scripts/test_build_pages.py` (append)

**Interfaces:**
- Consumes: the three level hub URLs from Task 4.
- Produces: a deployable Phase 1. No later task depends on this one.

- [ ] **Step 1: Write the failing sitemap parity test**

Append to `scripts/test_build_pages.py`:

```python
def test_sitemap_lists_every_article_and_every_hub():
    import re as _re
    sitemap = (pathlib.Path(bp.ROOT) / "sitemap.xml").read_text()
    locs = set(_re.findall(r"<loc>https://fullsteamahead\.ca/(.*?)</loc>", sitemap))
    for a in bp.scan_articles(pathlib.Path(bp.ROOT) / "articles"):
        assert f"articles/{a.slug}/" in locs, f"{a.slug} missing from sitemap"
    for slug in ("4th-class", "3rd-class", "2nd-class"):
        assert f"articles/{slug}/" in locs, f"hub {slug} missing from sitemap"
    assert "articles/" in locs


def test_sitemap_has_no_loc_without_a_page():
    import re as _re
    sitemap = (pathlib.Path(bp.ROOT) / "sitemap.xml").read_text()
    art_locs = set(_re.findall(
        r"<loc>https://fullsteamahead\.ca/articles/([a-z0-9-]+)/</loc>", sitemap))
    hubs = {"4th-class", "3rd-class", "2nd-class"}
    slugs = {a.slug for a in bp.scan_articles(pathlib.Path(bp.ROOT) / "articles")}
    orphans = art_locs - slugs - hubs
    assert not orphans, f"sitemap lists pages that do not exist: {sorted(orphans)}"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m pytest scripts/test_build_pages.py -v -k sitemap`
Expected: FAIL, `hub 4th-class missing from sitemap`

- [ ] **Step 3: Add the three hub entries**

Insert immediately after the existing `<url>` block for `https://fullsteamahead.ca/articles/`:

```xml
  <url>
    <loc>https://fullsteamahead.ca/articles/4th-class/</loc>
    <lastmod>2026-09-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>

  <url>
    <loc>https://fullsteamahead.ca/articles/3rd-class/</loc>
    <lastmod>2026-09-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>

  <url>
    <loc>https://fullsteamahead.ca/articles/2nd-class/</loc>
    <lastmod>2026-09-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
```

Also set `<lastmod>` to today on the homepage entry and the `/articles/` entry, per the deploy skill.

- [ ] **Step 4: Validate the XML and run the tests**

Run:
```bash
python3 -c "import xml.dom.minidom as m; m.parse('sitemap.xml'); print('XML OK')"
python3 -m pytest scripts/test_build_pages.py -v
```
Expected: `XML OK`, then 36 passed.

- [ ] **Step 5: Demote the manifest to a content plan**

Add `"status": "published"` to each of the 28 manifest entries whose slug has an article directory, and `"status": "planned"` to the 6 that do not (`absa-exam-alberta-requirements`, `power-engineering-salary-by-class`, `4th-class-power-engineering-salary`, `process-operator-to-power-engineer`, `stationary-engineer-vs-power-engineer`, `pan-global-vs-ai-adaptive-learning`).

```bash
python3 - <<'PY'
import json, os
p = 'scripts/articles_manifest.json'
m = json.load(open(p))
dirs = {d for d in os.listdir('articles')
        if os.path.isdir(f'articles/{d}') and not d.startswith(('_', '.'))}
for a in m['articles']:
    a['status'] = 'published' if a['slug'] in dirs else 'planned'
open(p, 'w').write(json.dumps(m, indent=2) + '\n')
print('published:', sum(1 for a in m['articles'] if a['status'] == 'published'))
print('planned:  ', sum(1 for a in m['articles'] if a['status'] == 'planned'))
PY
```
Expected: `published: 28`, `planned: 6`.

**Do not backfill the 20 missing entries.** The filesystem is the source of truth for what exists. Duplicating it into the manifest recreates the drift this whole design exists to kill.

- [ ] **Step 6: Document the new manifest contract**

In `wiki/projects/fsa-website.md` (the wiki is a separate git repo at `/home/debian/wiki`), add to the articles section:

```markdown
### articles_manifest.json is a content plan, not an index (2026-09-01)

It is **not** a rendering input and must **not** be kept in sync with what is
live. The hub pages are generated by `build_pages.py` from the `fsa:levels`
and `fsa:stage` meta tags in each article's own `<head>`, so the article file
is the single source of truth for its own placement.

The manifest keeps one job: recording articles that are **planned and not yet
written** (`"status": "planned"`). It drifted to describing 34 articles against
48 live before this was settled, which is exactly why it was demoted rather
than repaired. Do not "fix" it back into a half-index.
```

- [ ] **Step 7: Full verification before deploy**

```bash
python3 -m pytest scripts/test_build_pages.py -v
python3 scripts/build_pages.py
ls -d articles/*/ | grep -v _template | grep -v impeccable | sed 's#articles/##;s#/$##' | sort > /tmp/f.txt
grep -oP '(?<=articles/)[a-z0-9-]+(?=/</loc>)' sitemap.xml | sort > /tmp/s.txt
echo "missing from sitemap:"; comm -23 /tmp/f.txt /tmp/s.txt
echo "in sitemap, no folder:"; comm -13 /tmp/f.txt /tmp/s.txt
```
Expected: all tests pass, build succeeds, "missing from sitemap" is empty, and "in sitemap, no folder" lists only the three hub slugs (which are generated, not folders, so this is correct).

- [ ] **Step 8: Render check at both widths**

Serve `dist/` on a free port and screenshot `/articles/`, `/articles/4th-class/` at 1280px and 390px. Confirm: no page-level horizontal overflow, no console errors, level pills wrap rather than overflow, and the active pill is the right one on each page.

- [ ] **Step 9: Commit**

```bash
git add sitemap.xml scripts/articles_manifest.json scripts/test_build_pages.py
git commit -m "feat(articles): sitemap entries for the three level hubs

Also demotes articles_manifest.json to a content plan with an explicit
status field. 28 published, 6 planned. It is no longer a rendering input
and is deliberately not backfilled to match what is live."
```

- [ ] **Step 10: Deploy Phase 1 (only when the user says so)**

Follow the `fsa-website-deploy` skill in order: push, `docker compose build --no-cache`, recreate the container, submit the sitemap, purge Cloudflare. **The purge must exit `0`.** Exit `2` means only the named URLs are cold and the deploy must not be reported complete.

Verify on the live public URLs, never localhost:

```bash
for u in / /articles/ /articles/4th-class/ /articles/3rd-class/ /articles/2nd-class/; do
  printf "%s  https://fullsteamahead.ca%s\n" \
    "$(curl -s -o /dev/null -w '%{http_code}' "https://fullsteamahead.ca$u")" "$u"
done
```
Expected: 200 on all five.

Then append a `wiki/log.md` entry recording what shipped and the coverage numbers.

---

# Phase 2: slug renames

Phase 1 must be deployed and verified before starting this. The two phases are independent, but shipping them together makes a rollback harder to reason about.

## Task 7: Rename the four misleading slugs

**Files:**
- Rename: 4 directories under `articles/`
- Modify: every file containing a reference to an old slug
- Test: `scripts/test_build_pages.py` (append)

**Interfaces:**
- Consumes: `scan_articles` from Task 1.
- Produces: `RENAMES: dict[str,str]` in `scripts/build_pages.py`, used by Task 8 to generate redirects and by the test below.

These four have level-neutral content behind a 2nd-Class URL. The other 14 branded slugs are correctly scoped and are deliberately left alone.

| From | To |
|---|---|
| `2nd-class-exam-day-what-to-expect` | `power-engineering-exam-day` |
| `how-long-to-prepare-2nd-class-exam` | `how-long-to-prepare-power-engineering-exam` |
| `past-papers-2nd-class-power-engineering` | `past-papers-power-engineering` |
| `cost-of-2nd-class-power-engineering-exam-prep` | `cost-of-power-engineering-exam-prep` |

- [ ] **Step 1: Write the failing test**

Append to `scripts/test_build_pages.py`:

```python
def test_no_file_references_a_renamed_slug():
    """After the rename, an old slug may appear ONLY in the redirect config."""
    import subprocess
    for old in bp.RENAMES:
        out = subprocess.run(
            ["grep", "-rl", old, ".",
             "--include=*.html", "--include=*.json", "--include=*.xml",
             "--exclude-dir=dist", "--exclude-dir=.git"],
            capture_output=True, text=True, cwd=bp.ROOT).stdout.split()
        assert not out, f"{old} still referenced in {out}"


def test_renamed_articles_exist_at_their_new_slug():
    slugs = {a.slug for a in bp.scan_articles(pathlib.Path(bp.ROOT) / "articles")}
    for old, new in bp.RENAMES.items():
        assert new in slugs, f"{new} does not exist"
        assert old not in slugs, f"{old} still exists"
```

- [ ] **Step 2: Add the rename map to `build_pages.py`**

Insert after `HUB_PAGES`:

```python
# Slugs renamed 2026-09-01 because the URL said 2nd Class while the content
# served every level. Kept here so the nginx redirects and the guard test
# read from one list. Do NOT delete entries: the redirects depend on them.
RENAMES = {
    "2nd-class-exam-day-what-to-expect": "power-engineering-exam-day",
    "how-long-to-prepare-2nd-class-exam": "how-long-to-prepare-power-engineering-exam",
    "past-papers-2nd-class-power-engineering": "past-papers-power-engineering",
    "cost-of-2nd-class-power-engineering-exam-prep": "cost-of-power-engineering-exam-prep",
}
```

- [ ] **Step 3: Run to verify it fails**

Run: `python3 -m pytest scripts/test_build_pages.py -v -k renamed`
Expected: FAIL, `power-engineering-exam-day does not exist`

- [ ] **Step 4: Rename the directories**

```bash
git mv articles/2nd-class-exam-day-what-to-expect articles/power-engineering-exam-day
git mv articles/how-long-to-prepare-2nd-class-exam articles/how-long-to-prepare-power-engineering-exam
git mv articles/past-papers-2nd-class-power-engineering articles/past-papers-power-engineering
git mv articles/cost-of-2nd-class-power-engineering-exam-prep articles/cost-of-power-engineering-exam-prep
```

- [ ] **Step 5: Rewrite every reference**

```bash
python3 - <<'PY'
import pathlib, sys
sys.path.insert(0, 'scripts')
import build_pages as bp

targets = []
for pat in ("articles/**/*.html", "*.html", "resources/**/*.html",
            "sitemap.xml", "scripts/articles_manifest.json"):
    targets += pathlib.Path('.').glob(pat)

changed = 0
for p in targets:
    if 'dist/' in str(p):
        continue
    text = original = p.read_text()
    for old, new in bp.RENAMES.items():
        text = text.replace(old, new)
    if text != original:
        p.write_text(text)
        changed += 1
        print('  updated', p)
print(changed, 'files updated')
PY
```

Then update each renamed article's own self-references, which the pass above already covers: `<link rel="canonical">`, `og:url`, the JSON-LD `url` and its breadcrumb `item`.

- [ ] **Step 6: Update the migration script's assignment table**

In `scripts/add_article_metadata.py`, change the four `ASSIGNMENT` keys to the new slugs. Then run `python3 scripts/add_article_metadata.py --check` and expect `0 of 48 articles would change` with exit 0. If it reports "Assignments with no article on disk", a key was missed.

- [ ] **Step 7: Run the tests and build**

```bash
python3 -m pytest scripts/test_build_pages.py -v
python3 scripts/build_pages.py
```
Expected: 38 passed; build reports 48 articles as before.

- [ ] **Step 8: Confirm no dangling internal links**

```bash
grep -oh 'href="/articles/[a-z0-9-]*/"' dist/articles/*/index.html dist/articles/index.html \
  | sort -u | sed 's|href="/||;s|/"||' | while read l; do
    [ -d "$l" ] || echo "DANGLING: $l"
  done
```
Expected: no output apart from the three generated hub slugs (`articles/4th-class` etc), which have no source folder by design.

- [ ] **Step 9: Commit**

```bash
git add -u
git add scripts/build_pages.py scripts/test_build_pages.py scripts/add_article_metadata.py
git commit -m "refactor(articles): rename four slugs that said 2nd Class but were not

These four carry level-agnostic content behind a 2nd-Class URL. The other
14 branded slugs are correctly scoped and are left alone.

Redirects land in the next commit; do not deploy this commit on its own."
```

---

## Task 8: 301 redirects for the old slugs

**Files:**
- Modify: `nginx.conf.template`
- Test: manual, against the live URL after deploy

**Interfaces:**
- Consumes: `RENAMES` from Task 7.
- Produces: nothing later depends on this.

- [ ] **Step 1: Add the redirect blocks**

`nginx.conf.template` already does a server-level `rewrite ^/(.+)\.html$ /$1 permanent;` at line 17. Add these four `location` blocks immediately **after** that rewrite and **before** the `location = /` block, so they are matched as exact locations before the generic handlers:

```nginx
    # Article slugs renamed 2026-09-01: the URL said 2nd Class while the
    # content served every level. Keep these; they are the only thing standing
    # between an old Facebook-group link and a 404.
    location = /articles/2nd-class-exam-day-what-to-expect/ {
        return 301 /articles/power-engineering-exam-day/;
    }
    location = /articles/how-long-to-prepare-2nd-class-exam/ {
        return 301 /articles/how-long-to-prepare-power-engineering-exam/;
    }
    location = /articles/past-papers-2nd-class-power-engineering/ {
        return 301 /articles/past-papers-power-engineering/;
    }
    location = /articles/cost-of-2nd-class-power-engineering-exam-prep/ {
        return 301 /articles/cost-of-power-engineering-exam-prep/;
    }
```

- [ ] **Step 2: Validate the config renders and nginx accepts it**

```bash
docker compose -f docker-compose.yml build
docker rm -f fsa-website && docker compose -f docker-compose.yml up -d
sleep 3
docker exec fsa-website nginx -t
```
Expected: `syntax is ok` and `test is successful`. If nginx rejects the config the container will be restarting; check `docker logs fsa-website`.

- [ ] **Step 3: Verify the redirects locally before deploying**

```bash
for old in 2nd-class-exam-day-what-to-expect \
           how-long-to-prepare-2nd-class-exam \
           past-papers-2nd-class-power-engineering \
           cost-of-2nd-class-power-engineering-exam-prep; do
  printf "%s %s\n" \
    "$(curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}' \
       "http://127.0.0.1:8087/articles/$old/")" "$old"
done
```
Expected: `301 -> /articles/<new-slug>/` for all four.

- [ ] **Step 4: Commit**

```bash
git add nginx.conf.template
git commit -m "feat(nginx): 301 the four renamed article slugs

Verified locally: all four return 301 to the new path before deploy."
```

- [ ] **Step 5: Deploy Phase 2 (only when the user says so)**

Follow the `fsa-website-deploy` skill. Pass the changed paths to the purge so the fallback list is right:

```bash
bash scripts/purge_cloudflare.sh /sitemap.xml \
  /articles/power-engineering-exam-day/index.html \
  /articles/how-long-to-prepare-power-engineering-exam/index.html \
  /articles/past-papers-power-engineering/index.html \
  /articles/cost-of-power-engineering-exam-prep/index.html
```
The purge must exit `0`.

- [ ] **Step 6: Verify the redirects on the live domain, through Cloudflare**

```bash
for old in 2nd-class-exam-day-what-to-expect \
           how-long-to-prepare-2nd-class-exam \
           past-papers-2nd-class-power-engineering \
           cost-of-2nd-class-power-engineering-exam-prep; do
  printf "%s %s\n" \
    "$(curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}' \
       "https://fullsteamahead.ca/articles/$old/")" "$old"
done
```
Expected: `301` to the new HTTPS URL for all four. **Cloudflare can cache a redirect, so this must be checked after the purge, not before.**

Then append a `wiki/log.md` entry.

---

## What is deliberately not in this plan

**Phase 3, the level-inclusive rewrite.** Nine articles need editorial passes:
`active-recall-power-engineering`, `spaced-repetition-power-engineering`,
`study-schedule-power-engineering-job`, `ai-tutoring-power-engineering-study`,
`multiple-choice-power-engineering-strategy`, `power-engineering-exam-time-management`,
`mental-prep-power-engineering-exam`, `power-engineering-exam-stress`,
`power-engineering-interview-questions`. Plus a retitle of
`practice-questions-vs-full-course` and a rewrite of `cost-of-power-engineering-exam-prep`
to cover all three price points. This is writing, and it needs its own plan with
per-article acceptance criteria rather than a test cycle.

**Phase 4, the gap fill.** The coverage matrix exposes that 4th Class has one career
article and no exam guide, and neither 4th nor 3rd has paper guides. Those are new
articles, each needing its own scoping.

Both should be planned after Phase 1 is live and the level views can be looked at.
