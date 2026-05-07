---
name: fsa-website-deploy
description: Author content and deploy the Full Steam Ahead static website. Use when publishing new articles, updating pages, or deploying any file change — including adding/removing HTML pages, styles, assets, or articles. Orchestrates content authoring, git commit and push, Docker container rebuild, sitemap maintenance, Google Search Console registration, and Cloudflare cache purging in the correct order.
---

# FSA Website: Author & Deploy

Covers everything needed to write, publish, and deploy content on the Full Steam Ahead website.

**Project root:** `/home/debian/projects/fsa/fsa-website/`
**Git remote:** `https://github.com/PowerBootWS/fsa-website.git` (branch: `master`)
**Docker container:** `fsa-website` (port `8087:80`, nginx:alpine)
**Live routing:** Nginx serves `index.html` as the site root (`/`)

---

## When to Use

- Publishing a new article or updating existing articles
- Updating any page — homepage, affiliate, legal, testimonials, CTAs
- Any file in `fsa-website/` has been added, removed, or modified
- The sitemap needs updating to reflect new or removed pages
- A full end-to-end publish (git → Docker → Google → Cloudflare) is required

---

## Preconditions

- Working directory: `/home/debian/projects/fsa/fsa-website/`
- Docker and docker-compose available
- Centralized `.env` at `/home/debian/projects/fsa/.env` contains `CF_ZONE_ID` and `CF_API_TOKEN`
- Google Search Console OAuth token exists at `scripts/google_token.json`
- Git remote configured for `origin/master`

---

## Directory Structure

```
fsa-website/
├── index.html              # Full homepage (current)
├── home-v2.html            # Legacy homepage (do not edit)
├── affiliate.html          # Affiliate page
├── privacy-policy.html
├── terms-of-use.html
├── styles.css              # Legacy v1 styles (do not use for new work)
├── styles-v2.css           # Current v2 styles (use this)
├── assets/                 # Images, logos, favicon
│   ├── favicon.png
│   └── FSA Logo Main - Light.png
├── articles/
│   ├── index.html          # Article hub ("Power Engineering Guides" landing)
│   ├── articles.css        # Article-specific styles (included on all articles)
│   └── _template/
│       └── index.html      # Article template — copy this for new articles
├── nginx.conf
├── Dockerfile
└── docker-compose.yml
```

---

## Stylesheets

| File | Use for |
|---|---|
| `styles-v2.css` | All pages — homepage, legal, affiliate, article hub |
| `articles/articles.css` | All article pages (include alongside styles-v2.css) |
| `styles.css` | Legacy only — do not use for new work |

---

## Content Strategy Reference

Before writing any article, consult these two documents:

- **Content strategy & plan** (pillar, slug, target keyword, internal links, generation order):
  `/home/debian/.claude/plans/cheeky-seeking-starlight.md`
- **SEO keyword reference** (supporting keywords, long-tail terms, LSI phrases):
  `/home/debian/projects/fsa/fsa-marketing/seo-keywords.md`

---

## Publishing a New Article

### Step 1 — Create the article folder

```bash
cp -r /home/debian/projects/fsa/fsa-website/articles/_template \
      /home/debian/projects/fsa/fsa-website/articles/[slug]
```

Slug convention: lowercase, hyphenated (e.g. `power-engineering-exam-prep`)

### Step 2 — Fill in the template

Open `articles/[slug]/index.html` and replace all `<!-- REPLACE -->` placeholders:

- `<title>` — article title + " | Full Steam Ahead"
- `<meta name="description">` — 150–160 character summary
- `<link rel="canonical">` — `https://fullsteamahead.ca/articles/[slug]/`
- OG tags (`og:title`, `og:description`, `og:url`, `og:image`)
- JSON-LD schema: `datePublished`, `dateModified`, `headline`, `description`
- Breadcrumb nav text
- Article metadata: category, publish date, read time
- `.article-body` — article content (h2/h3, p, ul, callout divs)
- Related articles section — 3 card links to other articles
- Bottom CTA if relevant

### Step 3 — Add the article card to the hub

Open `articles/index.html` and add a card in the article grid following the existing card pattern. Include: title, excerpt, category tag, read time, and link to `/articles/[slug]/`.

---

## Updating Existing Pages

