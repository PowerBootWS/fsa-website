#!/usr/bin/env python3
"""
FSA Article Generator
Generates article HTML using Claude Sonnet via OpenRouter and publishes it
into the fsa-website article template.

Usage:
  # Generate a single article by ID:
  python generate_article.py P1

  # Generate all articles (in strategy order):
  python generate_article.py --all

  # Generate all pillar articles only:
  python generate_article.py --pillars

  # Generate a cluster by letter:
  python generate_article.py --cluster A

  # Dry run — show the prompt without calling the API:
  python generate_article.py P1 --dry-run

Requires:
  OPENROUTER_API_KEY environment variable
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

import requests

# ─── Paths ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TEMPLATE_PATH = PROJECT_ROOT / "articles" / "_template" / "index.html"
MANIFEST_PATH = SCRIPT_DIR / "articles_manifest.json"
ARTICLES_DIR = PROJECT_ROOT / "articles"

# ─── OpenRouter config ────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path("/home/debian/projects/fsa/.env"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Writing model: default to Claude Sonnet via OpenRouter. Override with --model or OPENROUTER_MODEL env var.
WRITING_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-6")

# Research model: use the same model for simplicity. Can be overridden.
RESEARCH_MODEL = WRITING_MODEL

# ─── Unicode sanitization ────────────────────────────────────────────────────

# Replace typographic characters with safe HTML entities so articles render
# correctly regardless of browser charset detection.
UNICODE_REPLACEMENTS = [
    ("\u2014", "&mdash;"),    # em dash —
    ("\u2013", "&ndash;"),    # en dash –
    ("\u2018", "&lsquo;"),    # left single quote '
    ("\u2019", "&rsquo;"),    # right single quote '
    ("\u201c", "&ldquo;"),    # left double quote "
    ("\u201d", "&rdquo;"),    # right double quote "
    ("\u2026", "&hellip;"),   # ellipsis …
    ("\u00a0", "&nbsp;"),     # non-breaking space
    ("\u2192", "&rarr;"),     # right arrow →
    ("\u2500", "-"),          # box-drawing dash ─ (from template comments only)
]


def sanitize_unicode(html: str) -> str:
    """Replace typographic Unicode characters with safe HTML entities."""
    for char, entity in UNICODE_REPLACEMENTS:
        html = html.replace(char, entity)
    return html


# ─── Helpers ──────────────────────────────────────────────────────────────────


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def get_article(manifest: dict, article_id: str) -> dict:
    for article in manifest["articles"]:
        if article["id"] == article_id:
            return article
    raise ValueError(f"Article ID '{article_id}' not found in manifest.")


def format_date_long(date_str: str) -> str:
    """Convert YYYY-MM-DD to 'April 30, 2026'"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y")


def build_internal_links_text(internal_links: list) -> str:
    lines = []
    for link in internal_links:
        lines.append(f'  - Anchor text: "{link["anchor_text"]}" -> href="/articles/{link["slug"]}/"')
    return "\n".join(lines)


# ─── Web research step ────────────────────────────────────────────────────────

# Known facts that must be included in every exam-related article.
# Updated to reflect January 2025 SOPEEC changes.
SOPEEC_FACTS = """
VERIFIED SOPEEC 2ND CLASS EXAM FACTS (as of January 2025):
- There are six exam papers: 2A1, 2A2, 2A3, 2B1, 2B2, 2B3
- ALL six papers are 100-question multiple-choice examinations
- As of January 2025, there are NO more written/long-answer papers at the 2nd class level
  (2A1 was previously long-answer; it converted to 100-question MCQ in January 2025)
- Time allowed: most jurisdictions allow 3.5 hours per paper; some allow 3 hours
- Pass mark: 65% (65 out of 100 questions)
- Papers can be written in any order
- Each paper is passed or failed independently
- SOPEEC = Standardized Official Power Engineering Examination Committee
- Administered provincially: ABSA in Alberta, TSBC in BC, TSSA in Ontario, etc.
"""


