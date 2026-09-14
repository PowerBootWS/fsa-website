#!/usr/bin/env python3
"""
Build step for fsa-website — stitches shared nav/footer partials into every
source HTML page and assembles the servable tree in dist/.

Added 2026-07-28 to kill the nav/footer duplication problem (identical
<nav>/<footer> blocks copy-pasted across 50+ pages, drifting silently —
see wiki/projects/fsa-website.md for the incident that prompted this).

Source pages mark where the shared blocks go with HTML comments:

    <!-- INCLUDE:fonts -->
    <!-- INCLUDE:nav [active="how-it-works"|"resources"|"enroll"] [enroll_href="..."] -->
    <!-- INCLUDE:footer -->

INCLUDE:fonts goes in <head> and emits the Google Fonts preconnect/preload/noscript
block. It exists because a CSS custom property cannot download a font: styles-v2.css
can say `font-family: var(--font-body)`, but something in the document still has to
fetch the file, and that link was copy-pasted into 66 heads. 61 of them requested
plain `Barlow`, which no rule in styles-v2.css or articles.css references, while
`IBM Plex Sans` -- the face `body` is actually set to -- never loaded at all. Nothing
errored; the body copy just rendered in system sans for months (2026-08-27).

coming-soon.html deliberately has no INCLUDE:fonts marker: it is the only page still
on the legacy styles.css, where `'Barlow'` is a real rule, so it keeps its own link.

`active` controls which nav item gets the nav-active styling on that page;
omit it for pages with no active nav item (e.g. the homepage). `enroll_href`
overrides the "Start Today" CTA's target — defaults to the standard enroll
page, but 2nd-class-complete.html/3rd-class-complete.html point it at their
own embedded signup form (#enroll-form) instead, since they're self-contained
landing pages, not a link to a separate page. These are the two pieces of
real per-page nav state — everything else in partials/nav.html is identical
across every page that includes it.

A handful of pages (enrollment-confirmation.html, 404.html,
free-practice-exam.html, library.html) have a genuinely different nav
structure — not just a different active item — so they keep their own
hand-written <nav> block and have no INCLUDE:nav marker. They still use
INCLUDE:footer, since the footer has no such structural exceptions.

Usage:
    python3 scripts/build_pages.py [--out dist]
"""

import argparse
import html as html_mod
import pathlib
import re
import shutil
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).parent.parent

# Exact allowlist of what ships — mirrors the old Dockerfile's individual
# COPY lines. Keep this in sync if a new root-level file is added; the
# same "forgot to list it" trap the old Dockerfile had still applies here,
# just in one place instead of two (Dockerfile + this list).
ROOT_HTML_PAGES = [
    "index.html", "how-it-works.html", "coming-soon.html",
    "privacy-policy.html", "terms-of-use.html", "affiliate.html",
    "affiliate-dashboard.html", "affiliate-confirmation.html",
    "enrollment-confirmation.html", "enroll.html",
    "3rd-class-complete.html", "2nd-class-complete.html", "4th-class-complete.html",
    "library.html", "free-practice-exam.html", "two-weeks-out.html",
    "jobs.html", "404.html", "compare.html",
]
ROOT_PASSTHROUGH_FILES = [
    "exit-intent.js", "exit-intent-jobs.js", "exit-intent-exam-articles.js",
    "nav.js", "pricing.js", "styles.css", "styles-v2.css",
    "sitemap.xml", "robots.txt",
]
ROOT_PASSTHROUGH_DIRS = ["assets"]
# Trees walked and stitched file-by-file. resources/ moved here from
# ROOT_PASSTHROUGH_DIRS on 2026-08-27: as passthrough its two lead-magnet
# landing pages could not receive INCLUDE:fonts (or nav/footer), so they
# kept a stale hand-pasted font link nobody would have thought to check.
STITCHED_DIRS = ["articles", "resources"]

