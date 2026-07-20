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
    }
  };
})();