def build_research_prompt(article: dict) -> str:
    """
    Build a prompt that asks the model to research and summarize current,
    accurate facts relevant to this article before writing begins.
    """
    return f"""You are a research assistant helping prepare accurate facts for a power engineering article.

The article is titled: "{article["title"]}"
Topic focus: {article["notes"][:400]}

TASK: Identify the key factual claims this article will need to make. For each claim type, provide:
1. What the current, accurate information is (as of 2025)
2. Any important caveats or provincial variations
3. Any common misconceptions or outdated information to avoid

Focus areas to research and summarize (only the ones relevant to this article):
- SOPEEC exam structure (papers, format, question count, time limits) — if relevant
- Pass marks and re-sit policies — if relevant
- Provincial regulatory bodies (ABSA, TSBC, TSSA) and their specific rules — if relevant
- Salary ranges for 2nd class power engineers in Canada — if relevant
- Plant classification requirements by province — if relevant
- Career progression timelines — if relevant

KNOWN VERIFIED FACTS TO INCORPORATE:
{SOPEEC_FACTS}

Return a concise factual brief (bullet points, under 400 words) that the article writer should treat as ground truth.
Do not write the article — just provide the factual foundation."""


def build_article_prompt(article: dict, research_brief: str) -> str:
    is_pillar = article["type"] == "pillar"
    word_range = "2,500–4,000" if is_pillar else "1,200–2,000"

    internal_links_text = build_internal_links_text(article["internal_links"])
    supporting_kw_text = ", ".join(article.get("supporting_keywords", []))

    prompt = f"""You are writing an SEO-optimized article for Full Steam Ahead, a 2nd class power engineering exam prep platform for Canadian operators.

AUDIENCE: 4th/3rd class certified power engineers preparing for their SOPEEC 2nd class exam. They are experienced, working operators -- skip all "what is power engineering" basics. No fluff, no padding. They read trade publications, not lifestyle blogs. Write like a knowledgeable colleague, not a content marketer.

ARTICLE DETAILS:
  Title: {article["title"]}
  Primary keyword: {article["keyword"]}
  Supporting keywords (use naturally where they fit): {supporting_kw_text}
  Target length: {word_range} words
  Category: {article["category"]}
  Type: {"Pillar (comprehensive authority guide)" if is_pillar else "Cluster article (focused, practical)"}

ANGLE / CONTENT FOCUS:
{article["notes"]}

VERIFIED FACTS -- USE THESE, DO NOT CONTRADICT THEM:
{research_brief}

INTERNAL LINKS (include each of these naturally in the article body -- use the exact anchor text and href):
{internal_links_text}

CTA MENTION (include once, near the end of the article body before the conclusion, in a natural way):
Full Steam Ahead includes a dedicated course for each of the six 2nd class papers, plus an adaptive practice exam system that tailors itself to your weak areas -- all for $149/month. Link: https://enrollment.fullsteamahead.ca

WRITING GUIDELINES:
- Direct, professional tone -- written for working power engineers
- No fluff openers like "In today's competitive industry..." or "Are you wondering..."
- Use concrete numbers, examples, and specifics wherever possible
- Short paragraphs (2-4 sentences max)
- {"Use H2 for major sections, H3 for sub-points within a section. This is a long comprehensive guide -- 5 to 8 major H2 sections expected." if is_pillar else "Use H2 for major sections, H3 for sub-points. 3 to 5 H2 sections expected."}
- Callout boxes for the most important tips or key facts: <div class="article-callout"><p>...</p></div>
- Include 1-2 callout boxes, not more
- When stating specific facts about the SOPEEC exam (paper count, question count, time limits, pass mark), use the verified facts above exactly -- do not hedge or say "typically" or "may vary" for things that are clearly defined
- For salary ranges and provincial variations, use realistic ranges and note that these vary -- do not invent precise figures

OUTPUT FORMAT -- CRITICAL:
Return ONLY the HTML for the article body. This is the content that goes inside <article class="article-body">...</article>.
- Pure HTML only -- no markdown, no code fences, no explanation text
- Do NOT include <html>, <head>, <body>, <article>, or any wrapper tags
- Do NOT include an H1 (the template handles that)
- Do NOT include a CTA button block (the template adds one)
- Start directly with a short lead-in <p> or the first <h2>
- Valid HTML tags to use: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <a href="...">, <div class="article-callout">
- Use only straight ASCII apostrophes and quotes in HTML -- do NOT use curly/smart quotes or typographic dashes; use hyphens (-) for dashes in text, or HTML entities (&mdash; &ndash;) if needed
"""
    return prompt.strip()


def build_meta_description_prompt(article: dict) -> str:
    return f"""Write a meta description for this article. Requirements:
- Exactly 140-160 characters
- Includes the primary keyword: "{article["keyword"]}"
- Factual and specific -- no marketing fluff
- Written for someone searching this topic on Google
- Do NOT start with the site name
- Use only straight ASCII characters -- no curly quotes, no em dashes

Article title: {article["title"]}
Article focus: {article["notes"][:300]}

Return ONLY the meta description text -- no quotes, no label, no explanation."""


