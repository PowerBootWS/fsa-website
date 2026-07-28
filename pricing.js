/*
 * FSA pricing — single source of truth.
 *
 * Every page that displays a course price should read it from here instead
 * of hardcoding a number, so a price change only has to happen in one place.
 * Added 2026-07-27 after a stale $99/mo price sat live on 25 article CTAs
 * for weeks — see wiki/log.md for the incident.
 *
 * Two ways to use it:
 *
 * 1. Static content (articles, marketing pages): mark the number with
 *    data-price="planKey.field" and load this file near the end of <body>
 *    (with `defer`, same spot as nav.js). On load it fills in every
 *    matching element's text automatically.
 *
 *      <sup>$</sup><span data-price="secondClass.current">149</span>/month
 *
 *    The literal number left in the markup is the fallback shown if JS is
 *    blocked — keep it in sync with the object below when you edit prices.
 *
 * 2. Pages with their own pricing logic (enroll.html): load this file
 *    synchronously, BEFORE your own script runs, with a plain
 *    `<script src="/pricing.js"></script>` (no defer) — then read
 *    window.FSA_PRICING directly instead of hardcoding numbers.
 */

window.FSA_PRICING = {
  secondClass: { current: 149, was: 199, cadence: 'month', savings: 50, papers: 6 },
  thirdClass:  { current: 99,  was: 149, cadence: 'month', savings: 50, papers: 4 },
  fourthClass: { current: 99,  cadence: 'year', papers: 1 }
};

(function () {
  var els = document.querySelectorAll('[data-price]');
  for (var i = 0; i < els.length; i++) {
    var el = els[i];
    var parts = el.getAttribute('data-price').split('.');
    var plan = window.FSA_PRICING[parts[0]];
    if (plan && plan[parts[1]] !== undefined) {
      el.textContent = plan[parts[1]];
    }
  }
})();
