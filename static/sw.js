// Service Worker for Institut ILAS PWA
const CACHE_NAME = 'ilas-pwa-v1.0.3';
const STATIC_ASSETS = [
  '/',
  '/login',
  '/offline.html',
  '/manifest.json',
  '/static/style.css',
  '/static/favicon.svg',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use try/catch style fetching to prevent one failure from aborting install
      return Promise.allSettled(
        STATIC_ASSETS.map((url) =>
          cache.add(url).catch((err) => {
            console.warn('[PWA SW] Pre-cache failed for', url, err);
          })
        )
      );
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 0. NEVER intercept localhost or loopback - always direct to native server
  if (url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
    return;
  }

  // Only handle HTTP/HTTPS GET requests
  if (req.method !== 'GET' || !url.protocol.startsWith('http')) {
    return;
  }

  // 1. Navigation requests (HTML pages): Network-first with retry & offline fallback
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(async () => {
        // Quick retry once after 400ms to ignore micro-drops
        try {
          await new Promise((res) => setTimeout(res, 400));
          return await fetch(req);
        } catch (_) {
          const cached = await caches.match(req);
          return cached || (await caches.match('/offline.html'));
        }
      })
    );
    return;
  }

  // 2. Static assets (/static/): Stale-While-Revalidate
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cachedResp) => {
        const fetchPromise = fetch(req).then((networkResp) => {
          if (networkResp && networkResp.status === 200) {
            const respClone = networkResp.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(req, respClone);
            });
          }
          return networkResp;
        }).catch(() => null);

        return cachedResp || fetchPromise;
      })
    );
    return;
  }

  // 3. All other requests: Network first
  event.respondWith(
    fetch(req).catch(() => caches.match(req))
  );
});
