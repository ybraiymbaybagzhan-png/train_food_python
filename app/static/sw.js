const CACHE_NAME = 'dar-res-cache-v7';

// Жолаушы беттері — желі жоқ кезде кэштен ашылады (қызметкер беттері кэштелмейді)
const OFFLINE_PAGES = ['/', '/menu', '/cart', '/checkout', '/about', '/lunchboxes'];
function isPassengerPage(pathname) {
  return OFFLINE_PAGES.includes(pathname) || pathname.startsWith('/order/');
}
const STATIC_ASSETS = [
  '/',
  '/menu',
  '/static/style.css',
  '/static/manifest.json',
  '/static/assets/dar_res_logo.jpeg',
  '/static/assets/hero_ambience.jpg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Фондық синхрондау: желі қайта пайда болғанда ашық бетке кезекті жіберуді бұйырамыз
// (кезек localStorage-та сақталады, оған service worker қол жеткізе алмайды)
self.addEventListener('sync', (event) => {
  if (event.tag === 'flush-orders') {
    event.waitUntil(
      self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
        clients.forEach((c) => c.postMessage({ type: 'flush-orders' }));
      })
    );
  }
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  // NEVER cache API orders, auth, lunchboxes, or WebSocket connections
  if (
    url.pathname.startsWith('/api/orders') ||
    url.pathname.startsWith('/api/auth') ||
    url.pathname.startsWith('/api/lunchboxes') ||
    url.pathname.startsWith('/ws')
  ) {
    return;
  }

  // Network-first for dynamic menu data with cache fallback
  if (url.pathname.startsWith('/api/menu')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Network-first for static assets (суреттер ауыстырылса, бірден жаңасы көрінеді); желі жоқ болса — кэштен
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      fetch(event.request, { cache: 'no-cache' })
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return networkResponse;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Network-first for pages: сәтті жауап кэшке түседі, желі жоқ болса кэштен (іздеу параметрінсіз) беріледі
  const cacheable = event.request.mode === 'navigate' && isPassengerPage(url.pathname);
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (cacheable && response && response.status === 200 && !response.redirected) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request, { ignoreSearch: true })
          .then((r) => r || caches.match('/menu', { ignoreSearch: true }))
          .then((r) => r || caches.match('/'));
      })
  );
});
