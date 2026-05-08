(function () {
  'use strict';

  var STORAGE_KEY = 'fsa_exit_intent_dismissed';
  var GHL_BEARER  = 'Bearer pit-1101cce2-706a-41aa-9934-8da9f19e9dae';
  var GHL_ALT_ID  = 'SrttR5wZPQD7bIeOAplf';
  var ENROLL_BASE = 'https://enrollment.fullsteamahead.ca';

  // --- Suppression check ---
  function isDismissed() {
    try { return !!localStorage.getItem(STORAGE_KEY); } catch (e) { return false; }
  }
  function markDismissed() {
    try { localStorage.setItem(STORAGE_KEY, '1'); } catch (e) {}
  }

  if (isDismissed()) return;

  // --- Code generator: FSA + 5 chars, no ambiguous O/0/I/1 ---
  function genCode() {
    var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    var code = 'FSA';
    for (var i = 0; i < 5; i++) {
      code += chars[Math.floor(Math.random() * chars.length)];
    }
    return code;
  }

  // --- ISO timestamp helpers ---
  function toISO(d) {
    return d.toISOString();
  }

  // --- Inject styles ---
  var style = document.createElement('style');
  style.textContent = [
    '.fsa-exit-overlay{',
      'position:fixed;inset:0;z-index:3000;',
      'background:rgba(5,9,15,0.93);',
      'backdrop-filter:blur(6px);',
      '-webkit-backdrop-filter:blur(6px);',
      'display:flex;align-items:center;justify-content:center;',
      'padding:1.5rem;',
      'opacity:0;pointer-events:none;transition:opacity 0.25s ease;',
    '}',
    '.fsa-exit-overlay.is-open{opacity:1;pointer-events:auto;}',
    '.fsa-exit-modal{',
      'position:relative;',
      'width:100%;max-width:500px;',
      'background:var(--iron,#141A24);',
      'border:1px solid var(--plate-edge,#252F42);',
      'border-top:3px solid var(--orange,#E8720C);',
      'padding:2.4rem 2.2rem 2rem;',
      'box-shadow:0 0 80px rgba(0,0,0,0.85);',
    '}',
    '.fsa-exit-close{',
      'position:absolute;top:-2.2rem;right:0;',
      'background:none;border:none;cursor:pointer;',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:0.85rem;font-weight:600;letter-spacing:0.08em;',
      'text-transform:uppercase;color:var(--gray-light,#C8D0DA);',
      'padding:0.2rem 0;transition:color 0.18s;',
    '}',
    '.fsa-exit-close::before{content:"✕  ";}',
    '.fsa-exit-close:hover{color:#fff;}',
    '.fsa-exit-badge{',
      'display:inline-block;',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:0.78rem;font-weight:700;letter-spacing:0.12em;',
      'text-transform:uppercase;color:var(--orange,#E8720C);',
      'margin-bottom:0.7rem;',
    '}',
    '.fsa-exit-modal h2{',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:1.9rem;font-weight:800;letter-spacing:0.02em;',
      'text-transform:uppercase;color:#fff;',
      'margin:0 0 0.6rem;line-height:1.15;',
    '}',
    '.fsa-exit-sub{',
      'font-family:"Barlow",sans-serif;',
      'font-size:0.95rem;color:var(--gray-light,#C8D0DA);',
      'margin:0 0 1.4rem;line-height:1.5;',
    '}',
    '.fsa-exit-offer-box{',
      'display:flex;align-items:center;gap:1rem;',
      'background:rgba(232,114,12,0.07);',
      'border-left:4px solid var(--orange,#E8720C);',
      'padding:1rem 1.2rem;margin-bottom:1.6rem;',
    '}',
    '.fsa-exit-offer-amount{',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:2.6rem;font-weight:800;color:var(--orange,#E8720C);',
      'line-height:1;white-space:nowrap;',
    '}',
    '.fsa-exit-offer-desc{',
      'font-family:"Barlow",sans-serif;',
      'font-size:0.88rem;color:var(--gray-light,#C8D0DA);',
      'line-height:1.45;',
    '}',
    '.fsa-exit-cta-btn{',
      'display:block;width:100%;',
      'background:var(--orange,#E8720C);color:#fff;border:none;',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:1.1rem;font-weight:700;letter-spacing:0.08em;',
      'text-transform:uppercase;padding:1rem 2rem;',
      'border-radius:4px;cursor:pointer;',
      'transition:background 0.2s,transform 0.18s,box-shadow 0.2s;',
    '}',
    '.fsa-exit-cta-btn:hover:not(:disabled){',
      'background:var(--orange-glow,#FF8C2A);',
      'transform:translateY(-2px);',
      'box-shadow:0 10px 28px rgba(232,114,12,0.35);',
    '}',
    '.fsa-exit-cta-btn:disabled{opacity:0.6;cursor:not-allowed;}',
    '.fsa-exit-spinner{',
      'display:inline-block;',
      'width:1em;height:1em;',
      'border:2px solid rgba(255,255,255,0.3);',
      'border-top-color:#fff;border-radius:50%;',
      'animation:fsa-spin 0.7s linear infinite;',
      'vertical-align:middle;margin-right:0.5em;',
    '}',
    '@keyframes fsa-spin{to{transform:rotate(360deg);}}',
    '.fsa-exit-code-wrap{margin:1.4rem 0 0.6rem;}',
    '.fsa-exit-code-label{',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:0.78rem;font-weight:700;letter-spacing:0.12em;',
      'text-transform:uppercase;color:var(--gray-mid,#7a8899);',
      'margin-bottom:0.45rem;',
    '}',
    '.fsa-exit-code-box{',
      'display:flex;align-items:center;justify-content:center;',
      'background:var(--plate,#1C2333);',
      'border:1px solid var(--plate-edge,#252F42);',
      'border-left:4px solid var(--orange,#E8720C);',
      'padding:0.9rem 1.2rem;',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:2rem;font-weight:800;letter-spacing:0.18em;',
      'color:#fff;text-transform:uppercase;',
      'user-select:all;',
    '}',
    '.fsa-exit-timer-wrap{',
      'text-align:center;margin:0.9rem 0 1.2rem;',
    '}',
    '.fsa-exit-timer-label{',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:0.8rem;font-weight:600;letter-spacing:0.1em;',
      'text-transform:uppercase;color:var(--gray-mid,#7a8899);',
      'display:block;margin-bottom:0.2rem;',
    '}',
    '.fsa-exit-timer-val{',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:2.2rem;font-weight:800;',
      'color:var(--amber,#F5A623);letter-spacing:0.06em;',
    '}',
    '.fsa-exit-timer-val.expired{color:var(--gray-mid,#7a8899);}',
    '.fsa-exit-enroll-btn{',
      'display:block;width:100%;',
      'background:var(--orange,#E8720C);color:#fff;border:none;',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:1.1rem;font-weight:700;letter-spacing:0.08em;',
      'text-transform:uppercase;padding:1rem 2rem;',
      'border-radius:4px;cursor:pointer;',
      'text-decoration:none;text-align:center;',
      'transition:background 0.2s,transform 0.18s,box-shadow 0.2s;',
    '}',
    '.fsa-exit-enroll-btn:hover{',
      'background:var(--orange-glow,#FF8C2A);',
      'transform:translateY(-2px);',
      'box-shadow:0 10px 28px rgba(232,114,12,0.35);',
    '}',
    '.fsa-exit-error{',
      'font-family:"Barlow",sans-serif;font-size:0.85rem;',
      'color:#e57373;margin-top:0.7rem;text-align:center;',
    '}',
    '.fsa-exit-footnote{',
      'font-family:"Barlow",sans-serif;',
      'font-size:0.72rem;color:var(--gray-mid,#7a8899);',
      'margin-top:1rem;text-align:center;',
    '}',
    '@media(max-width:520px){',
      '.fsa-exit-modal{padding:1.8rem 1.3rem 1.5rem;}',
      '.fsa-exit-modal h2{font-size:1.55rem;}',
      '.fsa-exit-offer-amount{font-size:2rem;}',
      '.fsa-exit-code-box{font-size:1.6rem;}',
    '}',
  ].join('');
  document.head.appendChild(style);

  // --- Build popup DOM ---
  var overlay = document.createElement('div');
  overlay.className = 'fsa-exit-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Special enrollment offer');

  overlay.innerHTML = [
    '<div class="fsa-exit-modal">',
      '<button class="fsa-exit-close" id="fsa-exit-close" aria-label="Close offer">Close</button>',
      '<div class="fsa-exit-badge">Limited Time Offer</div>',
      '<h2>Don\'t Leave Without Your Discount</h2>',
      '<p class="fsa-exit-sub">',
        'You\'re one step from your 2nd Class ticket. Grab <strong>$50 off your first six months</strong> — ',
        'only available right now.',
      '</p>',
      '<div class="fsa-exit-offer-box">',
        '<div class="fsa-exit-offer-amount">$50<sup style="font-size:1.1rem;vertical-align:super">OFF</sup></div>',
        '<div class="fsa-exit-offer-desc">',
          '<strong style="color:#fff;font-family:\'Barlow Condensed\',sans-serif;font-size:1rem;letter-spacing:0.04em">',
            '$50 off your first six months',
          '</strong><br>',
          '2nd Class Complete — all six papers, AI tutoring, adaptive practice exams.',
        '</div>',
      '</div>',
      '<div id="fsa-exit-action-area">',
        '<button class="fsa-exit-cta-btn" id="fsa-exit-cta">Claim My $50 Discount &rarr;</button>',
        '<div class="fsa-exit-error" id="fsa-exit-error" style="display:none"></div>',
      '</div>',
      '<p class="fsa-exit-footnote">* Discount cannot be combined with any other offer.</p>',
    '</div>',
  ].join('');

  document.body.appendChild(overlay);

  var closeBtn   = document.getElementById('fsa-exit-close');
  var ctaBtn     = document.getElementById('fsa-exit-cta');
  var actionArea = document.getElementById('fsa-exit-action-area');
  var errorEl    = document.getElementById('fsa-exit-error');

  // --- Open / close ---
  var timerInterval = null;

  function openPopup() {
    overlay.classList.add('is-open');
    closeBtn.focus();
  }

  function closePopup() {
    overlay.classList.remove('is-open');
    markDismissed();
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  }

  closeBtn.addEventListener('click', closePopup);

  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closePopup();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) closePopup();
  });

  // --- Countdown timer ---
  function startTimer(seconds, timerValEl, enrollBtn) {
    var remaining = seconds;

    function tick() {
      if (remaining <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        timerValEl.textContent = 'Expired';
        timerValEl.classList.add('expired');
        if (enrollBtn) enrollBtn.style.opacity = '0.4';
        return;
      }
      remaining--;
      var m = Math.floor(remaining / 60);
      var s = remaining % 60;
      timerValEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
    }

    tick();
    timerInterval = setInterval(tick, 1000);
  }

  // --- Coupon creation ---
  ctaBtn.addEventListener('click', function () {
    ctaBtn.disabled = true;
    errorEl.style.display = 'none';
    ctaBtn.innerHTML = '<span class="fsa-exit-spinner"></span>Generating your code…';

    var code = genCode();
    var now  = new Date();
    var end  = new Date(now.getTime() + 15 * 60 * 1000);

    var payload = {
      altId: GHL_ALT_ID,
      altType: 'location',
      name: 'Exit Intent - ' + code,
      code: code,
      discountType: 'amount',
      discountValue: 50,
      startDate: toISO(now),
      endDate: toISO(end),
      usageLimit: 1,
      productIds: ['prod_UPxkq0bv5W786k'],
      priceIds: ['price_1TR7p3PIu0moGqy4Z3HM3hbh'],
      applyToFuturePayments: true,
      applyToFuturePaymentsConfig: [{ type: 'fixed', duration: 5, durationType: 'months' }],
      limitPerCustomer: true
    };

    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'https://services.leadconnectorhq.com/payments/coupon', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.setRequestHeader('Version', '2023-02-21');
    xhr.setRequestHeader('Authorization', GHL_BEARER);

    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        showCodeState(code);
        markDismissed();
      } else {
        showError('Something went wrong — please try again.');
        ctaBtn.disabled = false;
        ctaBtn.innerHTML = 'Claim My $50 Discount &rarr;';
      }
    };

    xhr.onerror = function () {
      showError('Network error — please check your connection and try again.');
      ctaBtn.disabled = false;
      ctaBtn.innerHTML = 'Claim My $50 Discount &rarr;';
    };

    xhr.send(JSON.stringify(payload));
  });

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.style.display = 'block';
  }

  function showCodeState(code) {
    actionArea.innerHTML = [
      '<div class="fsa-exit-code-wrap">',
        '<div class="fsa-exit-code-label">Your Discount Code</div>',
        '<div class="fsa-exit-code-box" id="fsa-exit-codeval">' + code + '</div>',
      '</div>',
      '<div class="fsa-exit-timer-wrap">',
        '<span class="fsa-exit-timer-label">Code expires in</span>',
        '<span class="fsa-exit-timer-val" id="fsa-exit-timer">15:00</span>',
      '</div>',
      '<a href="' + ENROLL_BASE + '?dc=' + encodeURIComponent(code) + '" ',
        'rel="nofollow noopener" class="fsa-exit-enroll-btn" id="fsa-exit-enroll">',
        'Lock In My Discount &rarr;',
      '</a>',
    ].join('');

    var timerValEl = document.getElementById('fsa-exit-timer');
    var enrollBtn  = document.getElementById('fsa-exit-enroll');
    startTimer(15 * 60, timerValEl, enrollBtn);
  }

  // --- Trigger logic ---
  var triggered   = false;
  var mouseEntered = false;

  function maybeShow() {
    if (triggered || isDismissed()) return;
    triggered = true;
    openPopup();
  }

  // Desktop: fire only after the mouse has entered the viewport at least once,
  // then leaves toward the top (address bar / browser chrome).
  document.addEventListener('mouseenter', function () {
    mouseEntered = true;
  });

  document.addEventListener('mouseleave', function (e) {
    if (mouseEntered && e.clientY < 10) maybeShow();
  });

  // Mobile: 30s delay
  if (window.innerWidth < 768) {
    setTimeout(maybeShow, 30000);
  }

}());
