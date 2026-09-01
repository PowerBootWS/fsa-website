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
    "cost-of-power-engineering-exam-prep": ("choosing", "4,3,2"),
    "how-long-to-prepare-power-engineering-exam": ("choosing", "4,3,2"),
    # Studying for it
    "how-to-study-for-power-engineering-exams": ("studying", "4,3,2"),
    "active-recall-power-engineering": ("studying", "4,3,2"),
    "spaced-repetition-power-engineering": ("studying", "4,3,2"),
    "study-schedule-power-engineering-job": ("studying", "4,3,2"),
    "ai-tutoring-power-engineering-study": ("studying", "4,3,2"),
    "past-papers-power-engineering": ("studying", "4,3,2"),
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
    "power-engineering-exam-day": ("exam", "4,3,2"),
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
    matches = list(CANONICAL_RE.finditer(stripped))
    if len(matches) != 1:
        sys.exit(f"{slug}: expected exactly one <link rel=\"canonical\">, "
                  f"found {len(matches)} -- refusing to guess which one to "
                  "anchor the insert to")
    m = matches[0]
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
