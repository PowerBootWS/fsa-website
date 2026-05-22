# Account Dropdown Nav — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the "Account" nav link on all 41 pages into an accessible hover/click dropdown with "Learning Platform" and "Manage Subscription" sub-links.

**Architecture:** CSS handles the visual dropdown reveal on hover; a new shared `/nav.js` manages ARIA state, keyboard navigation, and click-outside dismissal. A Python script does the bulk HTML replacement across all 41 files in one pass.

**Tech Stack:** Vanilla HTML/CSS/JS, Python 3 (for bulk update script), static nginx site

---

### Task 1: Add dropdown CSS to `styles-v2.css`

**Files:**
- Modify: `fsa-website/styles-v2.css` (after line 160, after `.nav-links a:hover` rule)

- [ ] **Step 1: Insert the dropdown CSS block**

Open `fsa-website/styles-v2.css`. Find the line:
```css
.nav-links a:hover { color: var(--white); }
```
Insert the following block immediately after it (leave a blank line before the existing `.nav-cta` rule that follows):

```css
/* ── ACCOUNT DROPDOWN ── */
.nav-dropdown { position: relative; }

.nav-dropdown-trigger {
  background: none;
  border: none;
  padding: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.03em;
  color: var(--gray-light);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  transition: color var(--duration-fast);
}
.nav-dropdown-trigger:hover,
.nav-dropdown:hover .nav-dropdown-trigger { color: var(--white); }

.nav-dropdown-arrow {
  font-size: 0.7rem;
  transition: transform var(--duration-fast);
}
.nav-dropdown-trigger[aria-expanded="true"] .nav-dropdown-arrow {
  transform: rotate(180deg);
}

.nav-dropdown-menu {
  position: absolute;
  top: calc(100% + 0.75rem);
  right: 0;
  min-width: 200px;
  list-style: none;
  background: var(--iron);
  border: 1px solid var(--plate-edge);
  border-top: 2px solid var(--orange);
  border-radius: 4px;
  padding: 0.4rem 0;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-6px);
  transition: opacity var(--duration-fast), transform var(--duration-fast), visibility var(--duration-fast);
  z-index: 200;
}
.nav-dropdown:hover .nav-dropdown-menu,
.nav-dropdown-menu.is-open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.nav-dropdown-menu a {
  display: block;
  padding: 0.55rem 1.1rem;
  color: var(--gray-light);
  text-decoration: none;
  font-size: 0.875rem;
  white-space: nowrap;
  transition: color var(--duration-fast), background var(--duration-fast);
}
.nav-dropdown-menu a:hover,
.nav-dropdown-menu a:focus {
  color: var(--white);
  background: var(--plate);
  outline: none;
}
```

- [ ] **Step 2: Verify no syntax errors**

```bash
grep -c "nav-dropdown" /home/debian/projects/fsa/fsa-website/styles-v2.css
```
Expected output: `12` (12 occurrences of "nav-dropdown" in the file)

- [ ] **Step 3: Commit**

```bash
cd /home/debian/projects/fsa/fsa-website
git add styles-v2.css
git commit -m "feat: add account dropdown CSS"
```

---

### Task 2: Create `/nav.js`

**Files:**
- Create: `fsa-website/nav.js`

- [ ] **Step 1: Create the file**

Create `/home/debian/projects/fsa/fsa-website/nav.js` with this exact content:

