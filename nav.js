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

      menu.addEventListener('click', function (e) { e.stopPropagation(); });

      dropdown.addEventListener('mouseenter', function () { open(); });
      dropdown.addEventListener('mouseleave', function () { close(); });
    });

    document.addEventListener('click', function () {
      document.querySelectorAll('.nav-dropdown-menu.is-open').forEach(function (menu) {
        menu.classList.remove('is-open');
        var parentDropdown = menu.closest('.nav-dropdown');
        if (parentDropdown) {
          var trigger = parentDropdown.querySelector('.nav-dropdown-trigger');
          if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDropdowns);
  } else {
    initDropdowns();
  }
})();

(function () {
  function initAffiliateTracking() {
    var params = new URLSearchParams(window.location.search);
    var code = params.get('am_id');
    if (!code) return;
    document.cookie = 'fsa_affiliate=' + encodeURIComponent(code) + '; max-age=7776000; path=/';
    try {
      fetch('https://fsa-lead-capture.powerboot.workers.dev/track?am_id=' + encodeURIComponent(code), { mode: 'no-cors' });
    } catch (e) {}
  }
  initAffiliateTracking();

  window.FSAAffiliate = {
    processStripePaymentLinks: function () {
      var match = document.cookie.match(/(?:^|;\s*)fsa_affiliate=([^;]+)/);
      if (!match) return;
      var code = decodeURIComponent(match[1]);
      document.querySelectorAll('.refgrow-stripe-payment-link').forEach(function (link) {
        try {
          var url = new URL(link.href);
          url.searchParams.set('client_reference_id', 'ref_' + code);
          link.href = url.toString();
        } catch (e) {}
      });
    },
    // free-practice-exam.html forwards its own am_id query param onto the
    // learn.* CTA it builds, but internal links to /free-practice-exam from
    // other pages (library.html, homepage) are plain hrefs with no query
    // string — since learn.fullsteamahead.ca is a different subdomain, the
    // fsa_affiliate cookie set here doesn't carry over on its own, so the
    // code has to be appended to the link's href before the click happens.
    //
    // Called automatically on every page that loads nav.js (see below). It
    // used to be opt-in, invoked by hand from index.html and library.html
    // only, which meant the three article pages that also link to
    // /free-practice-exam silently dropped the affiliate code — an affiliate
    // visitor who landed on an article and clicked through to the practice
    // exam was never attributed, with nothing anywhere to show it. Any new
    // page linking to the practice exam would have inherited the same bug.
    processFreePracticeExamLinks: function () {
      var match = document.cookie.match(/(?:^|;\s*)fsa_affiliate=([^;]+)/);
      if (!match) return;
      var code = decodeURIComponent(match[1]);
      document.querySelectorAll('a[href^="/free-practice-exam"]').forEach(function (link) {
        try {
          var url = new URL(link.href, window.location.origin);
          if (!url.searchParams.has('am_id')) {
            url.searchParams.set('am_id', code);
            link.href = url.toString();
          }
        } catch (e) {}
      });
    }
  };

  // Run on every page rather than requiring each one to opt in. The function
  // is a no-op without an fsa_affiliate cookie and skips any link that
  // already carries an am_id, so running it everywhere is safe and
  // idempotent — including on the pages that still call it explicitly, and
  // on free-practice-exam.html, which sets its own am_id first.
  //
  // processStripePaymentLinks is deliberately NOT auto-run: it rewrites
  // checkout URLs and stays opt-in per page.
  function applyExamLinkAttribution() {
    window.FSAAffiliate.processFreePracticeExamLinks();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyExamLinkAttribution);
  } else {
    applyExamLinkAttribution();
  }
})();

