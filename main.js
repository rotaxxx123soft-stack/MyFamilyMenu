/* My family — онлайн-меню. Без библиотек. */
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  var topbar = document.getElementById("topbar");
  var toTop = document.querySelector(".to-top");
  var nav = document.querySelector(".nav");
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var sections = Array.prototype.slice.call(document.querySelectorAll(".menu .section"));

  /* 1. Высота шапки → CSS-переменная (для точной прокрутки к разделам) */
  function setHeaderHeight() {
    if (topbar) root.style.setProperty("--header-h", topbar.offsetHeight + "px");
  }
  setHeaderHeight();
  if ("ResizeObserver" in window && topbar) {
    new ResizeObserver(setHeaderHeight).observe(topbar);
  } else {
    window.addEventListener("resize", setHeaderHeight);
  }

  /* 2. Фотографии: плавное появление и запасная плашка, если фото не загрузилось */
  var photos = document.querySelectorAll(".dish__media img, .drink__photo img");
  Array.prototype.forEach.call(photos, function (img) {
    function onLoad() { img.classList.add("is-loaded"); }
    function onError() {
      // Убираем сломанную картинку — под ней остаётся аккуратная плашка с иконкой
      img.remove();
    }
    if (img.complete) {
      if (img.naturalWidth > 0) onLoad(); else onError();
    } else {
      img.addEventListener("load", onLoad, { once: true });
      img.addEventListener("error", onError, { once: true });
    }
  });
  // Фото в главном экране: при ошибке остаётся тёплый градиент рамки
  Array.prototype.forEach.call(document.querySelectorAll(".frame img"), function (img) {
    if (img.complete && img.naturalWidth === 0) img.remove();
    else img.addEventListener("error", function () { img.remove(); }, { once: true });
  });

  /* 3. Шапка с тенью после начала прокрутки и кнопка «Наверх» */
  var ticking = false;
  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    if (topbar) topbar.classList.toggle("is-scrolled", y > 8);
    if (toTop) toTop.classList.toggle("is-visible", y > 900);
    ticking = false;
  }
  window.addEventListener("scroll", function () {
    if (!ticking) {
      window.requestAnimationFrame(onScroll);
      ticking = true;
    }
  }, { passive: true });
  onScroll();

  /* 4. Подсветка текущего раздела в навигации */
  function setActive(id) {
    chips.forEach(function (chip) {
      var active = chip.getAttribute("href") === "#" + id;
      chip.classList.toggle("is-active", active);
      if (active) {
        chip.setAttribute("aria-current", "true");
        // На телефоне докручиваем ленту разделов, чтобы активный был виден
        if (nav && nav.scrollWidth > nav.clientWidth) {
          var left = chip.offsetLeft - (nav.clientWidth - chip.offsetWidth) / 2;
          nav.scrollTo({ left: Math.max(0, left), behavior: "smooth" });
        }
      } else {
        chip.removeAttribute("aria-current");
      }
    });
  }

  function updateActive() {
    var line = (topbar ? topbar.offsetHeight : 72) + window.innerHeight * 0.25;
    var current = null;
    sections.forEach(function (s) {
      if (s.getBoundingClientRect().top <= line) current = s.id;
    });
    // В самом низу страницы активен последний раздел
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4 && sections.length) {
      current = sections[sections.length - 1].id;
    }
    if (current !== updateActive.last) {
      updateActive.last = current;
      if (current) setActive(current);
      else chips.forEach(function (c) { c.classList.remove("is-active"); c.removeAttribute("aria-current"); });
    }
  }
  var spyTicking = false;
  window.addEventListener("scroll", function () {
    if (!spyTicking) {
      window.requestAnimationFrame(function () { updateActive(); spyTicking = false; });
      spyTicking = true;
    }
  }, { passive: true });
  window.addEventListener("resize", updateActive);
  updateActive();

  /* 5. Плавное появление элементов при прокрутке */
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduceMotion && "IntersectionObserver" in window) {
    var items = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
    var below = items.filter(function (el) {
      // Скрываем только то, что ниже первого экрана — первый экран виден сразу
      return el.getBoundingClientRect().top > window.innerHeight;
    });

    // Небольшая «лесенка» для карточек в одной сетке
    below.forEach(function (el) {
      var parent = el.parentElement;
      if (parent && (parent.classList.contains("dishes") || parent.classList.contains("drinks"))) {
        var index = Array.prototype.indexOf.call(parent.children, el);
        el.style.setProperty("--delay", (index % 3) * 90 + "ms");
      }
      el.classList.add("reveal-pending");
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    below.forEach(function (el) { io.observe(el); });

    // При быстром переходе по разделам показываем всё, что уже проехали
    var catchUp = false;
    window.addEventListener("scroll", function () {
      if (catchUp) return;
      catchUp = true;
      window.requestAnimationFrame(function () {
        below.forEach(function (el) {
          if (!el.classList.contains("is-in") && el.getBoundingClientRect().bottom < 0) {
            el.classList.add("is-in");
            io.unobserve(el);
          }
        });
        catchUp = false;
      });
    }, { passive: true });
  }
})();
