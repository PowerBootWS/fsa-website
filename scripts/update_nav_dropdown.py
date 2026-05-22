#!/usr/bin/env python3
"""One-shot script: adds account dropdown to all FSA website HTML files."""

import os
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD_ACCOUNT = '<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Account</a></li>'

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

NEW_MOBILE = (
    '<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Learning Platform</a></li>\n'
    '      <li><a href="https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600" rel="noopener noreferrer" target="_blank">Manage Subscription</a></li>'
)

NAV_SCRIPT_TAG = '<script src="/nav.js" defer></script>\n</body>'

html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
# Exclude spec/plan docs that happen to contain HTML
html_files = [f for f in html_files if '/docs/' not in f]

updated = []
skipped = []

for path in sorted(html_files):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if OLD_ACCOUNT not in content:
        skipped.append(path)
        continue

    # Count occurrences — expect exactly 2 (one desktop, one mobile)
    count = content.count(OLD_ACCOUNT)
    if count != 2:
        print(f"WARNING: {path} has {count} occurrences of the Account link (expected 2) — skipping")
        skipped.append(path)
        continue

    # Replace first occurrence (desktop nav-links) with dropdown HTML
    content = content.replace(OLD_ACCOUNT, NEW_DESKTOP, 1)

    # Replace second occurrence (mobile drawer) with two flat links
    content = content.replace(OLD_ACCOUNT, NEW_MOBILE, 1)

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
