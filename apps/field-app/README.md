# NEXUS Field PWA — Offline-First Tactical Mobile Application Foundation

Phase 22 implements the **Field Progressive Web App (PWA)** foundation for NEXUS. Designed for field officers, first responders, and rescue teams operating in harsh disaster environments with intermittent or severed network connectivity.

---

## 🎯 Capabilities

1. **Touch-First Mobile UX**:
   - Minimum 48px touch targets compliant with emergency responder glove use.
   - High-contrast tactical dark theme (`#0f172a` slate base with vivid status accents).
   - Bottom navigation bar with direct thumb reach for one-handed operation.

2. **Bilingual Support (Tamil / English)**:
   - Complete localization toggle in header (English and தமிழ்).
   - Instant dynamic switching persisted in local settings.

3. **Field Incident Reporting**:
   - Canonical incident reporting adhering strictly to Phase 04 schema (`incident.schema.json`).
   - WGS84 coordinates capture: Device GPS with accuracy estimation in meters, plus seamless manual coordinate input fallback.
   - Severity tagging (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), description, and reporter metadata.

4. **Evidence Capture Simulation**:
   - Touch photo and video capture interface.
   - Attaches timestamps and GPS coordinates to media payloads enqueued for sync.

5. **Tactical Assignment HUD**:
   - Operational mission view with title, priority badge, and target coordinates.
   - Interactive progress stepper (`ASSIGNED` → `EN_ROUTE` → `ON_SCENE` → `COMPLETED`).

6. **Tactical Resource Requests**:
   - Emergency requisition interface for Boats, Medical Kits, Food/Water, Sandbags, and High-capacity Pumps.
   - Enqueued into synchronization queue.

7. **Structured SMS Fallback Generation**:
   - When mobile data and Wi-Fi are totally unavailable, generates standard-compliant 160-character SMS payload:
     ```text
     FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>
     ```
   - Includes one-tap clipboard copy and direct `sms:?body=...` launch.

8. **Offline Queue & Connectivity HUD**:
   - Network listener tracking browser online/offline status.
   - Testing simulation toggle bar to test `ONLINE`, `OFFLINE`, and `SYNCING` behavior.
   - Live queue monitor showing queued actions, retry counts, and manual sync trigger.

9. **Cached Map Foundation**:
   - Visual tactical vector grid with GPS position marker and mission waypoint.
   - Clear operational disclaimer: `OFFLINE MAP: Cached map tiles will be available when configured`.

---

## 🏗️ Architecture & Phase Boundaries

Phase 22 established the UI layout, while **Phase 23 introduces durable browser-side storage**:
- **IndexedDB Persistence (Phase 23)**:
  - Database: `nexus-field` (Version 1)
  - Object Stores: `incidents`, `evidence`, `assignments`, `resource_requests`, `outbox`, `app_state`.
  - Atomic multi-store transactions: saves incident + evidence + outbox record atomically.
  - Zero-loss recovery: all locally recorded incidents, requests, and outbox actions survive application close, page refresh, and device reboots.
- **Service Worker & Offline Cache (Phase 24)**:
  - Native Service Worker (`public/sw.js`) with cache versioning: `nexus-field-shell-v1` and `nexus-field-assets-v1`.
  - Offline App Shell precaching with offline navigation fallback.
  - Safe network interception: Network-First for navigation, Cache-First for static assets, Network-Only for `/api/*`.
  - Background Sync registration hook (`nexus-field-outbox-sync`) and client broadcast channel.
  - Selective cache purge protecting Phase 23 IndexedDB stores from any deletion during SW upgrades.
- **Conflict Resolution & Sync Protocol (Phase 25)**:
  - Canonical Synchronization Protocol (`services/sync/sync_protocol.md`) connecting Field PWA outbox with central NEXUS API.
  - Multi-tab synchronization locking via Web Locks API (`navigator.locks`).
  - At-least-once delivery with server-side idempotency registry and payload SHA-256 collision detection (`IDEMPOTENCY_KEY_REUSE`).
  - Optimistic concurrency & conflict handling against authoritative Digital Twin state version.
  - Append-only sync audit ledger (`services/sync/event_log/`).
- **SMS Gateway/Ingestion Backend**: Telecom parser reserved for Phase 26.

---

## 🚀 Running Locally

```bash
cd apps/field-app
npm install
npm run dev
```

App runs locally at `http://localhost:3001/`.

### Running Tests
```bash
npm run test
```

### Production Build
```bash
npm run build
```