# ─── API call ─────────────────────────────────────────────────────────────────

def call_openrouter(prompt: str, model: str, max_tokens: int = 4096, reasoning: bool = False) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable is not set.\n"
            "Export it with: export OPENROUTER_API_KEY=your_key_here"
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fullsteamahead.ca",
        "X-Title": "FSA Article Generator",
    }

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    if reasoning:
        payload["reasoning"] = {"effort": "high"}

    response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=180)
    response.raise_for_status()

    data = response.json()
    message = data["choices"][0]["message"]
    content = message.get("content")
    if content is None:
        # Some reasoning models may return reasoning text when content is empty
        reasoning_text = message.get("reasoning", "")
        if reasoning_text:
            content = reasoning_text
        else:
            raise RuntimeError("API returned empty content and no reasoning text.")
    return content.strip()


def clean_html_response(raw: str) -> str:
    """Strip markdown code fences if the model wrapped the output."""
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n', '', raw)
    raw = re.sub(r'\n```$', '', raw)
    return raw.strip()


def strip_template_comment(html: str) -> str:
    """Remove the developer instruction comment block at the top of the template.
    The block contains a nested <!-- --> which breaks HTML parsing, causing
    browsers to treat the field list as visible document text."""
    return re.sub(r'(<!DOCTYPE html>)\s*<!--.*?-->\s*(<html)', r'\1\n\2', html, count=1, flags=re.DOTALL)


# ─── Template filling ─────────────────────────────────────────────────────────

def build_related_cards_html(related_cards: list) -> str:
    cards_html = []
    for card in related_cards:
        cards_html.append(f"""        <a href="/articles/{card["slug"]}/" class="article-card">
          <div class="article-card-tag">{card["category"]}</div>
          <h3>{card["title"]}</h3>
          <p>{card["description"]}</p>
          <span class="article-card-read">Read &rarr;</span>
        </a>""")
    return "\n\n".join(cards_html)


