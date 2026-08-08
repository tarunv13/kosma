/* KOSMA — the small amount of behaviour this interface needs.
 *
 * No framework, no build step, no inline handlers (the CSP forbids them).
 * Two jobs: switch each place block between city and coordinates, and show or
 * hide the third person on the compatibility form.
 */
(function () {
  "use strict";

  /* ── Place entry: city or coordinates, scoped per person block ───────── */

  function wireSegmented(scope) {
    var tabs = scope.querySelectorAll('.segmented [data-tab]');
    if (!tabs.length) return;

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var wanted = tab.getAttribute('data-tab');

        tabs.forEach(function (t) {
          t.setAttribute('aria-selected', String(t === tab));
        });

        scope.querySelectorAll('[data-panel]').forEach(function (panel) {
          var match = panel.getAttribute('data-panel') === wanted;
          panel.classList.toggle('panel-hidden', !match);
          // Clear the inputs we are hiding, so a half-filled alternative
          // cannot silently win on the server.
          if (!match) {
            panel.querySelectorAll('input').forEach(function (input) {
              input.value = '';
            });
          }
        });
      });
    });
  }

  document.querySelectorAll('[data-person]').forEach(wireSegmented);

  /* ── Third person ────────────────────────────────────────────────────── */

  var thirdSelect = document.getElementById('third');
  var slot = document.getElementById('person-c-slot');
  var people = document.getElementById('people');

  if (thirdSelect && slot && people) {
    var sync = function () {
      var on = thirdSelect.value === 'yes';
      slot.classList.toggle('panel-hidden', !on);
      people.classList.toggle('people--three', on);
      // A hidden third person must not carry a required attribute, or the
      // form will refuse to submit for reasons the user cannot see.
      slot.querySelectorAll('input').forEach(function (input) {
        if (input.type === 'date' || input.type === 'time') {
          if (on) {
            input.setAttribute('required', '');
          } else {
            input.removeAttribute('required');
            input.value = '';
          }
        } else if (!on) {
          input.value = '';
        }
      });
    };
    thirdSelect.addEventListener('change', sync);
    sync();
  }

  /* ── Submit feedback ─────────────────────────────────────────────────── */

  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      var button = form.querySelector('button[type="submit"]');
      if (!button) return;
      // Re-enable shortly after: a PDF download does not navigate away, so a
      // permanently disabled button would strand the user on this page.
      button.disabled = true;
      var original = button.textContent;
      button.textContent = 'Computing…';
      window.setTimeout(function () {
        button.disabled = false;
        button.textContent = original;
      }, 6000);
    });
  });
})();
