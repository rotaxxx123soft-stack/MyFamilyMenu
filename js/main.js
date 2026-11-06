(() => {
  /* Класс ставит сам скрипт: если он не запустится, фото и карточки останутся видимыми */
  document.documentElement.classList.add('js');

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Плавное проявление фотографий и запасной вид, если фото не загрузилось */
  document.querySelectorAll('.dish__photo img').forEach((img) => {
    const markLoaded = () => img.classList.add('is-loaded');
    const markFailed = () => {
      img.hidden = true;
      img.parentElement.classList.add('is-failed');
    };

    if (img.complete) {
      img.naturalWidth > 0 ? markLoaded() : markFailed();
    } else {
      img.addEventListener('load', markLoaded, { once: true });
      img.addEventListener('error', markFailed, { once: true });
    }
  });

  /* Появление элементов при прокрутке */
  const reveals = document.querySelectorAll('.reveal');
  const show = (el) => {
    el.classList.add('is-visible');
    setTimeout(() => el.classList.add('is-done'), 1100);
  };

  if (reducedMotion || !('IntersectionObserver' in window)) {
    reveals.forEach(show);
  } else {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        show(entry.target);
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

    reveals.forEach((el) => revealObserver.observe(el));
  }

  /* Подсветка текущего раздела в навигации */
  const cats = document.querySelector('.cats');
  const links = [...cats.querySelectorAll('a')];
  const sections = links.map((link) => document.querySelector(link.getAttribute('href')));
  const header = document.querySelector('.site-header');
  let activeLink = null;

  const setActive = (link) => {
    if (link === activeLink) return;
    if (activeLink) {
      activeLink.classList.remove('is-active');
      activeLink.removeAttribute('aria-current');
    }
    if (link) {
      link.classList.add('is-active');
      link.setAttribute('aria-current', 'true');
    }
    activeLink = link;

    /* На телефоне прокручиваем саму полосу разделов, не страницу */
    if (link && cats.scrollWidth > cats.clientWidth) {
      cats.scrollTo({
        left: link.offsetLeft - (cats.clientWidth - link.offsetWidth) / 2,
        behavior: reducedMotion ? 'auto' : 'smooth',
      });
    }
  };

  let ticking = false;
  const update = () => {
    ticking = false;
    header.classList.toggle('is-stuck', window.scrollY > 8);

    const line = header.getBoundingClientRect().bottom + window.innerHeight * 0.2;
    let current = null;
    sections.forEach((section, i) => {
      if (section.getBoundingClientRect().top <= line) current = links[i];
    });
    setActive(current);
  };

  const requestUpdate = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  };

  window.addEventListener('scroll', requestUpdate, { passive: true });
  window.addEventListener('resize', requestUpdate, { passive: true });
  update();
})();