- **Homepage** (`index.html`) — testimonials, hero copy, feature sections, CTAs
- **Affiliate page** (`affiliate.html`) — affiliate program details
- **Legal pages** — `privacy-policy.html`, `terms-of-use.html`

Navigation is duplicated across all pages (no include mechanism). If nav changes, update each page individually.

---

## Notes

- No CMS, no build step, no templating engine — pure HTML/CSS
- Google Analytics (gtag.js) is included inline on article pages — don't remove it
- Fonts: Google Fonts (Barlow, Barlow Condensed) — preconnect tags are in `<head>`
- External network `cloudflare` is used by Docker — do not remove from `docker-compose.yml`

---

## SEO Checklist (for new articles)

- [ ] Unique `<title>` (50–60 chars)
- [ ] Unique `<meta name="description">` (150–160 chars)
- [ ] Canonical URL set correctly
- [ ] OG tags filled in (title, description, url, image)
- [ ] JSON-LD schema: `datePublished`, `dateModified`, `headline`
- [ ] Article added to hub page (`articles/index.html`)
- [ ] Sitemap updated (`sitemap.xml`) if adding new root-level pages

---

## Deploy Workflow

Run steps in order. Do not skip steps unless the user explicitly says so.

### 1. Inspect Changes

```bash
git -C /home/debian/projects/fsa/fsa-website/ status
git -C /home/debian/projects/fsa/fsa-website/ diff --stat
```

Identify:
- New `.html` pages added to the repo root
- Any `.html` pages removed from the repo root
- Modified files (styles, content, assets)

### 2. Update Sitemap (if pages added/removed)

If new root-level `.html` pages were added or removed, update `sitemap.xml` before committing.

Rules:
- Add a `<url>` block for each new root-level `.html` page
- Remove `<url>` blocks for deleted root-level `.html` pages
- Set `<lastmod>` to today's date (`YYYY-MM-DD`) for changed entries
- Use these defaults for new pages:
  - `changefreq`: `monthly` (use `daily` for frequently-updated pages like job boards)
  - `priority`: `0.5` for utility pages, `0.7` for high-traffic/new features, `1.0` for homepage
- Update the homepage `<lastmod>` to today's date on every deploy
- Articles inside `articles/` are **not** tracked individually in the sitemap (only the `articles/` hub is listed)

After editing, validate the XML is well-formed.

### 3. Commit and Push

Stage only the files that actually changed (do not use `git add -A`):

```bash
git -C /home/debian/projects/fsa/fsa-website/ add <file1> <file2> ...
git -C /home/debian/projects/fsa/fsa-website/ commit -m "<concise message>"
git -C /home/debian/projects/fsa/fsa-website/ push origin master
```

### 4. Rebuild Docker Container

Build a fresh image and recreate the container:

```bash
docker compose -f /home/debian/projects/fsa/fsa-website/docker-compose.yml build --no-cache
docker rm -f fsa-website
docker compose -f /home/debian/projects/fsa/fsa-website/docker-compose.yml up -d
```

Verify it is running:

```bash
docker ps --filter "name=fsa-website" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

The site is live within ~1–2 minutes of the Docker rebuild completing.

### 5. Submit Sitemap to Google Search Console

Run the submission script. Use `--sitemap-only` if only the sitemap was updated; omit the flag to also request indexing for all known URLs.

```bash
python3 /home/debian/projects/fsa/fsa-website/scripts/submit_to_google.py --sitemap-only
```

If the OAuth token is expired or missing, the script will open a browser flow on port `8888` and save a new token to `scripts/google_token.json`.

### 6. Purge Cloudflare Cache

Always run this last so visitors see the latest content immediately:

```bash
bash /home/debian/projects/fsa/fsa-website/scripts/purge_cloudflare.sh
```

Credentials (`CF_ZONE_ID`, `CF_API_TOKEN`) are read automatically from the centralized `.env` at `/home/debian/projects/fsa/.env`.

**Always run the Cloudflare purge after every rebuild.** Without it, visitors (especially on mobile) may see stale cached versions of pages for hours.

---

## One-Shot Deploy Script

For hands-free deployments, execute the bundled script:

```bash
bash /home/debian/projects/fsa/fsa-website/skills/fsa-website-deploy/scripts/deploy.sh
```

The script performs the full workflow: inspect → sitemap update (interactive) → commit/push → Docker rebuild → Google sitemap submit → Cloudflare purge.
