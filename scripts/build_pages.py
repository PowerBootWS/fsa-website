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
    "jobs.html", "404.html",
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
           fonts_template: str) -> str:
    def nav_sub(m: re.Match) -> str:
        return render_nav(nav_template, m.group(1), m.group(2))

    html = INCLUDE_NAV_RE.sub(nav_sub, html)
    html = INCLUDE_FOOTER_RE.sub(footer_template, html)
    html = INCLUDE_FONTS_RE.sub(fonts_template.rstrip("\n"), html)
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

    # Root HTML pages
    for name in ROOT_HTML_PAGES:
        src = ROOT / name
        html = stitch(src.read_text(), nav_template, footer_template, fonts_template)
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
            dest = tree_out / src.relative_to(ROOT / tree)
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
