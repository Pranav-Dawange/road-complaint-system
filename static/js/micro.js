/**
 * micro.js — Shared micro-interactions for Road Complaint System
 * Include in every page: <script src="/static/js/micro.js"></script>
 */
(function () {
  'use strict';

  /* ── 1. Ripple on every .btn-grad (event delegation) ──── */
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-grad');
    if (!btn) return;
    const s = document.createElement('span');
    const r = btn.getBoundingClientRect();
    const z = Math.max(r.width, r.height);
    s.className = 'ripple-span';
    s.style.cssText =
      `width:${z}px;height:${z}px;` +
      `left:${e.clientX - r.left - z / 2}px;` +
      `top:${e.clientY - r.top  - z / 2}px`;
    btn.appendChild(s);
    setTimeout(() => s.remove(), 700);
  });

  /* ── 2. Staggered fade-up on all .glass-card elements ─── */
  function staggerCards() {
    const cards = document.querySelectorAll(
      '.glass-card:not(.fade-up), .glass-card-sm:not(.fade-up)'
    );
    cards.forEach((card, i) => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(22px)';
      card.style.transition = `opacity .42s cubic-bezier(.16,1,.3,1) ${i * 0.08}s,
                               transform .42s cubic-bezier(.16,1,.3,1) ${i * 0.08}s`;
      /* Force reflow, then animate */
      requestAnimationFrame(() => requestAnimationFrame(() => {
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }));
    });
  }

  /* ── 3. Generic number count-up (exposed globally) ──────── */
  window.countUp = function (el, target, duration) {
    if (!el) return;
    duration = duration || 750;
    const start = performance.now();
    (function step(now) {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(ease * target);
      if (p < 1) requestAnimationFrame(step);
    })(performance.now());
  };

  /* ── 4. Table row stagger on dynamic renders ─────────────
     Call window.staggerRows(tbody) after injecting table HTML */
  window.staggerRows = function (tbody) {
    if (!tbody) return;
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((tr, i) => {
      tr.style.opacity = '0';
      tr.style.transform = 'translateY(10px)';
      tr.style.transition = `opacity .28s ease ${i * 0.03}s,
                             transform .28s ease ${i * 0.03}s`;
      requestAnimationFrame(() => requestAnimationFrame(() => {
        tr.style.opacity = '1';
        tr.style.transform = 'translateY(0)';
      }));
    });
  };

  /* ── 5. Input shake helper (exposed globally) ────────────
     Call window.shakeEl(element) to trigger validation shake */
  window.shakeEl = function (el) {
    if (!el) return;
    el.classList.remove('shake');
    void el.offsetWidth; /* reflow to restart animation */
    el.classList.add('shake');
    el.addEventListener('animationend', () => el.classList.remove('shake'), { once: true });
  };

  /* ── 6. Auto-focus glow on glass inputs ─────────────────── */
  document.addEventListener('focusin', function (e) {
    if (e.target.classList.contains('glass-input') ||
        e.target.classList.contains('glass-select')) {
      e.target.style.borderColor = 'var(--primary)';
      e.target.style.boxShadow   = '0 0 0 3px rgba(26,86,219,.22)';
    }
  });
  document.addEventListener('focusout', function (e) {
    if (e.target.classList.contains('glass-input') ||
        e.target.classList.contains('glass-select')) {
      e.target.style.borderColor = '';
      e.target.style.boxShadow   = '';
    }
  });

  /* ── 7. Smooth scroll for all internal anchor links ──────── */
  document.addEventListener('click', function (e) {
    const a = e.target.closest('a[href^="#"]');
    if (a) { e.preventDefault(); document.querySelector(a.getAttribute('href'))?.scrollIntoView({ behavior: 'smooth' }); }
  });

  /* ── Run stagger after DOM is ready ─────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', staggerCards);
  } else {
    staggerCards();
  }

})();