def fill_template(template: str, article: dict, body_html: str, meta_description: str) -> str:
    # Remove the developer instruction comment block which contains a nested
    # <!-- --> and causes browsers to expose the field list as visible text.
    template = strip_template_comment(template)

    slug = article["slug"]
    title = article["title"]
    category = article["category"]
    date_str = article["published_date"]
    date_long = format_date_long(date_str)
    canonical_url = f"https://www.fullsteamahead.ca/articles/{slug}/"
    pillar = article["breadcrumb"]
    intro = article["intro"]

    # Title tag
    html = template.replace(
        "<title>Article Title \u2013 Full Steam Ahead</title>",
        f"<title>{title} &ndash; Full Steam Ahead</title>"
    )

    # Meta description
    html = html.replace(
        '<meta name="description" content="REPLACE: article description.">',
        f'<meta name="description" content="{meta_description}">'
    )

    # Canonical — replace all occurrences of SLUG in URLs
    html = html.replace(
        'href="https://www.fullsteamahead.ca/articles/SLUG/"',
        f'href="{canonical_url}"'
    )
    html = html.replace(
        'content="https://www.fullsteamahead.ca/articles/SLUG/"',
        f'content="{canonical_url}"'
    )
    html = html.replace(
        '"url": "https://www.fullsteamahead.ca/articles/SLUG/"',
        f'"url": "{canonical_url}"'
    )

    # OG title
    html = html.replace(
        '<meta property="og:title" content="REPLACE: Article Title \u2013 Full Steam Ahead">',
        f'<meta property="og:title" content="{title} &ndash; Full Steam Ahead">'
    )

    # OG description
    html = html.replace(
        '<meta property="og:description" content="REPLACE: article description.">',
        f'<meta property="og:description" content="{meta_description}">'
    )

    # OG url
    html = html.replace(
        '<meta property="og:url" content="https://www.fullsteamahead.ca/articles/SLUG/">',
        f'<meta property="og:url" content="{canonical_url}">'
    )

    # JSON-LD headline
    html = html.replace(
        '"headline": "REPLACE: Article headline (same as H1, max 110 chars)"',
        f'"headline": "{title}"'
    )

    # JSON-LD description
    html = html.replace(
        '"description": "REPLACE: article description"',
        f'"description": "{meta_description}"'
    )

    # JSON-LD datePublished
    html = html.replace(
        '"datePublished": "REPLACE: YYYY-MM-DD"',
        f'"datePublished": "{date_str}"'
    )

    # JSON-LD dateModified
    html = html.replace(
        '"dateModified": "REPLACE: YYYY-MM-DD"',
        f'"dateModified": "{date_str}"'
    )

    # JSON-LD breadcrumb position 3 (pillar)
    html = html.replace(
        '{ "@type": "ListItem", "position": 3, "name": "REPLACE: Pillar name", "item": "https://www.fullsteamahead.ca/articles/PILLAR-SLUG/" }',
        f'{{ "@type": "ListItem", "position": 3, "name": "{pillar["pillar_name"]}", "item": "https://www.fullsteamahead.ca/articles/{pillar["pillar_slug"]}/" }}'
    )

    # JSON-LD breadcrumb position 4 (article)
    html = html.replace(
        '{ "@type": "ListItem", "position": 4, "name": "REPLACE: Article title", "item": "https://www.fullsteamahead.ca/articles/SLUG/" }',
        f'{{ "@type": "ListItem", "position": 4, "name": "{title}", "item": "{canonical_url}" }}'
    )

    # HTML breadcrumb nav
    html = html.replace(
        '<a href="/">Home</a> / <a href="/articles/">Guides</a> / <a href="/articles/PILLAR-SLUG/">REPLACE: Pillar Name</a> / REPLACE: Article Short Title',
        f'<a href="/">Home</a> / <a href="/articles/">Guides</a> / <a href="/articles/{pillar["pillar_slug"]}/">{pillar["pillar_name"]}</a> / {pillar["article_short_title"]}'
    )

    # Category tag
    html = html.replace(
        '<span class="article-meta-tag">REPLACE: Category</span>',
        f'<span class="article-meta-tag">{category}</span>'
    )

    # Published date
    html = html.replace(
        '<span class="article-meta-date">Published REPLACE: Month DD, YYYY</span>',
        f'<span class="article-meta-date">Published {date_long}</span>'
    )

    # H1
    html = html.replace(
        "<h1>REPLACE: Article Title</h1>",
        f"<h1>{title}</h1>"
    )

    # Intro paragraph
    html = html.replace(
        '<p class="article-intro">REPLACE: Brief intro paragraph visible in the page header \u2014 sets context, includes primary keyword naturally.</p>',
        f'<p class="article-intro">{intro}</p>'
    )

    # Article body
    html = html.replace(
        "      <p>REPLACE: Article body content.</p>",
        f"      {body_html}"
    )

    # Related articles
    related_html = build_related_cards_html(article["related_cards"])
    html = html.replace(
        """        <a href="/articles/RELATED-SLUG-1/" class="article-card">
          <div class="article-card-tag">REPLACE: Category</div>
          <h3>REPLACE: Related Article Title 1</h3>
          <p>REPLACE: One-line description.</p>
          <span class="article-card-read">Read \u2192</span>
        </a>

        <a href="/articles/RELATED-SLUG-2/" class="article-card">
          <div class="article-card-tag">REPLACE: Category</div>
          <h3>REPLACE: Related Article Title 2</h3>
          <p>REPLACE: One-line description.</p>
          <span class="article-card-read">Read \u2192</span>
        </a>""",
        related_html
    )

    # Final pass: sanitize any remaining Unicode typographic characters
    html = sanitize_unicode(html)

    return html


# ─── Main generation ──────────────────────────────────────────────────────────

