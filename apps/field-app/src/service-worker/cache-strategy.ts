/**
 * Service Worker Cache Strategy Engine (Phase 24)
 * Provides cache versioning, routing strategies (NetworkFirst, CacheFirst, NetworkOnly),
 * and selective cache cleanup for NEXUS Field PWA.
 */

export const CACHE_PREFIX = 'nexus-field-';
export const CACHE_VERSION = 'v1';
export const SHELL_CACHE_NAME = `${CACHE_PREFIX}shell-${CACHE_VERSION}`;
export const ASSETS_CACHE_NAME = `${CACHE_PREFIX}assets-${CACHE_VERSION}`;

export const CRITICAL_APP_SHELL: string[] = [
  '/',
  '/index.html',
  '/manifest.json',
];

export interface ICacheStrategy {
  name: string;
  handle(request: Request): Promise<Response>;
}

/**
 * NetworkFirst Strategy: Attempts network fetch first; falls back to cached response.
 * Used for navigation / HTML shell to ensure latest version when online,
 * while allowing offline application launch.
 */
export class NetworkFirstStrategy implements ICacheStrategy {
  name = 'network-first';
  private cacheName: string;

  constructor(cacheName: string = SHELL_CACHE_NAME) {
    this.cacheName = cacheName;
  }

  async handle(request: Request): Promise<Response> {
    try {
      const networkResponse = await fetch(request);
      if (networkResponse && networkResponse.status === 200) {
        const cache = await caches.open(this.cacheName);
        cache.put(request, networkResponse.clone()).catch(() => {});
      }
      return networkResponse;
    } catch (_err) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
      // Fallback to app root shell if available
      const fallbackShell = await caches.match('/index.html');
      if (fallbackShell) {
        return fallbackShell;
      }
      throw new Error('Network and cache unavailable for request.');
    }
  }
}

/**
 * CacheFirst Strategy: Checks cache first; fetches from network if missing and caches it.
 * Used for static immutable assets (hashed JS, CSS, icons, fonts).
 */
export class CacheFirstStrategy implements ICacheStrategy {
  name = 'cache-first';
  private cacheName: string;

  constructor(cacheName: string = ASSETS_CACHE_NAME) {
    this.cacheName = cacheName;
  }

  async handle(request: Request): Promise<Response> {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(this.cacheName);
      cache.put(request, networkResponse.clone()).catch(() => {});
    }
    return networkResponse;
  }
}

/**
 * NetworkOnly Strategy: Never caches the request or response.
 * Strictly enforced for all operational API requests (/api/*) and auth endpoints.
 */
export class NetworkOnlyStrategy implements ICacheStrategy {
  name = 'network-only';

  async handle(request: Request): Promise<Response> {
    return fetch(request);
  }
}

/**
 * Safe Cache Purge Utility
 * Cleans up old NEXUS caches during activation.
 * CRITICAL RULE: Never deletes non-NEXUS caches and NEVER touches IndexedDB.
 */
export async function purgeOldNexusCaches(activeCaches: string[]): Promise<string[]> {
  const allCacheNames = await caches.keys();
  const deletedCaches: string[] = [];

  for (const cacheName of allCacheNames) {
    // Only target caches prefixed with 'nexus-field-' that are not in the active list
    if (cacheName.startsWith(CACHE_PREFIX) && !activeCaches.includes(cacheName)) {
      await caches.delete(cacheName);
      deletedCaches.push(cacheName);
    }
  }

  return deletedCaches;
}
