const CACHE_NAME = 'dar-res-cache-v6';
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

self.addEventListener('fetch', (event) => {
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

  // Network-first for pages with correct fallback to root '/'
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request).then((r) => r || caches.match('/'));
    })
  );
});
