#!/usr/bin/env python3
"""
Build step for fsa-website — stitches shared nav/footer partials into every
source HTML page and assembles the servable tree in dist/.

Added 2026-07-28 to kill the nav/footer duplication problem (identical
<nav>/<footer> blocks copy-pasted across 50+ pages, drifting silently —
see wiki/projects/fsa-website.md for the incident that prompted this).

Source pages mark where the shared blocks go with HTML comments:

    <!-- INCLUDE:nav [active="how-it-works"|"exam-prep"|"enroll"] [enroll_href="..."] -->
    <!-- INCLUDE:footer -->

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
import pathlib
import re
import shutil

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
    "3rd-class-complete.html", "2nd-class-complete.html",
    "library.html", "free-practice-exam.html", "jobs.html", "404.html",
]
ROOT_PASSTHROUGH_FILES = [
    "exit-intent.js", "exit-intent-jobs.js", "exit-intent-exam-articles.js",
    "nav.js", "pricing.js", "styles.css", "styles-v2.css",
    "sitemap.xml", "robots.txt",
]
ROOT_PASSTHROUGH_DIRS = ["assets", "resources"]

ACTIVE_TOKENS = {
    "how-it-works": {"{{ACTIVE_HOW_IT_WORKS}}": ' class="nav-active"'},
    "exam-prep":    {"{{ACTIVE_EXAM_PREP}}": " nav-active"},
    "enroll":       {"{{ACTIVE_ENROLL}}": ' class="nav-active"'},
}
ALL_ACTIVE_PLACEHOLDERS = [
    "{{ACTIVE_HOW_IT_WORKS}}", "{{ACTIVE_EXAM_PREP}}", "{{ACTIVE_ENROLL}}",
]
DEFAULT_ENROLL_HREF = "https://fullsteamahead.ca/enroll.html"

INCLUDE_NAV_RE = re.compile(
    r'<!--\s*INCLUDE:nav'
    r'(?:\s+active="([^"]*)")?'
    r'(?:\s+enroll_href="([^"]*)")?'
    r'\s*-->'
)
INCLUDE_FOOTER_RE = re.compile(r'<!--\s*INCLUDE:footer\s*-->')


def render_nav(template: str, active: str | None, enroll_href: str | None) -> str:
    out = template
    tokens = ACTIVE_TOKENS.get(active, {}) if active else {}
    for placeholder in ALL_ACTIVE_PLACEHOLDERS:
        out = out.replace(placeholder, tokens.get(placeholder, ""))
    out = out.replace("{{ENROLL_HREF}}", enroll_href or DEFAULT_ENROLL_HREF)
    return out


def stitch(html: str, nav_template: str, footer_template: str) -> str:
    def nav_sub(m: re.Match) -> str:
        return render_nav(nav_template, m.group(1), m.group(2))

    html = INCLUDE_NAV_RE.sub(nav_sub, html)
    html = INCLUDE_FOOTER_RE.sub(footer_template, html)
    return html


def build(out_dir: pathlib.Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    nav_template = (ROOT / "partials" / "nav.html").read_text()
    footer_template = (ROOT / "partials" / "footer.html").read_text()

    stitched = 0
    copied = 0

    # Root HTML pages
    for name in ROOT_HTML_PAGES:
        src = ROOT / name
        html = stitch(src.read_text(), nav_template, footer_template)
        (out_dir / name).write_text(html)
        stitched += 1

    # Root passthrough files
    for name in ROOT_PASSTHROUGH_FILES:
        shutil.copy2(ROOT / name, out_dir / name)
        copied += 1
    for name in ROOT_PASSTHROUGH_DIRS:
        shutil.copytree(ROOT / name, out_dir / name)
        copied += 1

    # articles/ — every .html file gets stitched, everything else (articles.css) copied
    articles_out = out_dir / "articles"
    for src in (ROOT / "articles").rglob("*"):
        rel = src.relative_to(ROOT / "articles")
        dest = articles_out / rel
        if src.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix == ".html":
            dest.write_text(stitch(src.read_text(), nav_template, footer_template))
            stitched += 1
        else:
            shutil.copy2(src, dest)
            copied += 1

    print(f"Built {out_dir}: {stitched} HTML pages stitched, {copied} files/dirs copied through")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    args = parser.parse_args()
    build(ROOT / args.out)


if __name__ == "__main__":
    main()
