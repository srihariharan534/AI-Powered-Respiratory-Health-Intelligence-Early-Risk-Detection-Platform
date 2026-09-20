# NEXUS Offline Storage Architecture (Phase 23)

## 1. Overview
The **NEXUS Field PWA Offline Storage Subsystem** provides client-side, zero-loss durable persistence for emergency field responders operating in severed or disrupted network conditions.

The core principle is:
> **Application restart, page refresh, or device reboot must not erase valid offline field data.**

```
┌─────────────────────────────────────────────────────────────┐
│                 Field Application UI Layer                  │
│    (IncidentReport, EvidenceCapture, ResourceRequest, etc.)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Field Domain Repositories & Services            │
│  - IncidentRepository            - OutboxRepository         │
│  - EvidenceRepository            - AppStateRepository       │
│  - AssignmentRepository          - TransactionCoordinator   │
│  - ResourceRequestRepository     - SyncQueueService         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            NexusFieldDatabase (IndexedDB Adapter)           │
│  - Stable Database: "nexus-field"                           │
│  - Versioning & Migrations Runner (Migration v1)            │
│  - Atomic Multi-Store Transactions (readwrite)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Browser IndexedDB Engine                  │
│  [incidents] [evidence] [assignments]                       │
│  [resource_requests] [outbox] [app_state]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema & Object Stores

- **Database Name**: `nexus-field`
- **Schema Version**: `1`

### Stores & KeyPaths:
1. **`incidents`** (`keyPath: "incident_id"`):
   - Conforms strictly to Phase 04 `data/schemas/incident.schema.json`.
   - Indexes: `status`, `severity`, `event_type`, `sync_status`, `created_locally_at`.
   - Local Metadata: `local_record_id`, `created_locally_at`, `updated_locally_at`, `sync_status`, `sync_attempts`, `last_sync_error`.
2. **`evidence`** (`keyPath: "evidence_id"`):
   - Preserves filename, mime_type, file_size, captured_at, description, incident link.
   - Indexes: `incident_id`, `type`, `captured_at`, `sync_status`.
3. **`assignments`** (`keyPath: "assignment_id"`):
   - Preserves tactical instructions, mission target coordinates, priority, and progress.
   - Indexes: `status`, `priority`, `incident_id`, `assigned_at`.
   - Cache state: `cached_at`, `is_cached`, `last_local_status_update`.
4. **`resource_requests`** (`keyPath: "request_id"`):
   - Stores tactical asset requests (`RESCUE_BOAT`, `MEDICAL_KIT`, `FOOD_WATER`, `SANDBAGS`, `AMBULANCE`, `SQUAD_BACKUP`).
   - Indexes: `resource_type`, `urgency`, `sync_status`, `created_locally_at`.
5. **`outbox`** (`keyPath: "operation_id"`):
   - Stores durable operations awaiting future Phase 25 synchronization.
   - Collision-resistant IDs (`OP-<timestamp>-<hash>`).
   - Indexes: `status` (`PENDING`, `SYNCING`, `FAILED`), `entity_type`, `entity_id`, `created_at`.
6. **`app_state`** (`keyPath: "key"`):
   - Stores key-value settings (`last_known_user`, `last_selected_assignment`, `database_schema_version`).

---

## 3. Atomic Offline Creation Workflow

When an officer submits an emergency report offline:
```
Officer Submits Incident (Offline)
             ↓
DataValidator.validateIncident() (WGS84 coordinate bounds, enums, required fields)
             ↓
TransactionCoordinator.saveIncidentWithOutbox()
             ↓
[BEGIN IDB MULTI-STORE TRANSACTION: readwrite]
  ├── Store "incidents": put(durableIncident)
  ├── Store "evidence": put(evidenceItems...)
  └── Store "outbox": put(outboxOperation)
[COMMIT]
             ↓
UI displays: "SAVED ON DEVICE — PENDING SYNC"
```

If the transaction encounters quota exhaustion or storage errors:
```
[ABORT / ROLLBACK]
             ↓
UI displays: "Storage Error: Could not save report on device. Free storage space and try again."
(Never displays false success)
```

---

## 4. Phase Boundaries

| Phase | Boundary Ownership |
|---|---|
| **Phase 23 (Current)** | Durable local IndexedDB storage, atomic offline create, versioned migrations, outbox queue. |
| **Phase 24** | Service Worker, background sync registration, runtime tile & asset cache strategies. |
| **Phase 25** | Synchronization protocol, idempotency verification, conflict resolution, server reconciliation. |
| **Phase 26** | SMS parser, telecom provider gateway, incoming telemetry normalization. |

---

## 5. Security & Privacy
- IndexedDB is local to the device browser origin.
- Sensitive authentication tokens, passwords, and API secrets are strictly **never** stored in IndexedDB.
- Logs only capture sanitized operation metadata (`operation_id`, `entity_type`) and never expose private citizen details or payloads.
