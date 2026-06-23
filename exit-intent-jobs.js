(function () {
  'use strict';

  var STORAGE_KEY   = 'fsa_exit_jobs_dismissed';
  var SUBSCRIBED_KEY = 'fsa_exit_jobs_subscribed';
  var COOLDOWN_MS   = 14 * 24 * 60 * 60 * 1000;

  // --- Suppression check ---
  function isDismissed() {
    try {
      if (localStorage.getItem(SUBSCRIBED_KEY)) return true;
      var ts = localStorage.getItem(STORAGE_KEY);
      return !!(ts && (Date.now() - parseInt(ts, 10)) < COOLDOWN_MS);
    } catch (e) { return false; }
  }
  function markDismissed() {
    try { localStorage.setItem(STORAGE_KEY, String(Date.now())); } catch (e) {}
  }
  function markSubscribed() {
    try { localStorage.setItem(SUBSCRIBED_KEY, '1'); } catch (e) {}
  }

  if (isDismissed()) return;

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
      'margin:0 0 1.3rem;line-height:1.5;',
    '}',
    '.fsa-exit-field{margin-bottom:0.85rem;}',
    '.fsa-exit-field label{',
      'display:block;',
      'font-family:"Barlow Condensed",sans-serif;',
      'font-size:0.78rem;font-weight:700;letter-spacing:0.1em;',
      'text-transform:uppercase;color:var(--gray-mid,#7a8899);',
      'margin-bottom:0.35rem;',
    '}',
    '.fsa-exit-field input{',
      'display:block;width:100%;box-sizing:border-box;',
      'background:var(--plate,#1C2333);',
      'border:1px solid var(--plate-edge,#252F42);',
      'border-radius:4px;',
      'padding:0.65rem 0.9rem;',
      'font-family:"Barlow",sans-serif;font-size:0.97rem;',
      'color:#fff;',
      'outline:none;transition:border-color 0.18s;',
    '}',
    '.fsa-exit-field input::placeholder{color:var(--gray-mid,#7a8899);}',
    '.fsa-exit-field input:focus{border-color:var(--orange,#E8720C);}',
    '.fsa-exit-optin{',
      'display:flex;align-items:flex-start;gap:0.6rem;',
      'margin-bottom:1.2rem;',
    '}',
    '.fsa-exit-optin input[type="checkbox"]{',
      'flex-shrink:0;margin-top:0.18rem;',
      'width:1rem;height:1rem;',
      'accent-color:var(--orange,#E8720C);',
      'cursor:pointer;',
    '}',
    '.fsa-exit-optin span{',
      'font-family:"Barlow",sans-serif;',
      'font-size:0.8rem;color:var(--gray-mid,#7a8899);',
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
    '.fsa-exit-error{',
      'font-family:"Barlow",sans-serif;font-size:0.85rem;',
      'color:#e57373;margin-top:0.7rem;text-align:center;',
    '}',
    '.fsa-exit-success{',
      'text-align:center;padding:1.2rem 0 0.5rem;',
    '}',
    '.fsa-exit-success-icon{',
      'font-size:2.6rem;color:var(--orange,#E8720C);',
      'line-height:1;margin-bottom:0.7rem;',
    '}',
    '.fsa-exit-success p{',
      'font-family:"Barlow",sans-serif;font-size:1rem;',
      'color:var(--gray-light,#C8D0DA);line-height:1.55;margin:0;',
    '}',
    '.fsa-exit-footnote{',
      'font-family:"Barlow",sans-serif;',
      'font-size:0.72rem;color:var(--gray-mid,#7a8899);',
      'margin-top:1rem;text-align:center;',
    '}',
    '@media(max-width:520px){',
      '.fsa-exit-modal{padding:1.8rem 1.3rem 1.5rem;}',
      '.fsa-exit-modal h2{font-size:1.55rem;}',
    '}',
  ].join('');
  document.head.appendChild(style);

  // --- Build popup DOM ---
  var overlay = document.createElement('div');
  overlay.className = 'fsa-exit-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Free resume checklist');

  overlay.innerHTML = [
    '<div class="fsa-exit-modal">',
      '<button class="fsa-exit-close" id="fsa-exit-close" aria-label="Close">Close</button>',
      '<div class="fsa-exit-badge">Free Checklist</div>',
      '<h2>Before You Go — Grab the Resume Checklist</h2>',
      '<p class="fsa-exit-sub">',
        'Most power engineers write their resume like any other trade resume. Hiring managers at Canadian plants ',
        'screen for specific signals — this <strong>free 5-rule checklist</strong> covers exactly what those are.',
      '</p>',
      '<p class="fsa-exit-sub" style="margin-bottom:1.5rem;">',
        'Certificate class positioning, the equipment language that gets past ATS, why listing duties kills applications, ',
        'and the one formatting mistake that gets resumes tossed before they\'re read.',
      '</p>',
      '<a class="fsa-exit-cta-btn" id="fsa-exit-cta" href="/lead-magnets/power-engineering-resume-checklist/" style="display:block;text-align:center;text-decoration:none;">',
        'Get the Free Checklist &rarr;',
      '</a>',
      '<p class="fsa-exit-footnote">Free. No spam. Unsubscribe any time.</p>',
    '</div>',
  ].join('');

  document.body.appendChild(overlay);

  var closeBtn = document.getElementById('fsa-exit-close');
  var ctaBtn   = document.getElementById('fsa-exit-cta');

  // --- Open / close ---
  function openPopup() {
    overlay.classList.add('is-open');
    closeBtn.focus();
  }

  function closePopup() {
    overlay.classList.remove('is-open');
    markDismissed();
  }

  closeBtn.addEventListener('click', closePopup);

  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closePopup();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) closePopup();
  });

  // Dismiss popup when user clicks through to the landing page
  ctaBtn.addEventListener('click', function () {
    markDismissed();
  });

  // --- Trigger logic ---
  var triggered    = false;
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

  // Mobile: 30s delay, only if user has scrolled enough to show engagement
  if (window.innerWidth < 768) {
    setTimeout(function () {
      if (window.scrollY > 200) maybeShow();
    }, 30000);
  }

}());
