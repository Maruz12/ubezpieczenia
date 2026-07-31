(() => {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Intro overlay — desktop only "second screen" that rolls up to reveal the site */
  const introOverlay = document.getElementById('introOverlay');
  if (introOverlay) {
    const isDesktop = window.matchMedia('(min-width: 900px)').matches;
    if (!isDesktop || prefersReducedMotion) {
      introOverlay.classList.add('intro-overlay--off');
    } else {
      const HOLD_MS = 1150;
      const RISE_MS = 850;
      document.body.style.overflow = 'hidden';
      requestAnimationFrame(() => introOverlay.classList.add('is-active'));
      setTimeout(() => {
        introOverlay.classList.add('is-rising');
        document.body.style.overflow = '';
      }, HOLD_MS);
      setTimeout(() => {
        introOverlay.classList.add('is-done');
        introOverlay.setAttribute('aria-hidden', 'true');
      }, HOLD_MS + RISE_MS + 50);
    }
  }

  /* Hero entrance. Waits for fonts so the headline doesn't reflow mid-animation, but
     races a short timeout: the h1 is the LCP element and it sits at opacity 0 until
     this fires, so a slow font must never hold up the largest paint. */
  let started = false;
  const start = () => {
    if (started) return;
    started = true;
    document.documentElement.classList.add('is-loaded');
  };
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(start).catch(start);
  } else {
    window.addEventListener('load', start);
  }
  setTimeout(start, 300);

  /* Sticky header state — reads scrollY inside rAF so a fast scroll can't queue
     up a layout read per event. */
  const header = document.getElementById('siteHeader');
  let scrollQueued = false;
  const applyHeaderState = () => {
    scrollQueued = false;
    header.classList.toggle('is-scrolled', window.scrollY > 12);
  };
  applyHeaderState();
  window.addEventListener('scroll', () => {
    if (scrollQueued) return;
    scrollQueued = true;
    requestAnimationFrame(applyHeaderState);
  }, { passive: true });

  /* Mobile nav toggle */
  const navToggle = document.getElementById('navToggle');
  const mobileNav = document.getElementById('mobileNav');
  const closeMobileNav = () => {
    mobileNav.classList.remove('is-open');
    navToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };
  navToggle.addEventListener('click', () => {
    const isOpen = mobileNav.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });
  mobileNav.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMobileNav));

  /* Map facade — swap the placeholder for the real embed only when asked */
  const mapFacade = document.getElementById('mapFacade');
  if (mapFacade) {
    mapFacade.addEventListener('click', () => {
      const iframe = document.createElement('iframe');
      iframe.src = 'https://www.google.com/maps?q=Stolarska+39,+53-205+Wroc%C5%82aw&output=embed';
      iframe.title = 'Mapa — Ubezpieczenia Wrocław Szymon Wanat, Stolarska 39';
      iframe.loading = 'lazy';
      iframe.referrerPolicy = 'no-referrer-when-downgrade';
      iframe.setAttribute('allowfullscreen', '');
      mapFacade.replaceWith(iframe);
    }, { once: true });
  }

  /* Scroll reveal */
  const revealTargets = document.querySelectorAll('[data-reveal-scroll]');
  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    revealTargets.forEach((el) => el.classList.add('is-visible'));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
    );
    revealTargets.forEach((el) => io.observe(el));
  }
})();