```js
(function () {
  function initDropdowns() {
    document.querySelectorAll('.nav-dropdown').forEach(function (dropdown) {
      var trigger = dropdown.querySelector('.nav-dropdown-trigger');
      var menu = dropdown.querySelector('.nav-dropdown-menu');
      if (!trigger || !menu) return;
      var items = Array.from(menu.querySelectorAll('a[role="menuitem"]'));

      function open() {
        trigger.setAttribute('aria-expanded', 'true');
        menu.classList.add('is-open');
      }
      function close() {
        trigger.setAttribute('aria-expanded', 'false');
        menu.classList.remove('is-open');
      }
      function toggle() {
        trigger.getAttribute('aria-expanded') === 'true' ? close() : open();
      }

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        toggle();
      });

      trigger.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
        if (e.key === 'ArrowDown') { e.preventDefault(); open(); if (items[0]) items[0].focus(); }
        if (e.key === 'Escape') { close(); trigger.focus(); }
      });

      menu.addEventListener('keydown', function (e) {
        var idx = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') { e.preventDefault(); if (items[idx + 1]) items[idx + 1].focus(); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); idx > 0 ? items[idx - 1].focus() : trigger.focus(); }
        if (e.key === 'Escape')    { close(); trigger.focus(); }
      });

      dropdown.addEventListener('mouseenter', function () { open(); });
      dropdown.addEventListener('mouseleave', function () { close(); });
    });

    document.addEventListener('click', function () {
      document.querySelectorAll('.nav-dropdown-menu.is-open').forEach(function (menu) {
        menu.classList.remove('is-open');
        var trigger = menu.previousElementSibling;
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDropdowns);
  } else {
    initDropdowns();
  }
})();
```

- [ ] **Step 2: Verify the file exists and has content**

```bash
wc -l /home/debian/projects/fsa/fsa-website/nav.js
```
Expected: `55` (approximately — the exact line count of the file above)

- [ ] **Step 3: Commit**

```bash
cd /home/debian/projects/fsa/fsa-website
git add nav.js
git commit -m "feat: add nav.js dropdown behaviour"
```

---

### Task 3: Bulk-update all 41 HTML files

**Files:**
- Create (temp): `fsa-website/scripts/update_nav_dropdown.py`
- Modify: all 41 HTML files via the script

This task uses a Python script to make three replacements in every HTML file:

1. **Desktop nav** — replace the old `<li><a>Account</a></li>` with the dropdown `<li class="nav-dropdown">…</li>`
2. **Mobile drawer** — replace the old `<li><a>Account</a></li>` with two flat links
3. **Script tag** — insert `<script src="/nav.js" defer></script>` before `</body>`

- [ ] **Step 1: Create the update script**

Create `/home/debian/projects/fsa/fsa-website/scripts/update_nav_dropdown.py` with this exact content:

```python
#!/usr/bin/env python3
"""One-shot script: adds account dropdown to all FSA website HTML files."""

import os
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD_DESKTOP = '<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Account</a></li>'

NEW_DESKTOP = (
    '<li class="nav-dropdown">\n'
    '      <button class="nav-dropdown-trigger" aria-haspopup="true" aria-expanded="false">\n'
    '        Account <span class="nav-dropdown-arrow" aria-hidden="true">&#9662;</span>\n'
    '      </button>\n'
    '      <ul class="nav-dropdown-menu" role="menu">\n'
    '        <li role="none"><a href="https://my.fullsteamahead.ca" role="menuitem" rel="nofollow noopener">Learning Platform</a></li>\n'
    '        <li role="none"><a href="https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600" role="menuitem" rel="noopener noreferrer" target="_blank">Manage Subscription</a></li>\n'
    '      </ul>\n'
    '    </li>'
)

OLD_MOBILE = OLD_DESKTOP  # same string appears in both nav-links and mobile-menu-links

NEW_MOBILE = (
    '<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Learning Platform</a></li>\n'
    '      <li><a href="https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600" rel="noopener noreferrer" target="_blank">Manage Subscription</a></li>'
)

NAV_SCRIPT_TAG = '<script src="/nav.js" defer></script>\n</body>'

html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
# Exclude spec/plan docs that happen to mention HTML
html_files = [f for f in html_files if '/docs/' not in f]

updated = []
skipped = []

for path in sorted(html_files):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if OLD_DESKTOP not in content:
        skipped.append(path)
        continue

    # Count occurrences — expect exactly 2 (one desktop, one mobile)
    count = content.count(OLD_DESKTOP)
    if count != 2:
        print(f"WARNING: {path} has {count} occurrences of the Account link (expected 2) — skipping")
        skipped.append(path)
        continue

    # Replace first occurrence (desktop nav-links) with dropdown HTML
    content = content.replace(OLD_DESKTOP, NEW_DESKTOP, 1)

    # Replace second occurrence (mobile drawer) with two flat links
    content = content.replace(OLD_DESKTOP, NEW_MOBILE, 1)

    # Add nav.js before </body> if not already present
    if '/nav.js' not in content:
        content = content.replace('</body>', NAV_SCRIPT_TAG)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    updated.append(path)

print(f"\nUpdated: {len(updated)} files")
print(f"Skipped: {len(skipped)} files")
if skipped:
    print("Skipped files:")
    for p in skipped:
        print(f"  {p}")
```

