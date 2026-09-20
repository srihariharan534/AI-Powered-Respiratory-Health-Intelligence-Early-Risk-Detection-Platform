# NEXUS Architecture: Service Worker, Caching & Background Sync Foundation (Phase 24)

## 1. Overview & Operational Role

Phase 24 introduces the offline Service Worker foundation for the **NEXUS Field PWA**. Field officers operating in flood inundation zones and remote tactical sectors frequently suffer sudden network degradation, intermittent connectivity, or complete signal loss.

The Service Worker operates as a transparent network interception proxy and lifecycle coordinator that guarantees:
1. **Immediate Application Shell Availability**: Offline launch capability using versioned cache storage.
2. **Deterministic Route Caching Strategies**: Differential handling of static code/styles vs HTML navigation vs mutating API calls.
3. **Background Sync Trigger Hook**: Registration and broadcast hook for `nexus-field-outbox-sync` when connectivity recovers.
4. **Strict Isolation from IndexedDB**: Service Worker and cache management operations never delete or modify the durable Phase 23 IndexedDB outbox or operational stores.

---

## 2. Service Worker Architecture & Lifecycle

```
[Browser / PWA Client]
       │
       │ (1) Registers /sw.js (non-blocking)
       ▼
[Service Worker: /sw.js]
       │
       ├─► install event: Precaches App Shell (nexus-field-shell-v1) & skips waiting
       │
       ├─► activate event: Purges stale nexus-field-* caches & clients.claim()
       │
       ├─► fetch event: Intercepts network requests with safe routing strategies
       │
       ├─► sync event: Listens for 'nexus-field-outbox-sync' & broadcasts OUTBOX_SYNC_TRIGGERED
       │
       └─► message event: Responds to GET_SW_INFO, SKIP_WAITING, ping-pong diagnostics
```

---

## 3. Cache Versioning & Namespacing

NEXUS Field PWA defines explicit, segregated cache namespaces:

* **`nexus-field-shell-v1`**: Core entry points (`/`, `/index.html`, `/manifest.webmanifest`, `/favicon.ico`).
* **`nexus-field-assets-v1`**: Static assets (`/assets/*.js`, `/assets/*.css`, fonts, icons, images).

### Selective Cache Invalidation
When a new Service Worker activates, `purgeOldNexusCaches()` iterates through all keys in `window.caches` or Service Worker `caches`. It matches only keys starting with the prefix `nexus-field-` and deletes any version not present in the current active list (`nexus-field-shell-v1`, `nexus-field-assets-v1`).
**Critical Safety Guarantee**: Cache invalidation touches ONLY `CacheStorage`. It never touches IndexedDB databases (`nexus_field_offline_db`) or sync outbox queues.

---

## 4. Routing & Interception Strategies

| Request Type | Pattern | Strategy | Offline Behavior |
| :--- | :--- | :--- | :--- |
| **HTML Navigation** | `request.mode === 'navigate'` | **Network-First** | Attempts network with 3s timeout; on failure serves cached `/index.html` fallback. |
| **Static Assets** | Scripts, styles, fonts, images | **Cache-First** | Returns cached version immediately; fetches and populates cache if absent. |
| **REST / Tactical APIs** | `/api/*` | **Network-Only** | Directly fetches from server. Never cached. Returns explicit 503 JSON payload if offline. |
| **Mutating Requests** | `POST`, `PUT`, `DELETE`, `PATCH` | **Direct Network** | Service Worker fetch handler completely bypasses mutating operations, directing them to the application layer where Phase 23 SyncQueue and IndexedDB persist them. |

---

## 5. Background Sync Integration

### Feature Detection & Registration
Browsers supporting the `SyncManager` API (`'sync' in registration`) register one-off sync events:
```typescript
await registration.sync.register('nexus-field-outbox-sync');
```
If the browser does not support the Web Background Sync API (e.g. Firefox or iOS Safari), the `BackgroundSyncManager` logs graceful fallback and exposes capability status `supported: false` to the UI HUD.

### Sync Event Lifecycle
When network connectivity is restored:
1. The browser fires the `sync` event with tag `nexus-field-outbox-sync` in the Service Worker.
2. The Service Worker receives the event and sends a message to all active clients:
   ```json
   {
     "type": "OUTBOX_SYNC_TRIGGERED",
     "tag": "nexus-field-outbox-sync",
     "timestamp": 1726822800000
   }
   ```
3. The PWA application layer (`ServiceWorkerCoordinator` and `SyncStatusScreen`) receives the broadcast and updates UI indicators.
4. **Boundary Guard**: Full replay, retry policies, server reconciliation, and conflict resolution remain reserved for Phase 25.

---

## 6. Service Worker Communication Protocol

Clients communicate with the Service Worker via `navigator.serviceWorker.controller.postMessage()`:
- `GET_SW_INFO`: Requests current SW version, shell cache version, and asset cache version.
- `SKIP_WAITING`: Signals waiting Service Worker to take immediate control.
- `OUTBOX_SYNC_TRIGGERED`: Broadcast from SW to client upon OS-level background sync trigger.