// ---------------------------------------------------------------------------
// File-download tracking (added 2026-09-02)
//
// GA4 Enhanced Measurement's built-in `file_download` event has never been
// switched on for this property: a check of 180 days of event data, both
// hostname-filtered and property-wide, returned nine event names and
// file_download was not among them. The consequence was that /library — the
// single largest free asset on the site, 35 PDFs and ~1,100 landing sessions a
// quarter — produced no data whatsoever. There was no way to tell which books
// were in demand, whether visitors downloaded anything at all, or whether a
// download ever preceded an enrolment.
//
// This fires the event from our own code rather than from the GA4 admin
// toggle, so it lives in version control, deploys with the site, and cannot be
// silently switched off in a UI nobody is looking at.
//
// The gtag bootstrap mirrors what jobs.html already does inline for
// `jobs_banner_click` / `jobs_alert_subscribe` — a pattern proven to reach GA4
// on this property while GTM is also present. `send_page_view: false` is what
// keeps it from double-counting pageviews against the GTM container.
// ---------------------------------------------------------------------------
(function () {
  var GA4_ID = 'G-5ZFF5FB8R8';

  // Extensions worth counting as a download. Anything carrying an explicit
  // `download` attribute is tracked regardless of extension.
  var TRACKED_EXT = /\.(pdf|zip|csv|xlsx?|docx?|pptx?|epub|mp3)$/i;

  // Textbook filenames follow PowerEngineering_{Second|Third|Fourth}Class{A|B}_Book{N}_E{25|30|35}.pdf
  // (with one known exception carrying a trailing -1, which this still matches).
  var TEXTBOOK_RE = /PowerEngineering_(First|Second|Third|Fourth)Class([AB])_Book(\d+)/i;
  // Whole-part bundles (4th Class only, added 2026-09-02) — one zip per paper.
  // Tracked as their own category so a bundle download is never confused with a
  // single unit when the library is ranked by demand: one bundle is twelve books.
  var BUNDLE_RE = /PowerEngineering_(First|Second|Third|Fourth)Class([AB])_AllUnits/i;
  var CLASS_LABEL = { first: '1st Class', second: '2nd Class', third: '3rd Class', fourth: '4th Class' };

  function ensureGtag() {
    // GTM defines window.gtag in most GA4 container setups, and jobs.html
    // defines it inline. In either case the GA4 stream is already registered
    // and an event sent through it routes correctly, so leave it alone.
    if (typeof window.gtag === 'function') return;

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };

    if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
      document.head.appendChild(s);
    }

    window.gtag('js', new Date());
    window.gtag('config', GA4_ID, { send_page_view: false });
  }

  function classify(url, pathname) {
    if (BUNDLE_RE.test(pathname)) return 'textbook-bundle';
    if (TEXTBOOK_RE.test(pathname)) return 'textbook';
    if (pathname.indexOf('/assets/lead-magnets/') === 0) return 'lead-magnet';
    if (url.host !== window.location.host) return 'external';
    return 'other';
  }

  function trackDownload(link) {
    var url;
    try {
      url = new URL(link.getAttribute('href'), window.location.href);
    } catch (e) {
      return;
    }

    var pathname = url.pathname;
    var isExplicit = link.hasAttribute('download');
    if (!isExplicit && !TRACKED_EXT.test(pathname)) return;

    var fileName = pathname.split('/').pop() || pathname;
    var extMatch = fileName.match(/\.([a-z0-9]+)$/i);
    var linkText = (link.textContent || '').replace(/\s+/g, ' ').trim();

    var params = {
      file_name: fileName,
      file_extension: extMatch ? extMatch[1].toLowerCase() : '',
      link_url: url.href,
      link_text: linkText.slice(0, 100),
      file_category: classify(url, pathname),
      page_path: window.location.pathname
    };

    // Which book, so the library can be ranked by actual demand rather than
    // by guesswork about which class level people come here for.
    var book = pathname.match(TEXTBOOK_RE) || pathname.match(BUNDLE_RE);
    if (book) {
      params.book_class = CLASS_LABEL[book[1].toLowerCase()] || book[1];
      params.book_part = book[2].toUpperCase();
      if (book[3]) params.book_number = book[3];
    }

    // The size is printed next to every library download; carrying it through
    // makes it possible to spot a large file people start and abandon.
    var sizeEl = link.parentElement && link.parentElement.querySelector('.chapter-size');
    if (sizeEl) params.file_size = sizeEl.textContent.trim();

    try {
      ensureGtag();
      window.gtag('event', 'file_download', params);
    } catch (e) {}
  }

  // Delegated so it covers links added after load (the jobs page builds cards
  // client-side) without every page having to opt in.
  document.addEventListener('click', function (e) {
    var link = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!link) return;
    trackDownload(link);
  }, true);
})();