- [ ] **Step 2: Run the script**

```bash
cd /home/debian/projects/fsa/fsa-website
python3 scripts/update_nav_dropdown.py
```

Expected output:
```
Updated: 41 files
Skipped: 0 files
```

If any files show "WARNING" or the skipped count is non-zero, stop and investigate before continuing.

- [ ] **Step 3: Verify desktop nav replacement in a sample of files**

```bash
grep -l "nav-dropdown" \
  /home/debian/projects/fsa/fsa-website/index.html \
  /home/debian/projects/fsa/fsa-website/enrollment-confirmation.html \
  /home/debian/projects/fsa/fsa-website/articles/mental-prep-power-engineering-exam/index.html \
  /home/debian/projects/fsa/fsa-website/articles/sopeec-multiple-choice-traps/index.html
```

Expected: all 4 filenames printed (meaning all 4 contain "nav-dropdown")

- [ ] **Step 4: Verify mobile nav replacement in a sample file**

```bash
grep -A2 "Learning Platform" /home/debian/projects/fsa/fsa-website/index.html | head -6
```

Expected output (the two flat mobile links):
```html
<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Learning Platform</a></li>
      <li><a href="https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600" rel="noopener noreferrer" target="_blank">Manage Subscription</a></li>
```

- [ ] **Step 5: Verify /nav.js script tag was added**

```bash
grep -l "nav.js" /home/debian/projects/fsa/fsa-website/*.html /home/debian/projects/fsa/fsa-website/articles/*/index.html | wc -l
```

Expected: `41`

- [ ] **Step 6: Verify the old Account link is gone**

```bash
grep -rl '"https://my.fullsteamahead.ca" rel="nofollow noopener">Account<' \
  /home/debian/projects/fsa/fsa-website/*.html \
  /home/debian/projects/fsa/fsa-website/articles/*/index.html
```

Expected: no output (zero files still contain the old plain Account link)

- [ ] **Step 7: Commit**

```bash
cd /home/debian/projects/fsa/fsa-website
git add -A
git commit -m "feat: add account dropdown nav to all 41 pages"
```

---

### Task 4: Deploy

**Files:** No new file changes — deploy what's committed.

- [ ] **Step 1: Deploy using the fsa-website-deploy skill**

Invoke the `fsa-website-deploy` skill. It handles Docker rebuild, Cloudflare cache purge, sitemap, and Search Console in the correct order.

- [ ] **Step 2: Smoke-test the live site**

Open `https://fullsteamahead.ca` in a browser:

1. Hover over "Account" in the desktop nav → dropdown should appear with "Learning Platform" and "Manage Subscription"
2. Click "Learning Platform" → should go to `https://my.fullsteamahead.ca`
3. Click "Manage Subscription" → should open `https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600` in a new tab
4. Resize to mobile → open the hamburger menu → should see "Learning Platform" and "Manage Subscription" as two separate flat links
5. Tab to the "Account" trigger with keyboard → press Enter → dropdown opens; arrow keys navigate; Escape closes

- [ ] **Step 3: Spot-check a second page type**

Open `https://fullsteamahead.ca/enrollment-confirmation.html` and repeat step 2 above.
