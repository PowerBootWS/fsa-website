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
 *
 * 3. Computed values derived from a price (affiliate.html's commission
 *    table): mark the element data-commission="students:metric", where
 *    metric is "monthly" or "annual". Computed as
 *    secondClass.current * (affiliate.commissionRate / 100) * students,
 *    x12 for annual. Added 2026-07-28 — same drift problem, one level removed
 *    (the table's numbers are commissionRate x price x student count, not a
 *    literal price, so a plain data-price substitution can't cover it).
 */

/*
 * `was` and `savings` were removed 2026-08-30 with the discount framing they
 * fed. "Launch pricing — save $50/mo" had run open-ended since launch with no
 * end date on five pages; permanent urgency reads as fake and the struck-out
 * $199 anchor was doing no work. Nothing displays a former price any more, and
 * a price field nobody renders is exactly how a stale number creeps back in --
 * so they are gone rather than kept "just in case". A real, dated sale later
 * should re-add them deliberately, alongside the markup that shows them.
 */
window.FSA_PRICING = {
  secondClass: { current: 149, cadence: 'month', papers: 6 },
  thirdClass:  { current: 99,  cadence: 'month', papers: 4 },
  fourthClass: { current: 99,  cadence: 'year', papers: 1 },
  // Annual prepay, added 2026-09-14. Same course, same papers and the same
  // subscriptions.class_code as the monthly plans — only the billing interval
  // differs — so these are a cadence of the plans above, not new programs.
  // Priced at 6x the monthly rate.
  secondClassAnnual: { current: 894, cadence: 'year', papers: 6 },
  thirdClassAnnual:  { current: 594, cadence: 'year', papers: 4 },
  affiliate:   { commissionRate: 20 }
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

(function () {
  var rate = window.FSA_PRICING.affiliate.commissionRate;
  var perStudentMonthly = window.FSA_PRICING.secondClass.current * (rate / 100);
  var els = document.querySelectorAll('[data-commission]');
  for (var i = 0; i < els.length; i++) {
    var el = els[i];
    var parts = el.getAttribute('data-commission').split(':');
    var students = parseInt(parts[0], 10);
    var metric = parts[1];
    var monthly = perStudentMonthly * students;
    var value = metric === 'annual' ? monthly * 12 : monthly;
    el.textContent = '$' + Math.round(value).toLocaleString('en-US');
  }
})();