def generate_article(article: dict, dry_run: bool = False, model: str = WRITING_MODEL, reasoning: bool = False) -> None:
    article_id = article["id"]
    slug = article["slug"]
    output_dir = ARTICLES_DIR / slug
    output_path = output_dir / "index.html"

    print(f"\n{'='*60}")
    print(f"Article: {article_id} -- {article['title']}")
    print(f"Slug:    {slug}")
    print(f"Output:  {output_path}")
    print(f"Model:   {model}")
    print(f"Reasoning: {reasoning}")
    print(f"{'='*60}")

    # Step 1: Research brief
    research_prompt = build_research_prompt(article)

    if dry_run:
        article_prompt = build_article_prompt(article, "[research brief would go here]")
        meta_prompt = build_meta_description_prompt(article)
        print("\n--- RESEARCH PROMPT (dry run) ---")
        print(research_prompt)
        print("\n--- ARTICLE PROMPT (dry run) ---")
        print(article_prompt)
        print("\n--- META DESCRIPTION PROMPT (dry run) ---")
        print(meta_prompt)
        return

    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Step 1: Get research brief
    print(f"\nStep 1/3: Researching facts via {model}...")
    research_brief = call_openrouter(research_prompt, model=model, max_tokens=800, reasoning=reasoning)
    print(f"Research brief: {len(research_brief)} chars")
    print("---")
    print(research_brief[:500] + ("..." if len(research_brief) > 500 else ""))
    print("---")

    # Step 2: Generate article body
    article_prompt = build_article_prompt(article, research_brief)
    print(f"\nStep 2/3: Generating article body via {model}...")
    body_raw = call_openrouter(article_prompt, model=model, max_tokens=6000, reasoning=reasoning)
    body_html = clean_html_response(body_raw)
    print(f"Body received: {len(body_html)} characters")

    # Step 3: Generate meta description
    meta_prompt = build_meta_description_prompt(article)
    print("\nStep 3/3: Generating meta description...")
    meta_raw = call_openrouter(meta_prompt, model=model, max_tokens=200, reasoning=reasoning)
    meta_description = meta_raw.strip().strip('"')
    if len(meta_description) > 160:
        meta_description = meta_description[:157] + "..."
    print(f"Meta ({len(meta_description)} chars): {meta_description}")

    # Fill template
    print("\nFilling template...")
    filled_html = fill_template(template, article, body_html, meta_description)

    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(filled_html, encoding="utf-8")
    print(f"Written to: {output_path}")

    # SEO checklist
    html_no_comments = re.sub(r'<!--.*?-->', '', filled_html, flags=re.DOTALL)
    print("\nSEO checklist:")
    checks = [
        ("REPLACE" not in html_no_comments.split("<title>")[1].split("</title>")[0], "Title tag"),
        ('meta name="description"' in filled_html and "REPLACE" not in filled_html.split('meta name="description"')[1].split(">")[0], "Meta description"),
        ('rel="canonical"' in filled_html, "Canonical URL"),
        ('og:title' in filled_html, "OG title"),
        ('datePublished' in filled_html, "JSON-LD datePublished"),
        ("REPLACE" not in html_no_comments, "No remaining REPLACE placeholders"),
        # Check no raw typographic unicode remains in the body
        ("\u2014" not in filled_html and "\u2013" not in filled_html, "No raw Unicode dashes"),
    ]
    all_pass = True
    for passed, label in checks:
        status = "+" if passed else "!"
        print(f"  [{status}] {label}")
        if not passed:
            all_pass = False

    if not all_pass:
        print("\nWARNING: Some checks failed -- review the output file.")
    else:
        print("\nAll checks passed.")


def main():
    parser = argparse.ArgumentParser(description="FSA Article Generator")
    parser.add_argument("article_id", nargs="?", help="Article ID (e.g. P1, A3, B5)")
    parser.add_argument("--all", action="store_true", help="Generate all articles in strategy order")
    parser.add_argument("--pillars", action="store_true", help="Generate pillar articles only")
    parser.add_argument("--cluster", choices=["A", "B", "C", "D"], help="Generate all articles in a cluster")
    parser.add_argument("--model", default=None, help="Override writing/research model (default: OPENROUTER_MODEL env var or anthropic/claude-sonnet-4-6)")
    parser.add_argument("--reasoning", action="store_true", help="Enable reasoning mode (model-dependent, e.g. moonshotai/kimi-k2.6)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling the API")
    args = parser.parse_args()

    manifest = load_manifest()
    articles = manifest["articles"]

    model = args.model or WRITING_MODEL

    strategy_order = [
        "P1", "P2", "P3", "P4",
        "A1", "A2", "A3", "A4", "A5", "A6", "A7",
        "B1", "B2", "B3", "B4", "B5", "B6", "B7",
        "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9",
        "D1", "D2", "D3", "D4", "D5",
    ]

    if args.all:
        targets = [get_article(manifest, aid) for aid in strategy_order]
    elif args.pillars:
        targets = [get_article(manifest, aid) for aid in ["P1", "P2", "P3", "P4"]]
    elif args.cluster:
        targets = [a for a in articles if a["id"].startswith(args.cluster)]
    elif args.article_id:
        targets = [get_article(manifest, args.article_id)]
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Generating {len(targets)} article(s)...")
    for article in targets:
        generate_article(article, dry_run=args.dry_run, model=model, reasoning=args.reasoning)

    print(f"\nDone. {len(targets)} article(s) processed.")
    if not args.dry_run:
        print("\nNext steps:")
        print("  1. Review generated files in articles/")
        print("  2. git add articles/<slug>/")
        print("  3. git commit -m 'Publish articles: ...'")
        print("  4. git push origin main")
        print("  5. docker compose -f docker-compose.yml up -d --build")


if __name__ == "__main__":
    main()
