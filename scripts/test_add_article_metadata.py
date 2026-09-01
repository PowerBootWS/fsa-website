"""Tests for scripts/add_article_metadata.py.

Only the CANONICAL_RE anchor guard is covered here: everything else in the
module was already exercised by inference from the real 48-article run, but
the guard's failure path (zero or multiple canonical links) never was.

Run with:
    python3 -m pytest scripts/test_add_article_metadata.py -v
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import add_article_metadata as aam


def make_article(root, slug, canonical_hrefs):
    """Write a synthetic articles/<slug>/index.html under root with however
    many <link rel="canonical"> tags canonical_hrefs asks for.

    A blank line separates consecutive tags: CANONICAL_RE's capture group
    eats the newline on both sides of a match, so two tags on back-to-back
    lines share one newline and only ever count as a single match. A blank
    line between them gives each tag its own leading and trailing newline
    so both are found independently.
    """
    d = root / "articles" / slug
    d.mkdir(parents=True)
    head = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
    head += "\n".join(f'  <link rel="canonical" href="{href}">\n'
                       for href in canonical_hrefs)
    head += "</head>\n<body>\n  <h1>T</h1>\n</body>\n</html>\n"
    (d / "index.html").write_text(head)


def test_apply_exits_when_canonical_link_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(aam, "ROOT", tmp_path)
    make_article(tmp_path, "no-canonical", [])
    with pytest.raises(SystemExit) as exc:
        aam.apply("no-canonical", "studying", "4,3,2", check=True)
    msg = str(exc.value)
    assert "no-canonical" in msg
    assert "found 0" in msg


def test_apply_exits_when_canonical_link_is_duplicated(tmp_path, monkeypatch):
    monkeypatch.setattr(aam, "ROOT", tmp_path)
    make_article(tmp_path, "two-canonical",
                 ["https://fullsteamahead.ca/articles/a/",
                  "https://fullsteamahead.ca/articles/b/"])
    with pytest.raises(SystemExit) as exc:
        aam.apply("two-canonical", "studying", "4,3,2", check=True)
    msg = str(exc.value)
    assert "two-canonical" in msg
    assert "found 2" in msg


def test_apply_succeeds_with_exactly_one_canonical_link(tmp_path, monkeypatch):
    """Control case: proves the guard's failures above are about the count,
    not the fixture shape."""
    monkeypatch.setattr(aam, "ROOT", tmp_path)
    make_article(tmp_path, "one-canonical",
                 ["https://fullsteamahead.ca/articles/one-canonical/"])
    result = aam.apply("one-canonical", "studying", "4,3,2", check=True)
    assert result == "one-canonical: would update -> studying / 4,3,2"
