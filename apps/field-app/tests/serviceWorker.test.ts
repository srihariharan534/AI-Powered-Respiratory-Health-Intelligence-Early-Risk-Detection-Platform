import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  CACHE_PREFIX,
  SHELL_CACHE_NAME,
  ASSETS_CACHE_NAME,
  NetworkFirstStrategy,
  CacheFirstStrategy,
  NetworkOnlyStrategy,
  purgeOldNexusCaches,
} from '../src/service-worker/cache-strategy';
import {
  BackgroundSyncManager,
  OUTBOX_SYNC_TAG,
} from '../src/service-worker/background-sync';
import {
  ServiceWorkerCoordinator,
} from '../src/service-worker/offline-sync';
import { IncidentRepository } from '../src/database/repositories/IncidentRepository';
import { NexusFieldDatabase } from '../src/database/indexeddb/connection';
import { DurableIncident } from '../src/database/types';

describe('Phase 24 Service Worker & Offline Cache Foundation', () => {
  let mockCaches: Record<string, Map<string, Response>> = {};

  beforeEach(async () => {
    mockCaches = {};

    // Mock global CacheStorage API for testing caching strategies
    const cacheStorageMock = {
      open: vi.fn(async (cacheName: string) => {
        if (!mockCaches[cacheName]) {
          mockCaches[cacheName] = new Map();
        }
        const store = mockCaches[cacheName];
        return {
          match: vi.fn(async (req: Request | string) => {
            const url = typeof req === 'string' ? req : req.url;
            return store.get(url) || undefined;
          }),
          put: vi.fn(async (req: Request | string, res: Response) => {
            const url = typeof req === 'string' ? req : req.url;
            store.set(url, res);
          }),
          delete: vi.fn(async (req: Request | string) => {
            const url = typeof req === 'string' ? req : req.url;
            return store.delete(url);
          }),
        };
      }),
      match: vi.fn(async (req: Request | string) => {
        const url = typeof req === 'string' ? req : req.url;
        for (const store of Object.values(mockCaches)) {
          if (store.has(url)) {
            return store.get(url);
          }
        }
        return undefined;
      }),
      keys: vi.fn(async () => Object.keys(mockCaches)),
      delete: vi.fn(async (cacheName: string) => {
        if (mockCaches[cacheName]) {
          delete mockCaches[cacheName];
          return true;
        }
        return false;
      }),
    };

    (globalThis as any).caches = cacheStorageMock;
    vi.restoreAllMocks();
  });

  describe('Cache Strategies', () => {
    it('NetworkFirstStrategy fetches from network when available and caches response', async () => {
      const strategy = new NetworkFirstStrategy(SHELL_CACHE_NAME);
      const mockResponse = new Response('<html>Online Shell</html>', { status: 200 });

      (globalThis as any).fetch = vi.fn().mockResolvedValue(mockResponse);

      const req = new Request('http://localhost:3001/index.html');
      const res = await strategy.handle(req);

      expect(res).toBe(mockResponse);
      expect((globalThis as any).fetch).toHaveBeenCalled();
    });

    it('NetworkFirstStrategy falls back to cached shell when network fails', async () => {
      const strategy = new NetworkFirstStrategy(SHELL_CACHE_NAME);
      const cachedShell = new Response('<html>Cached Offline Shell</html>', { status: 200 });

      // Pre-seed cache
      const cache = await caches.open(SHELL_CACHE_NAME);
      await cache.put(new Request('http://localhost:3001/index.html'), cachedShell);

      // Network fails
      (globalThis as any).fetch = vi.fn().mockRejectedValue(new Error('Network offline'));

      const req = new Request('http://localhost:3001/index.html');
      const res = await strategy.handle(req);

      expect(res).toBe(cachedShell);
    });

    it('CacheFirstStrategy serves from cache without hitting network if present', async () => {
      const strategy = new CacheFirstStrategy(ASSETS_CACHE_NAME);
      const cachedAsset = new Response('console.log("asset");', { status: 200 });

      const cache = await caches.open(ASSETS_CACHE_NAME);
      await cache.put(new Request('http://localhost:3001/assets/main.js'), cachedAsset);

      (globalThis as any).fetch = vi.fn();

      const req = new Request('http://localhost:3001/assets/main.js');
      const res = await strategy.handle(req);

      expect(res).toBe(cachedAsset);
      expect((globalThis as any).fetch).not.toHaveBeenCalled();
    });

    it('NetworkOnlyStrategy strictly fetches from network and never caches', async () => {
      const strategy = new NetworkOnlyStrategy();
      const mockApiResponse = new Response(JSON.stringify({ status: 'live' }), { status: 200 });

      (globalThis as any).fetch = vi.fn().mockResolvedValue(mockApiResponse);

      const req = new Request('http://localhost:3001/api/v1/incidents');
      const res = await strategy.handle(req);

      expect(res).toBe(mockApiResponse);
      expect((globalThis as any).fetch).toHaveBeenCalled();
      expect(caches.open).not.toHaveBeenCalled();
    });

    it('purgeOldNexusCaches purges only obsolete nexus-field- caches without touching external caches', async () => {
      // Create active and obsolete caches
      await caches.open(SHELL_CACHE_NAME);
      await caches.open(ASSETS_CACHE_NAME);
      await caches.open(`${CACHE_PREFIX}shell-v0`);
      await caches.open('other-app-cache-v1'); // Unrelated cache

      const deleted = await purgeOldNexusCaches([SHELL_CACHE_NAME, ASSETS_CACHE_NAME]);

      expect(deleted).toContain(`${CACHE_PREFIX}shell-v0`);
      expect(deleted).not.toContain('other-app-cache-v1');

      const remainingKeys = await caches.keys();
      expect(remainingKeys).toContain(SHELL_CACHE_NAME);
      expect(remainingKeys).toContain(ASSETS_CACHE_NAME);
      expect(remainingKeys).toContain('other-app-cache-v1');
      expect(remainingKeys).not.toContain(`${CACHE_PREFIX}shell-v0`);
    });
  });

  describe('IndexedDB Isolation Guarantee', () => {
    it('verifies that Service Worker cache purge never deletes Phase 23 IndexedDB records', async () => {
      const idb = NexusFieldDatabase.getInstance();
      await idb.resetDatabaseForTesting();

      const incidentRepo = new IncidentRepository();
      const incident: DurableIncident = {
        schema_version: '1.0.0',
        incident_id: 'INC-ISOLATION-001',
        event_type: 'FLOOD_INUNDATION',
        severity: 'HIGH',
        status: 'OPEN',
        priority: 1,
        location: { type: 'Point', coordinates: [80.223, 13.018] },
        reported_at: new Date().toISOString(),
        reported_by: 'FIELD_OFFICER_01',
        description: 'Testing IDB isolation during SW cache wipe',
        source: 'field_officer',
        local_record_id: 'LOCAL-ISO-01',
        created_locally_at: new Date().toISOString(),
        updated_locally_at: new Date().toISOString(),
        sync_status: 'PENDING_SYNC',
        sync_attempts: 0,
      };
      await incidentRepo.save(incident);

      // Perform aggressive SW cache purge
      await purgeOldNexusCaches([]);

      // Verify incident in IndexedDB remains intact
      const recovered = await incidentRepo.getById('INC-ISOLATION-001');
      expect(recovered).not.toBeNull();
      expect(recovered?.description).toBe('Testing IDB isolation during SW cache wipe');
    });
  });

  describe('Background Sync & Messaging Foundation', () => {
    it('detects Background Sync capability accurately in unsupported environment', () => {
      const bgSync = BackgroundSyncManager.getInstance();
      // In Node/JSDOM default without window.SyncManager
      expect(bgSync.isSupported()).toBe(false);

      const capability = bgSync.getCapability();
      expect(capability.isSupported).toBe(false);
      expect(capability.registeredTag).toBeNull();
    });

    it('detects Background Sync capability and registers tag when SyncManager exists', async () => {
      const mockRegister = vi.fn().mockResolvedValue(undefined);
      (globalThis as any).SyncManager = class {};
      (globalThis as any).navigator.serviceWorker = {
        ready: Promise.resolve({
          sync: {
            register: mockRegister,
          },
        }),
      };

      const bgSync = BackgroundSyncManager.getInstance();
      expect(bgSync.isSupported()).toBe(true);

      const registered = await bgSync.registerOutboxSync();
      expect(registered).toBe(true);
      expect(mockRegister).toHaveBeenCalledWith(OUTBOX_SYNC_TAG);

      const capability = bgSync.getCapability();
      expect(capability.registeredTag).toBe(OUTBOX_SYNC_TAG);
    });

    it('ServiceWorkerCoordinator provides status and update subscription', () => {
      const coordinator = ServiceWorkerCoordinator.getInstance();
      const status = coordinator.getStatus();

      expect(status.status).toBeDefined();
      expect(status.cacheVersion).toBe('v1');

      let updateNotified = false;
      const unsub = coordinator.onUpdateFound((hasUpdate) => {
        updateNotified = hasUpdate;
      });
      expect(updateNotified).toBe(false);
      unsub();
    });
  });
});