ACTIVE_TOKENS = {
    "how-it-works": {"{{ACTIVE_HOW_IT_WORKS}}": ' class="nav-active"'},
    "programs":     {"{{ACTIVE_PROGRAMS}}": " nav-active"},
    "resources":    {"{{ACTIVE_RESOURCES}}": " nav-active"},
    # Legacy alias: the nav item was called "Exam Prep" until 2026-08-11. Any
    # page still carrying active="exam-prep" keeps highlighting the right item.
    "exam-prep":    {"{{ACTIVE_RESOURCES}}": " nav-active"},
    "enroll":       {"{{ACTIVE_ENROLL}}": ' class="nav-active"'},
}
ALL_ACTIVE_PLACEHOLDERS = [
    "{{ACTIVE_HOW_IT_WORKS}}", "{{ACTIVE_RESOURCES}}", "{{ACTIVE_PROGRAMS}}",
    "{{ACTIVE_ENROLL}}",
]
DEFAULT_ENROLL_HREF = "https://fullsteamahead.ca/enroll"

INCLUDE_NAV_RE = re.compile(
    r'<!--\s*INCLUDE:nav'
    r'(?:\s+active="([^"]*)")?'
    r'(?:\s+enroll_href="([^"]*)")?'
    r'\s*-->'
)
INCLUDE_FOOTER_RE = re.compile(r'<!--\s*INCLUDE:footer\s*-->')
INCLUDE_FONTS_RE = re.compile(r'<!--\s*INCLUDE:fonts\s*-->')
INCLUDE_HOME_GUIDES_RE = re.compile(r'<!--\s*INCLUDE:home-guides\s*-->')


# Families the shared font link actually downloads, parsed from the partial so the
# two can never be asserted apart. Anything else named in a font-family rule is a
# face the browser will not have.
# Stop at ; } or " -- but NOT at ', or the declaration would be cut off before the
# family name and the check would pass on everything. That exact mistake made the
# first version of this guard silently useless.
FONT_FAMILY_RE = re.compile(r'font-family:[^;}"]*')
QUOTED_FAMILY_RE = re.compile(r"'([^']+)'")


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
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


@dataclass
class Article:
    slug: str
    title: str
    description: str
    levels: list[str]
    stage: str


