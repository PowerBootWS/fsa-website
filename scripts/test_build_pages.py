"""Tests for scripts/build_pages.py.

First test file in this repo. Run with:
    python3 -m pytest scripts/test_build_pages.py -v
"""
import pathlib
import re
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
    art = bp.parse_article("s", article_html(levels="2,4,3"))
    assert art.levels == ["2", "4", "3"]


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


def test_render_level_nav_avoids_the_bare_nav_element():
    """styles-v2.css has a global `nav { position: fixed; ... }` rule that would
    yank this out of flow and cover the site nav. Use a div with role=navigation."""
    out = bp.render_level_nav("4")
    assert "<nav" not in out
    assert 'role="navigation"' in out


ANCHOR_HREF_RE = re.compile(r'href="#([^"]+)"')
ID_ATTR_RE = re.compile(r'\bid="([^"]+)"')


def test_generated_hub_in_page_anchors_resolve_to_a_real_id(built):
    """Generic on purpose: the defect class is 'a hand-written #anchor drifts
    from the generated ids', not any specific anchor. This must catch the next
    one too, e.g. if a STAGES key is ever renamed again."""
    for rel in HUB_RELS:
        html = (built / rel).read_text()
        ids = set(ID_ATTR_RE.findall(html))
        anchors = set(ANCHOR_HREF_RE.findall(html))
        dangling = sorted(a for a in anchors if a not in ids)
        assert not dangling, f"{rel}: anchor(s) {dangling} have no matching id=... on the page"


CARD_COUNTS = {
    "articles/index.html": 48,
    "articles/4th-class/index.html": 31,
    "articles/3rd-class/index.html": 34,
    "articles/2nd-class/index.html": 45,
}


def test_generated_hub_card_counts_match_the_spec(built):
    for rel, expected in CARD_COUNTS.items():
        html = (built / rel).read_text()
        actual = html.count('class="article-card"')
        assert actual == expected, f"{rel}: expected {expected} cards, found {actual}"


def test_generated_3rd_class_hub_excludes_other_levels(built):
    html = (built / "articles/3rd-class/index.html").read_text()
    # A 4th-Class-only article must not appear on the 3rd Class hub.
    assert 'href="/articles/how-to-become-a-4th-class-power-engineer/"' not in html
    # A 2nd-Class-only article must not appear either.
    assert 'href="/articles/sopeec-2a1-exam-guide/"' not in html
    # A level-agnostic one must.
    assert 'href="/articles/sopeec-multiple-choice-traps/"' in html


def test_generated_2nd_class_hub_excludes_other_levels(built):
    html = (built / "articles/2nd-class/index.html").read_text()
    # A 4th-Class-only article must not appear on the 2nd Class hub.
    assert 'href="/articles/how-to-become-a-4th-class-power-engineer/"' not in html
    # A level-agnostic one must.
    assert 'href="/articles/sopeec-multiple-choice-traps/"' in html


def test_generated_hub_h1_placeholder_is_substituted(built):
    """Plumbing check only: confirms {{H1}} in the template actually gets
    replaced with the value build() reads out of HUB_PAGES for that page. It
    reads its expectation from the same HUB_PAGES list build() renders from,
    so it cannot catch a wrong value in HUB_PAGES itself -- see
    test_generated_hub_h1_matches_the_expected_level below for that."""
    for level, rel, title, h1, intro in bp.HUB_PAGES:
        html = (built / rel).read_text()
        assert f"<h1>{h1}</h1>" in html, f"{rel}: expected h1 '{h1}' not found"


HUB_H1 = {
    "articles/index.html": "Power Engineering Guides",
    "articles/4th-class/index.html": "Guides for 4th Class",
    "articles/3rd-class/index.html": "Guides for 3rd Class",
    "articles/2nd-class/index.html": "Guides for 2nd Class",
}


def test_generated_hub_h1_matches_the_expected_level(built):
    """Independent oracle, deliberately not read from HUB_PAGES: swapping two
    levels' h1 strings inside HUB_PAGES itself would make build() and the
    plumbing test above agree on the wrong value. This literal map is the
    only thing in the suite that knows what each page's h1 SHOULD say."""
    for rel, expected_h1 in HUB_H1.items():
        html = (built / rel).read_text()
        assert f"<h1>{expected_h1}</h1>" in html, \
            f"{rel}: expected h1 '{expected_h1}' not found"


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
