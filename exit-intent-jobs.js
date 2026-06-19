(function () {
  'use strict';

  var STORAGE_KEY   = 'fsa_exit_jobs_dismissed';
  var SUBSCRIBED_KEY = 'fsa_exit_jobs_subscribed';
  var COOLDOWN_MS   = 14 * 24 * 60 * 60 * 1000;
  var WORKER_URL    = 'https://fsa-lead-capture.powerboot.workers.dev/resume';

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
      '<h2>Land Your Next Power Engineering Job</h2>',
      '<p class="fsa-exit-sub">',
        'Get our free checklist: <strong>5 rules</strong> to craft a power engineering resume that gets past the first screen.',
      '</p>',
      '<div id="fsa-exit-action-area">',
        '<div class="fsa-exit-field">',
          '<label for="fsa-exit-name">First Name</label>',
          '<input type="text" id="fsa-exit-name" placeholder="Your first name" autocomplete="given-name">',
        '</div>',
        '<div class="fsa-exit-field">',
          '<label for="fsa-exit-email">Email</label>',
          '<input type="email" id="fsa-exit-email" placeholder="your@email.com" autocomplete="email">',
        '</div>',
        '<div class="fsa-exit-optin">',
          '<input type="checkbox" id="fsa-exit-optin" aria-required="true">',
          '<span>I agree to receive messages from Full Steam Ahead. I can unsubscribe any time.</span>',
        '</div>',
        '<button class="fsa-exit-cta-btn" id="fsa-exit-cta">Send Me the Checklist &rarr;</button>',
        '<div class="fsa-exit-error" id="fsa-exit-error" style="display:none"></div>',
      '</div>',
      '<p class="fsa-exit-footnote">No spam. Unsubscribe any time.</p>',
    '</div>',
  ].join('');

  document.body.appendChild(overlay);

  var closeBtn   = document.getElementById('fsa-exit-close');
  var ctaBtn     = document.getElementById('fsa-exit-cta');
  var actionArea = document.getElementById('fsa-exit-action-area');
  var errorEl    = document.getElementById('fsa-exit-error');

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

  // --- Form submission ---
  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.style.display = 'block';
  }

  function showSuccess() {
    actionArea.innerHTML = [
      '<div class="fsa-exit-success">',
        '<div class="fsa-exit-success-icon">✓</div>',
        '<p>You\'re in! Check your inbox — your resume checklist is on its way.</p>',
      '</div>',
    ].join('');
    markSubscribed();
  }

  ctaBtn.addEventListener('click', function () {
    var nameEl   = document.getElementById('fsa-exit-name');
    var emailEl  = document.getElementById('fsa-exit-email');
    var optinEl  = document.getElementById('fsa-exit-optin');

    errorEl.style.display = 'none';

    var firstName = nameEl.value.trim();
    var email     = emailEl.value.trim();

    if (!firstName) { showError('Please enter your first name.'); nameEl.focus(); return; }
    if (!email)     { showError('Please enter your email address.'); emailEl.focus(); return; }
    if (!optinEl.checked) { showError('Please check the consent box to continue.'); optinEl.focus(); return; }

    ctaBtn.disabled = true;
    ctaBtn.innerHTML = '<span class="fsa-exit-spinner"></span>Sending…';

    fetch(WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ firstName: firstName, email: email }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error('Worker error: ' + res.status);
        return res.json();
      })
      .then(function (data) {
        if (!data.success) throw new Error(data.error || 'Unknown error');
        showSuccess();
      })
      .catch(function () {
        showError('Something went wrong — please try again.');
        ctaBtn.disabled = false;
        ctaBtn.innerHTML = 'Send Me the Checklist &rarr;';
      });
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
