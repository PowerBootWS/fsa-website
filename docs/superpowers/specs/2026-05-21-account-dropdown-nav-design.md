# Account Dropdown Nav — Design Spec
**Date:** 2026-05-21  
**Status:** Approved

## Goal
Add a hover/click dropdown under the existing "Account" nav item on all public pages, exposing two links: the learning platform and the Stripe customer portal for subscription management.

## Scope
- **41 HTML files:** 13 top-level pages + 28 article sub-pages (all files containing `class="nav-links"`)
- **`styles-v2.css`** — new dropdown CSS block
- **`/nav.js`** — new shared script (created); referenced in all 41 HTML files

## Links
| Label | URL | Opens |
|-------|-----|-------|
| Learning Platform | `https://my.fullsteamahead.ca` | same tab |
| Manage Subscription | `https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600` | new tab |

## HTML Changes

### Desktop nav (`<ul class="nav-links">`)
Replace:
```html
<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Account</a></li>
```
With:
```html
<li class="nav-dropdown">
  <button class="nav-dropdown-trigger" aria-haspopup="true" aria-expanded="false">
    Account <span class="nav-dropdown-arrow" aria-hidden="true">▾</span>
  </button>
  <ul class="nav-dropdown-menu" role="menu">
    <li role="none"><a href="https://my.fullsteamahead.ca" role="menuitem" rel="nofollow noopener">Learning Platform</a></li>
    <li role="none"><a href="https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600" role="menuitem" rel="noopener noreferrer" target="_blank">Manage Subscription</a></li>
  </ul>
</li>
```

### Mobile drawer (`<ul class="mobile-menu-links">`)
Replace:
```html
<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Account</a></li>
```
With:
```html
<li><a href="https://my.fullsteamahead.ca" rel="nofollow noopener">Learning Platform</a></li>
<li><a href="https://billing.stripe.com/p/login/3cI14peeQ395ckie6N1B600" rel="noopener noreferrer" target="_blank">Manage Subscription</a></li>
```

## CSS (`styles-v2.css`)
Append a new block after the existing `.nav-links a:hover` rule:

```css
/* ── ACCOUNT DROPDOWN ── */
.nav-dropdown { position: relative; }

.nav-dropdown-trigger {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
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

## JavaScript (`/nav.js`)
New file. Handles:
- **Click** on trigger: toggles `aria-expanded` + `.is-open` on menu
- **Keyboard:** Enter/Space toggles; Escape closes + returns focus; ArrowDown/Up moves focus between the two `<a>` items
- **Outside click:** closes open dropdown
- **Hover intent:** CSS handles the visual reveal; JS manages ARIA state on mouseenter/mouseleave

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
      function toggle() { trigger.getAttribute('aria-expanded') === 'true' ? close() : open(); }

      trigger.addEventListener('click', function (e) { e.stopPropagation(); toggle(); });

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

      dropdown.addEventListener('mouseleave', function () { close(); });
      dropdown.addEventListener('mouseenter', function () { open(); });
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

## Script Tag
Add to every HTML file, just before `</body>` (or alongside existing scripts):
```html
<script src="/nav.js" defer></script>
```

## Pages Included
All pages — including confirmation pages (`enrollment-confirmation.html`, `affiliate-confirmation.html`), legal pages (`privacy-policy.html`, `terms-of-use.html`), `404.html`, `coming-soon.html`, and all 28 article sub-pages.

## Out of Scope
- No changes to any page content, hero, or other sections
- No changes to existing hamburger menu JS
- No changes to any other nav items
