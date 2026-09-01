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
