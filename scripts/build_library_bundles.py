#!/usr/bin/env python3
"""
Build the 4th Class "whole part" zip bundles for the free library.

Why this exists
---------------
2nd and 3rd Class map one book to one paper: someone writing 2A1 downloads 2A1
and is done. 4th Class does not work that way. Each part is a single paper
broken into twelve units, so sitting Paper 4A means twelve separate downloads,
one click each, on a page where roughly two thirds of visitors are on a phone.
These bundles collapse that into one download per paper. The individual unit
downloads stay exactly where they are; this is an addition, never a replacement.

Where the file list comes from
------------------------------
`library.html`, not the filesystem. The page is the source of truth for which
unit is which and what it is called, and parsing it means the bundle contents
and the page can never drift apart. It also means the files *inside* the zip get
their real names -- "Unit A-01 - Elementary Mechanics and Dynamics.pdf" rather
than "PowerEngineering_FourthClassA_Book1_E35.pdf" -- which is most of the value
of bundling in the first place. Unit numbers are zero-padded so an unzipped
folder sorts in syllabus order instead of 1, 10, 11, 12, 2.

Two things worth knowing before changing this
---------------------------------------------
* **The bundles are build artefacts, not source.** Like the PDFs themselves they
  live only on the server's disk under `assets/library/`, are excluded by
  `.gitignore` and `.dockerignore`, and reach nginx through the bind-mount in
  `docker-compose.yml`. A fresh clone will not have them; re-run this script.
* **Deflate buys about 4%.** PDFs are already compressed, so this is close to a
  no-op -- measured at 96.2% of original on the largest unit. It is kept only
  because it is a one-time cost against many downloads. Do not reach for a
  stronger algorithm expecting a real win; there isn't one.

A README carrying the CC BY-NC-SA attribution goes inside each bundle. The
licence requires attribution, and a zip travels away from the page that carries
it, so the notice has to travel with the files.

Usage:  python3 scripts/build_library_bundles.py [--check]
        --check verifies the existing bundles without rebuilding them.
"""

import argparse
import datetime
import html
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBRARY_HTML = ROOT / "library.html"
ASSETS = ROOT / "assets" / "library"

PARTS = {
    "A": {
        "zip": "PowerEngineering_FourthClassA_AllUnits_E35.zip",
        "folder": "4th Class Part A (Paper 4A)",
        "label": "Paper 4A",
    },
    "B": {
        "zip": "PowerEngineering_FourthClassB_AllUnits_E35.zip",
        "folder": "4th Class Part B (Paper 4B)",
        "label": "Paper 4B",
    },
}

README = """\
4TH CLASS POWER ENGINEERING - {label}
{underline}

{count} units, complete. Edition 3.5.

ATTRIBUTION AND LICENCE
-----------------------
This material has been made available by the Northern Alberta Institute of
Technology (NAIT), the Southern Alberta Institute of Technology (SAIT), and the
British Columbia Institute of Technology (BCIT).

It is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International (CC BY-NC-SA 4.0):
    https://creativecommons.org/licenses/by-nc-sa/4.0/

The full licence terms and acknowledgement also appear in the preface of each
book. These are the former PanGlobal learning materials; PanGlobal ceased
operations on 30 June 2025 and the three institutes released the complete set
free to the public.

The files in this archive are unmodified.

WHERE THIS CAME FROM
--------------------
Full Steam Ahead redistributes these files free of charge and without sign-up,
in keeping with the licence. The complete 2nd, 3rd and 4th Class set, plus the
official SOPEEC and ABSA exam syllabi:

    https://fullsteamahead.ca/library

CONTENTS
--------
{contents}

Bundle generated {date}.
"""


def parse_units(part: str):
    """Pull (unit, title, filename) for one 4th Class part out of library.html."""
    page = LIBRARY_HTML.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<div class="chapter-unit">Unit ' + part + r'-(\d+)</div>\s*'
        r'<div class="chapter-title">([^<]*)</div>.*?'
        r'href="/assets/library/([^"]+\.pdf)"',
        re.S,
    )
    units = [
        (int(n), html.unescape(title).strip(), fname)
        for n, title, fname in pattern.findall(page)
    ]
    if not units:
        sys.exit(f"error: found no Part {part} units in {LIBRARY_HTML.name}")
    units.sort(key=lambda u: u[0])

    seen = [u[0] for u in units]
    if seen != list(range(1, len(seen) + 1)):
        sys.exit(f"error: Part {part} unit numbers are not contiguous: {seen}")
    return units


def safe_name(unit_no: int, part: str, title: str) -> str:
    """'Unit A-01 - Elementary Mechanics and Dynamics.pdf', filesystem-safe."""
    clean = re.sub(r'[<>:"/\\|?*]', "-", title).strip()
    return f"Unit {part}-{unit_no:02d} - {clean}.pdf"


def build(part: str) -> pathlib.Path:
    spec = PARTS[part]
    units = parse_units(part)
    out = ASSETS / spec["zip"]

    missing = [f for _, _, f in units if not (ASSETS / f).is_file()]
    if missing:
        sys.exit("error: source PDFs missing from assets/library:\n  " + "\n  ".join(missing))

    contents = "\n".join(
        f"  {safe_name(n, part, t)}" for n, t, _ in units
    )
    readme = README.format(
        label=spec["label"],
        underline="=" * (len("4TH CLASS POWER ENGINEERING - ") + len(spec["label"])),
        count=len(units),
        contents=contents,
        date=datetime.date.today().isoformat(),
    )

    # Write to a temp name and move into place, so a crashed run can never leave
    # a half-written zip being served to somebody.
    tmp = out.with_suffix(".zip.partial")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr(f"{spec['folder']}/README.txt", readme)
        for n, title, fname in units:
            z.write(ASSETS / fname, f"{spec['folder']}/{safe_name(n, part, title)}")
    tmp.replace(out)

    src_total = sum((ASSETS / f).stat().st_size for _, _, f in units)
    size = out.stat().st_size
    print(
        f"  {spec['zip']}: {len(units)} units, "
        f"{size / 1024 / 1024:.0f} MB (sources {src_total / 1024 / 1024:.0f} MB, "
        f"{size / src_total * 100:.1f}%)"
    )
    return out


def check(part: str) -> bool:
    spec = PARTS[part]
    out = ASSETS / spec["zip"]
    if not out.is_file():
        print(f"  {spec['zip']}: MISSING")
        return False
    units = parse_units(part)
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        if bad:
            print(f"  {spec['zip']}: CORRUPT entry {bad}")
            return False
        names = z.namelist()
    expected = {f"{spec['folder']}/{safe_name(n, part, t)}" for n, t, _ in units}
    expected.add(f"{spec['folder']}/README.txt")
    if set(names) != expected:
        print(f"  {spec['zip']}: STALE - contents no longer match library.html")
        for extra in sorted(set(names) - expected):
            print(f"      unexpected: {extra}")
        for gone in sorted(expected - set(names)):
            print(f"      missing:    {gone}")
        return False
    print(f"  {spec['zip']}: OK, {len(names)} entries, "
          f"{out.stat().st_size / 1024 / 1024:.0f} MB")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify existing bundles instead of rebuilding")
    args = ap.parse_args()

    if args.check:
        print("Checking 4th Class bundles:")
        sys.exit(0 if all([check(p) for p in PARTS]) else 1)

    print("Building 4th Class bundles:")
    for part in PARTS:
        build(part)
    print("Done. These are build artefacts on this host only "
          "(gitignored, dockerignored, served via the bind-mount).")


if __name__ == "__main__":
    main()
