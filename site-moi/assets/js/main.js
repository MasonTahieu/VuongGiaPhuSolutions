/* Vuong Gia Phu Solutions – page router, VI/EN switcher + UI helpers (no dependencies)
 *
 * Every page is a real, pre-built HTML file (/, /cong-nghe/, /thiet-bi/, …) so search engines index
 * each one separately. In the browser, links between pages are handled here without a full reload:
 * the target page's <section data-view> is fetched once, inserted and shown.
 */
(function () {
  'use strict';

  var root = document.documentElement;
  var header = document.querySelector('.site-header');
  var nav = document.getElementById('site-nav');
  var navToggle = document.querySelector('.nav-toggle');
  var main = document.getElementById('main');
  var contactSection = document.getElementById('lien-he');
  var metaDescription = document.querySelector('meta[name="description"]');
  var canonical = document.querySelector('link[rel="canonical"]');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var STYLESHEET = document.querySelector('link[rel="stylesheet"][href^="/assets/css/"]').getAttribute('href');

  var config = JSON.parse(document.getElementById('vgp-pages').textContent);
  var SITE = config.site;
  var byRoute = {};
  var byPath = {};
  config.pages.forEach(function (p) { byRoute[p.route] = p; byPath[p.path] = p; });
  var current = document.body.getAttribute('data-route');

  // ---------- Language ----------
  var EN = window.I18N_EN || {};
  var VI = {  // the rest of the Vietnamese is in the HTML
    'js.menu.open': 'Mở menu', 'js.menu.close': 'Đóng menu',
    'js.viewer.label': 'Xem ảnh lớn', 'js.viewer.close': 'Đóng', 'js.viewer.prev': 'Ảnh trước', 'js.viewer.next': 'Ảnh sau'
  };
  var lang = 'vi';
  var originalHtml = new Map();   // element -> Vietnamese innerHTML
  var originalAttrs = new Map();  // element -> { attr: Vietnamese value }
  var originalText = new Map();   // element -> Vietnamese text or alt (data-en / data-en-alt)

  function t(key) {
    return lang === 'en' && EN[key] != null ? EN[key] : VI[key];
  }

  function readSavedLang() {
    var fromUrl = new URLSearchParams(location.search).get('lang');
    if (fromUrl === 'en' || fromUrl === 'vi') return fromUrl;
    try { return localStorage.getItem('lang') === 'en' ? 'en' : 'vi'; } catch (e) { return 'vi'; }
  }

  function langQuery() {
    return lang === 'en' ? '?lang=en' : '';
  }

  // Title, description and canonical URL of the current page in the current language
  function updateMeta() {
    var page = byRoute[current];
    document.title = page.title[lang] || page.title.vi;
    metaDescription.setAttribute('content', page.description[lang] || page.description.vi);
    canonical.href = SITE + page.path + langQuery();
    document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(function (link) {
      link.href = SITE + page.path + (link.hreflang === 'en' ? '?lang=en' : '');
    });
  }

  function applyLang(next) {
    lang = next;
    root.lang = next;

    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      if (!originalHtml.has(el)) originalHtml.set(el, el.innerHTML);
      var value = next === 'en' ? EN[el.getAttribute('data-i18n')] : null;
      var html = value != null ? value : originalHtml.get(el);
      if (el.innerHTML !== html) el.innerHTML = html;
    });

    document.querySelectorAll('[data-i18n-attr]').forEach(function (el) {
      if (!originalAttrs.has(el)) originalAttrs.set(el, {});
      var saved = originalAttrs.get(el);
      el.getAttribute('data-i18n-attr').split(';').forEach(function (pair) {
        var parts = pair.split(':');
        var attr = parts[0].trim();
        var key = parts[1].trim();
        if (!(attr in saved)) saved[attr] = el.getAttribute(attr);
        var value = next === 'en' ? EN[key] : null;
        el.setAttribute(attr, value != null ? value : saved[attr]);
      });
    });

    // Inline translations: data-en="…" (text) and data-en-alt="…" (image alt), used by generated captions
    document.querySelectorAll('[data-en]').forEach(function (el) {
      if (!originalText.has(el)) originalText.set(el, el.textContent);
      el.textContent = next === 'en' ? el.getAttribute('data-en') : originalText.get(el);
    });
    document.querySelectorAll('[data-en-alt]').forEach(function (el) {
      if (!originalText.has(el)) originalText.set(el, el.getAttribute('alt'));
      el.setAttribute('alt', next === 'en' ? el.getAttribute('data-en-alt') : originalText.get(el));
    });

    document.querySelectorAll('[data-set-lang]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', String(btn.getAttribute('data-set-lang') === next));
    });

    updateMeta();
    navToggle.setAttribute('aria-label', t(nav.classList.contains('open') ? 'js.menu.close' : 'js.menu.open'));
    root.classList.remove('i18n-pending');
  }

  function setLang(next) {
    if (next === lang) return;
    applyLang(next);
    try { localStorage.setItem('lang', next); } catch (e) { /* private mode: choice lasts this visit only */ }
    // Keep the URL shareable: ?lang=en for English, no parameter for Vietnamese
    var url = new URL(location.href);
    if (next === 'en') url.searchParams.set('lang', 'en'); else url.searchParams.delete('lang');
    history.replaceState(history.state, '', url);
  }

  document.querySelectorAll('[data-set-lang]').forEach(function (btn) {
    btn.addEventListener('click', function () { setLang(btn.getAttribute('data-set-lang')); });
  });

  // ---------- Router ----------
  function pageForPath(pathname) {
    pathname = pathname.replace(/index\.html$/, '');
    if (pathname.slice(-1) !== '/') pathname += '/';
    return byPath[pathname] || null;
  }

  function scrollToEl(el) {
    requestAnimationFrame(function () {
      el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    });
  }

  // A privacy-policy anchor from the other language (#pp-3 <-> #pp-en-3) points to a hidden block
  function findTarget(hash) {
    var id = decodeURIComponent((hash || '').replace(/^#/, ''));
    if (!id) return null;
    var target = document.getElementById(id);
    var block = target && target.closest('[data-lang]');
    if (block && block.getAttribute('data-lang') !== lang) {
      var twin = lang === 'en' ? id.replace(/^pp-(\d+)$/, 'pp-en-$1') : id.replace(/^pp-en-(\d+)$/, 'pp-$1');
      return document.getElementById(twin) || target;
    }
    return target;
  }

  function viewFor(route) {
    return document.querySelector('[data-view="' + route + '"]');
  }

  // Fetch another page once and keep its view in the DOM (hidden) for next time
  function loadView(page) {
    var existing = viewFor(page.route);
    if (existing) return Promise.resolve(existing);
    return fetch(page.path, { credentials: 'same-origin' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.text();
      })
      .then(function (text) {
        var doc = new DOMParser().parseFromString(text, 'text/html');
        // While the redesign is rolled out page by page, a page on another stylesheet gets a full load
        if (!doc.querySelector('link[rel="stylesheet"][href="' + STYLESHEET + '"]')) throw new Error('other stylesheet');
        var fresh = doc.querySelector('[data-view="' + page.route + '"]');
        if (!fresh) throw new Error('view not found');
        fresh.hidden = true;
        var node = document.importNode(fresh, true);
        main.insertBefore(node, contactSection);
        applyLang(lang);  // translate the new content
        return node;
      });
  }

  function activate(route) {
    document.querySelectorAll('[data-view]').forEach(function (v) {
      v.hidden = v.getAttribute('data-view') !== route;
    });
    var nav = (byRoute[route] && byRoute[route].nav) || route;  // brand pages highlight "Thiết bị & Thương hiệu"
    document.querySelectorAll('[data-route]').forEach(function (a) {
      var active = a.getAttribute('data-route') === nav;
      a.classList.toggle('active', active);
      if (active) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    current = route;
    document.body.setAttribute('data-route', route);
    updateMeta();
  }

  var navToken = 0;
  function go(url, push, savedY) {
    var page = pageForPath(url.pathname);
    if (!page) { location.href = url.href; return; }
    var token = ++navToken;
    loadView(page).then(function () {
      if (token !== navToken) return;  // a newer navigation started meanwhile
      var changed = page.route !== current;
      if (changed) activate(page.route);
      if (push) {
        history.replaceState({ y: window.scrollY }, '');
        history.pushState({ y: 0 }, '', page.path + langQuery() + url.hash);
      }
      var target = findTarget(url.hash);
      if (typeof savedY === 'number') window.scrollTo(0, savedY);
      else if (target) scrollToEl(target);
      else window.scrollTo(0, 0);
      if (changed) main.focus({ preventScroll: true });
    }).catch(function () {
      location.href = url.href;  // fall back to a normal page load
    });
  }

  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href]');
    if (!a) return;
    closeNav();
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ||
        a.target === '_blank' || a.hasAttribute('download')) return;
    var url = new URL(a.getAttribute('href'), location.href);
    if (url.origin !== location.origin || !pageForPath(url.pathname)) return;
    e.preventDefault();

    if (pageForPath(url.pathname).route === current) {
      // Same page: scroll to the anchor (or the top) ourselves, so repeat clicks and language twins work
      var target = findTarget(url.hash);
      if (url.hash && url.hash !== location.hash) {
        history.replaceState({ y: window.scrollY }, '');
        history.pushState({ y: null }, '', url.hash);
      }
      if (target) scrollToEl(target);
      else window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
      return;
    }
    go(url, true);
  });

  window.addEventListener('popstate', function (e) {
    var y = e.state && typeof e.state.y === 'number' ? e.state.y : undefined;
    go(new URL(location.href), false, y);
  });

  window.addEventListener('hashchange', function () {
    var target = findTarget(location.hash);
    if (target) scrollToEl(target);
  });

  // ---------- Start ----------
  applyLang(readSavedLang());

  // Old single-page links (/#cong-nghe, /#noi-that, …) now live at their own URL
  var legacy = byRoute[decodeURIComponent(location.hash.slice(1))];
  if (current === 'trang-chu' && legacy && legacy.route !== current) {
    location.replace(legacy.path + location.search);
    return;
  }
  if (location.hash) {
    var initialTarget = findTarget(location.hash);
    if (initialTarget) scrollToEl(initialTarget);
  }

  // ---------- Mobile navigation ----------
  function closeNav() {
    nav.classList.remove('open');
    navToggle.setAttribute('aria-expanded', 'false');
    navToggle.setAttribute('aria-label', t('js.menu.open'));
    navToggle.querySelector('use').setAttribute('href', '#i-menu');
  }
  navToggle.addEventListener('click', function () {
    var open = !nav.classList.contains('open');
    if (!open) return closeNav();
    nav.classList.add('open');
    navToggle.setAttribute('aria-expanded', 'true');
    navToggle.setAttribute('aria-label', t('js.menu.close'));
    navToggle.querySelector('use').setAttribute('href', '#i-close');
    // The links sit before the toggle in the markup, so Tab would skip them: move focus into the menu
    nav.querySelector('a').focus();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' || !nav.classList.contains('open')) return;
    closeNav();
    navToggle.focus();
  });
  // Close the open menu once keyboard focus leaves the header
  header.addEventListener('focusout', function (e) {
    if (nav.classList.contains('open') && e.relatedTarget && !header.contains(e.relatedTarget)) closeNav();
  });

  // ---------- Header shadow + back-to-top ----------
  var toTop = document.querySelector('.fab-top');
  function onScroll() {
    var y = window.scrollY;
    header.classList.toggle('scrolled', y > 8);
    toTop.hidden = y < 600;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });

  // ---------- Lazy-load Google Maps ----------
  var mapFrame = document.querySelector('.map iframe[data-src]');
  if (mapFrame) {
    var loadMap = function () { mapFrame.src = mapFrame.getAttribute('data-src'); mapFrame.removeAttribute('data-src'); };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { loadMap(); io.disconnect(); }
      }, { rootMargin: '300px' });
      io.observe(mapFrame);
    } else {
      loadMap();
    }
  }

  // ---------- Photo viewer: a project photo opens large; tap or click zooms in at that point, drag pans,
  // swipe or arrow keys browse. The large file only loads when opened; without <dialog> the link opens the image.
  var viewer = null;

  function buildViewer() {
    var dlg = document.createElement('dialog');
    dlg.className = 'viewer';
    dlg.innerHTML =
      '<div class="viewer-stage"><img class="viewer-img" alt=""></div>' +
      '<p class="viewer-caption" aria-live="polite"></p>' +
      '<button type="button" class="viewer-btn viewer-close"><svg class="icon"><use href="#i-close"/></svg></button>' +
      '<button type="button" class="viewer-btn viewer-prev"><svg class="icon"><use href="#i-arrow"/></svg></button>' +
      '<button type="button" class="viewer-btn viewer-next"><svg class="icon"><use href="#i-arrow"/></svg></button>';
    document.body.appendChild(dlg);
    var stage = dlg.querySelector('.viewer-stage');
    var img = dlg.querySelector('.viewer-img');
    var caption = dlg.querySelector('.viewer-caption');
    var api = { links: [], index: 0 };
    var startX = null;

    function aim(x, y) {
      var r = stage.getBoundingClientRect();
      var px = (x - r.left - img.offsetLeft) / img.offsetWidth * 100;
      var py = (y - r.top - img.offsetTop) / img.offsetHeight * 100;
      img.style.transformOrigin = Math.max(0, Math.min(100, px)) + '% ' + Math.max(0, Math.min(100, py)) + '%';
    }
    function zoom(on, x, y) {
      if (on) aim(x, y);
      stage.classList.toggle('zoomed', on);
    }
    api.show = function (i) {
      var n = api.links.length;
      api.index = (i + n) % n;
      var link = api.links[api.index];
      zoom(false);
      img.src = link.getAttribute('href');
      img.alt = link.querySelector('img').alt;
      caption.textContent = link.closest('figure').querySelector('figcaption').textContent;
      dlg.setAttribute('aria-label', t('js.viewer.label'));
      dlg.querySelector('.viewer-close').setAttribute('aria-label', t('js.viewer.close'));
      dlg.querySelector('.viewer-prev').setAttribute('aria-label', t('js.viewer.prev'));
      dlg.querySelector('.viewer-next').setAttribute('aria-label', t('js.viewer.next'));
      dlg.classList.toggle('single', n < 2);
      if (!dlg.open) {
        dlg.showModal();
        root.classList.add('viewer-open');
      }
    };

    img.addEventListener('click', function (e) {
      zoom(!stage.classList.contains('zoomed'), e.clientX, e.clientY);
    });
    stage.addEventListener('mousemove', function (e) {
      if (stage.classList.contains('zoomed')) aim(e.clientX, e.clientY);
    });
    stage.addEventListener('click', function (e) {
      if (e.target === stage) dlg.close();  // click beside the photo
    });
    stage.addEventListener('touchstart', function (e) {
      startX = e.touches.length === 1 ? e.touches[0].clientX : null;
    }, { passive: true });
    stage.addEventListener('touchmove', function (e) {
      if (stage.classList.contains('zoomed') && e.touches.length === 1) {
        e.preventDefault();
        aim(e.touches[0].clientX, e.touches[0].clientY);
      }
    }, { passive: false });
    stage.addEventListener('touchend', function (e) {
      if (startX === null || stage.classList.contains('zoomed')) return;
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) api.show(api.index + (dx < 0 ? 1 : -1));
    });
    dlg.querySelector('.viewer-close').addEventListener('click', function () { dlg.close(); });
    dlg.querySelector('.viewer-prev').addEventListener('click', function () { api.show(api.index - 1); });
    dlg.querySelector('.viewer-next').addEventListener('click', function () { api.show(api.index + 1); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') api.show(api.index + 1);
      if (e.key === 'ArrowLeft') api.show(api.index - 1);
    });
    dlg.addEventListener('close', function () {
      root.classList.remove('viewer-open');
      zoom(false);
    });
    return api;
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('[data-zoom]');
    if (!link || typeof HTMLDialogElement === 'undefined' ||
        e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    viewer = viewer || buildViewer();
    viewer.links = Array.prototype.slice.call(link.closest('.project-gallery').querySelectorAll('[data-zoom]'));
    viewer.show(viewer.links.indexOf(link));
  });

  document.getElementById('year').textContent = new Date().getFullYear();
})();
