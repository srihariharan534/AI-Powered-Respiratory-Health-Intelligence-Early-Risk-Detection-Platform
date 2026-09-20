/**
 * NEXUS Field PWA Service Worker (Phase 24)
 * Handles offline application shell caching, static assets, navigation fallbacks,
 * safe network-only API routing, and Background Sync event delegation.
 */

const CACHE_PREFIX = 'nexus-field-';
const CACHE_VERSION = 'v1';
const SHELL_CACHE = `${CACHE_PREFIX}shell-${CACHE_VERSION}`;
const ASSETS_CACHE = `${CACHE_PREFIX}assets-${CACHE_VERSION}`;
const ACTIVE_CACHES = [SHELL_CACHE, ASSETS_CACHE];

const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

const OUTBOX_SYNC_TAG = 'nexus-field-outbox-sync';

// 1. INSTALL LIFECYCLE: Precache App Shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.warn('Precache error in Service Worker install:', err);
      })
  );
});

// 2. ACTIVATE LIFECYCLE: Clean up obsolete NEXUS caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => {
        return Promise.all(
          keys.map((key) => {
            // Purge only obsolete nexus-field- caches (NEVER touch IndexedDB)
            if (key.startsWith(CACHE_PREFIX) && !ACTIVE_CACHES.includes(key)) {
              return caches.delete(key);
            }
            return Promise.resolve(false);
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// 3. FETCH LIFECYCLE: Strategy Routing
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Ignore non-GET requests (e.g. POSTs are handled by IndexedDB Outbox in Phase 23)
  if (request.method !== 'GET') {
    return;
  }

  // Strategy A: Operational API Requests (/api/*) -> STRICTLY NetworkOnly
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(request));
    return;
  }

  // Strategy B: Navigation requests (HTML pages) -> NetworkFirst with fallback to /index.html
  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cached) => {
            return cached || caches.match('/index.html');
          });
        })
    );
    return;
  }

  // Strategy C: Static assets (JS, CSS, images, icons, fonts) -> CacheFirst
  if (
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'image' ||
    request.destination === 'font' ||
    url.pathname.startsWith('/assets/')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const clone = networkResponse.clone();
            caches.open(ASSETS_CACHE).then((cache) => cache.put(request, clone));
          }
          return networkResponse;
        });
      })
    );
    return;
  }
});

// 4. BACKGROUND SYNC LIFECYCLE: Trigger event delegation to active clients
self.addEventListener('sync', (event) => {
  if (event.tag === OUTBOX_SYNC_TAG) {
    event.waitUntil(
      self.clients.matchAll({ includeUncontrolled: true, type: 'window' }).then((clients) => {
        clients.forEach((client) => {
          client.postMessage({
            type: 'OUTBOX_SYNC_TRIGGERED',
            tag: event.tag,
            timestamp: new Date().toISOString(),
          });
        });
      })
    );
  }
});

// 5. CONTROLLED MESSAGING LIFECYCLE
self.addEventListener('message', (event) => {
  const data = event.data;
  if (!data || typeof data !== 'object') return;

  if (data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (data.type === 'GET_SW_INFO' && event.source) {
    event.source.postMessage({
      type: 'SW_INFO_RESPONSE',
      version: CACHE_VERSION,
      activeCaches: ACTIVE_CACHES,
    });
  }
});