def _text(raw: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", raw)).strip()


def _find_one(pattern: re.Pattern, name: str, slug: str, html: str) -> str | None:
    """Return the single content="..." value for a meta tag, or None if absent.

    Raises if the tag appears more than once -- a second copy (duplicate, or a
    stray leftover from a copy-paste) must be caught, not silently ignored.
    """
    matches = pattern.findall(html)
    if len(matches) > 1:
        raise ValueError(f"{slug}: <meta name=\"{name}\"> appears more than once")
    return matches[0] if matches else None


def parse_article(slug: str, html: str) -> Article:
    """Read one article's metadata. Raises ValueError on anything wrong."""
    # Strip HTML comments first, so a commented-out leftover tag (e.g. from a
    # copy-paste during editing) cannot be matched instead of, or ahead of,
    # the real one.
    stripped = HTML_COMMENT_RE.sub("", html)

    raw = _find_one(META_LEVELS_RE, "fsa:levels", slug, stripped)
    if raw is None or not raw.strip():
        raise ValueError(f"{slug}: missing or empty <meta name=\"fsa:levels\">")
    levels = [v.strip() for v in raw.split(",") if v.strip()]
    if not levels:
        raise ValueError(f"{slug}: missing or empty <meta name=\"fsa:levels\">")
    for lv in levels:
        if lv not in LEVEL_LABELS:
            raise ValueError(
                f"{slug}: fsa:levels contains '{lv}', expected some of {','.join(LEVELS)}"
            )

    raw = _find_one(META_STAGE_RE, "fsa:stage", slug, stripped)
    if raw is None or not raw.strip():
        raise ValueError(f"{slug}: missing or empty <meta name=\"fsa:stage\">")
    stage = raw.strip()
    if stage not in STAGE_KEYS:
        raise ValueError(
            f"{slug}: fsa:stage is '{stage}', expected one of "
            + ", ".join(sorted(STAGE_KEYS))
        )

    m = H1_RE.search(stripped)
    title = _text(m.group(1)) if m else slug
    m = META_DESC_RE.search(stripped)
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


# ── Homepage "Guides & Resources" cards (added 2026-09-09, backlog #119) ──
#
# The homepage used to carry a hardcoded `var ARTICLES = [...]` of 20 articles
# and shuffle 3 of them in client-side. It had frozen before the 3rd Class, 4th
# Class and jobs content existed -- 41 of 61 live articles could never appear --
# and because the cards were injected by JS, the served HTML contained a
# "Loading guides…" placeholder and no article links at all. That wasted the
# strongest internal-link surface on the site (`/` sits at avg position 4.4).
# Same drift the hub pages were fixed for on 2026-09-01, same fix: derive it.
#
# ONE CARD PER JOURNEY STAGE, AND EVERY CARD MUST APPLY TO EVERY VISITOR.
# The homepage is class-agnostic -- a 3rd Class candidate and a 4th Class
# candidate land on the same page -- so a random draw that happened to serve
# five 2nd-Class-specific articles would be showing most arrivals content for a
# ticket they are not working on. Cards are therefore drawn only from articles
# tagged for ALL THREE levels (fsa:levels = 4,3,2), which every stage has at
# least two of. Level-specific guidance is what /articles/4th-class/,
# /articles/3rd-class/ and /articles/2nd-class/ are for, and the section links
# on to those.
#
# The pick is deterministic (first by title within the stage) so an article's
# homepage link is stable across builds rather than changing on every page load
# -- a link Google sees once and never again is not much of a link. To feature a
# specific article for a stage instead, name it in HOME_GUIDE_OVERRIDES; the
# build fails if the slug does not exist or is not valid for that stage, so the
# override cannot rot the way the old array did.

HOME_GUIDE_OVERRIDES: dict[str, str] = {
    # Alphabetical-by-title hands "choosing" the ABSA Alberta fee article, which
    # is province-specific and about exam fees -- a poor first card for someone
    # who does not yet know which ticket they want. The classes explainer is the
    # actual orientation piece for that stage and is national.
    "choosing": "power-engineering-classes-canada",
}


def pick_home_articles(articles: list[Article]) -> list[Article]:
    """One all-levels article per stage, in STAGES order. Raises if a stage is empty."""
    picked: list[Article] = []
    errors: list[str] = []
    for key, label in STAGES:
        pool = sorted(
            (a for a in articles
             if a.stage == key and set(a.levels) == set(LEVELS)),
            key=lambda a: a.title,
        )
        override = HOME_GUIDE_OVERRIDES.get(key)
        if override is not None:
            match = next((a for a in pool if a.slug == override), None)
            if match is None:
                errors.append(
                    f"HOME_GUIDE_OVERRIDES[{key!r}] = {override!r}: no such article, "
                    f"or it is not stage '{key}' with fsa:levels covering all of "
                    + ",".join(LEVELS)
                )
                continue
            picked.append(match)
            continue
        if not pool:
            errors.append(
                f"homepage guides: stage '{key}' ({label}) has no article tagged "
                f"for all of {','.join(LEVELS)}; every stage needs at least one, "
                f"or the homepage would silently drop a stage"
            )
            continue
        picked.append(pool[0])
    if errors:
        raise SystemExit("Homepage guides check failed:\n  " + "\n  ".join(errors))
    return picked


def render_home_cards(articles: list[Article]) -> str:
    """The homepage guides grid, matching .home-article-card in styles-v2.css."""
    labels = dict(STAGES)
    out = []
    for i, a in enumerate(pick_home_articles(articles)):
        desc = html_mod.escape(a.description)
        out.append(
            f'        <a href="/articles/{a.slug}/" class="home-article-card reveal" '
            f'data-delay="{i * 100}">\n'
            f'          <div class="home-article-card-tag">'
            f'{html_mod.escape(labels[a.stage])}</div>\n'
            f"          <h3>{html_mod.escape(a.title)}</h3>\n"
            f"          <p>{desc}</p>\n"
            f'          <span class="home-article-card-read">Read &rarr;</span>\n'
            f"        </a>\n"
        )
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
    return ('    <div class="hub-level-nav" role="navigation" aria-label="Filter '
            'guides by certification level">\n' + "".join(links) + "    </div>\n")


# (level, output path, <title>, <h1>, intro paragraph, bottom CTA paragraph)
#
# The CTA is level-specific: what a 4th Class candidate actually buys ($99 per
# paper per year, non-renewing) is not what a 2nd Class candidate buys ($149/
# month for all six papers), and a hub pitching the wrong product converts
# nobody. Every price in a CTA string is a data-price span, never a bare
# number -- see pricing.js.
HUB_PAGES = [
    (None, "articles/index.html",
     "Power Engineering Guides and Exam Resources",
     "Power Engineering Guides",
     "Every guide we have written, organized by where you are in your "
     "certification. Filter by class to see only what applies to you.",
     "Full Steam Ahead covers every certification level: single 4th Class "
     "papers, a 3rd Class subscription, and a 2nd Class subscription, each "
     "with step-by-step solutions and AI tutoring."),
    ("4", "articles/4th-class/index.html",
     "4th Class Power Engineering Guides",
     "Guides for 4th Class",
     "Everything we have for operators working toward their 4th Class ticket, "
     "from choosing the path through to landing the job.",
     "Full Steam Ahead sells 4A and 4B as separate papers, $"
     '<span data-price="fourthClass.current">99</span> per paper for the '
     "year with no renewal, including practice exams and chapter quizzes."),
    ("3", "articles/3rd-class/index.html",
     "3rd Class Power Engineering Guides",
     "Guides for 3rd Class",
     "Everything we have for operators upgrading to 3rd Class, from study "
     "method through exam technique to what the ticket is worth.",
     "Full Steam Ahead gives you all four 3rd Class exam papers, "
     "step-by-step solutions, and AI tutoring under one $"
     '<span data-price="thirdClass.current">99</span>/month subscription.'),
    ("2", "articles/2nd-class/index.html",
     "2nd Class Power Engineering Guides",
     "Guides for 2nd Class",
     "Everything we have for operators working toward 2nd Class, including "
     "a guide to each of the six SOPEEC papers.",
     "Full Steam Ahead gives you all six 2nd Class exam papers, "
     "step-by-step solutions, and AI tutoring under one $"
     '<span data-price="secondClass.current">149</span>/month subscription.'),
]


# Slugs renamed 2026-09-01 because the URL said 2nd Class while the content
# served every level. Kept here so the nginx redirects and the guard test
# read from one list. Do NOT delete entries: the redirects depend on them.
RENAMES = {
    "2nd-class-exam-day-what-to-expect": "power-engineering-exam-day",
    "how-long-to-prepare-2nd-class-exam": "how-long-to-prepare-power-engineering-exam",
    "past-papers-2nd-class-power-engineering": "past-papers-power-engineering",
    "cost-of-2nd-class-power-engineering-exam-prep": "cost-of-power-engineering-exam-prep",
}


def downloaded_families(fonts_template: str) -> set[str]:
    return {m.replace("+", " ")
            for m in re.findall(r"family=([^&:\"]+)", fonts_template)}


def check_fonts(name: str, html: str, allowed: set[str]) -> list[str]:
    """Names in font-family rules that nothing downloads.

    This exists because the failure is invisible: a page naming a face the
    browser never fetched does not error, does not warn and does not break
    layout -- it silently renders in system sans. That shipped site-wide for
    months, and then twice more in one afternoon while being fixed, each time
    because a literal was matched by exact string instead of by meaning.
    """
    if "styles-v2.css" not in html:
        return []                       # legacy pages carry their own font link
    bad = []
    for decl in FONT_FAMILY_RE.findall(html):
        for fam in QUOTED_FAMILY_RE.findall(decl):
            if fam not in allowed:
                bad.append(f"{name}: font-family names '{fam}', which is never downloaded")
    return bad


def render_nav(template: str, active: str | None, enroll_href: str | None) -> str:
    out = template
    tokens = ACTIVE_TOKENS.get(active, {}) if active else {}
    for placeholder in ALL_ACTIVE_PLACEHOLDERS:
        out = out.replace(placeholder, tokens.get(placeholder, ""))
    out = out.replace("{{ENROLL_HREF}}", enroll_href or DEFAULT_ENROLL_HREF)
    return out


def stitch(html: str, nav_template: str, footer_template: str,
           fonts_template: str, home_guides: str = "") -> str:
    def nav_sub(m: re.Match) -> str:
        return render_nav(nav_template, m.group(1), m.group(2))

    html = INCLUDE_NAV_RE.sub(nav_sub, html)
    html = INCLUDE_FOOTER_RE.sub(footer_template, html)
    html = INCLUDE_FONTS_RE.sub(fonts_template.rstrip("\n"), html)
    # Only index.html carries this marker; passing the block to every page is
    # harmless and keeps substitution in one place.
    html = INCLUDE_HOME_GUIDES_RE.sub(lambda _m: home_guides.rstrip("\n"), html)
    return html


def build(out_dir: pathlib.Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    nav_template = (ROOT / "partials" / "nav.html").read_text()
    footer_template = (ROOT / "partials" / "footer.html").read_text()
    fonts_template = (ROOT / "partials" / "fonts.html").read_text()

    stitched = 0
    copied = 0
    allowed = downloaded_families(fonts_template)
    font_errors: list[str] = []

    # Scanned up here, not just before the hub pages: index.html's guides grid
    # is derived from the same article metadata (see render_home_cards).
    articles = scan_articles(ROOT / "articles")
    home_guides = render_home_cards(articles)

    # Root HTML pages
    for name in ROOT_HTML_PAGES:
        src = ROOT / name
        html = stitch(src.read_text(), nav_template, footer_template,
                      fonts_template, home_guides)
        font_errors += check_fonts(name, html, allowed)
        (out_dir / name).write_text(html)
        stitched += 1

    # Root passthrough files
    for name in ROOT_PASSTHROUGH_FILES:
        shutil.copy2(ROOT / name, out_dir / name)
        copied += 1
    for name in ROOT_PASSTHROUGH_DIRS:
        shutil.copytree(ROOT / name, out_dir / name)
        copied += 1

    # Stitched trees — every .html file gets the partials, everything else
    # (articles.css, images) is copied through untouched.
    for tree in STITCHED_DIRS:
        tree_out = out_dir / tree
        for src in (ROOT / tree).rglob("*"):
            rel = src.relative_to(ROOT / tree)
            dir_parts = rel.parts if src.is_dir() else rel.parts[:-1]
            if any(part.startswith(("_", ".")) for part in dir_parts):
                continue
            dest = tree_out / rel
            if src.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix == ".html":
                html = stitch(src.read_text(), nav_template,
                              footer_template, fonts_template)
                font_errors += check_fonts(str(src.relative_to(ROOT)), html, allowed)
                dest.write_text(html)
                stitched += 1
            else:
                shutil.copy2(src, dest)
                copied += 1

    # Generated hub pages. These have no source file: articles/index.html was
    # deleted on 2026-09-01 because a hand-maintained index drifts. The index
    # is derived from the articles that actually exist.
    hub_template = (ROOT / "partials" / "article-hub.html").read_text()
    for level, rel, title, h1, intro, cta in HUB_PAGES:
        page = hub_template
        page = page.replace("{{TITLE}}", title)
        page = page.replace("{{DESCRIPTION}}", intro)
        page = page.replace("{{CANONICAL}}",
                            "https://fullsteamahead.ca/"
                            + rel.replace("index.html", ""))
        page = page.replace("{{H1}}", h1)
        page = page.replace("{{INTRO}}", intro)
        page = page.replace("{{CTA}}", cta)
        page = page.replace("{{LEVEL_NAV}}", render_level_nav(level))
        page = page.replace("{{SECTIONS}}", render_sections(articles, level))
        page = stitch(page, nav_template, footer_template, fonts_template)
        font_errors += check_fonts(rel, page, allowed)
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page)
        stitched += 1

    for sheet in ("styles-v2.css", "articles/articles.css"):
        font_errors += check_fonts(sheet, 'styles-v2.css' + (ROOT / sheet).read_text(), allowed)

    if font_errors:
        raise SystemExit("Font check failed:\n  " + "\n  ".join(font_errors) +
                         "\n\nUse var(--font-display) / var(--font-body), or add the face to "
                         "partials/fonts.html. See wiki/projects/fsa-website.md.")

    print(f"Built {out_dir}: {stitched} HTML pages stitched, {copied} files/dirs copied through")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    args = parser.parse_args()
    build(ROOT / args.out)


if __name__ == "__main__":
    main()
