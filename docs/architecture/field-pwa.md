# Field PWA Architecture & Data Contracts (Phase 22 Foundation)

## Overview
The NEXUS Field PWA (`apps/field-app`) is a resilient, offline-first client application running on field personnel mobile devices.

```
┌───────────────────────────────────────────────────────────┐
│                    Field PWA (React)                     │
├──────────────────────────┬────────────────────────────────┤
│    Presentation Layer    │ BottomNav, Layout, HUD         │
│                          │ IncidentReport, Evidence       │
│                          │ TacticalAssignment, Map        │
│                          │ ResourceRequest, SMS Fallback  │
├──────────────────────────┼────────────────────────────────┤
│       Context API        │ FieldAppContext (State)        │
│                          │ I18nContext (EN / TA)          │
├──────────────────────────┼────────────────────────────────┤
│     Core Services        │ LocationService (GPS / Manual) │
│                          │ ConnectivityService (Net/Sim)  │
│                          │ SyncQueueService (Queue)       │
├──────────────────────────┼────────────────────────────────┤
│   Foundation Hooks       │ CacheStrategyFoundation (P24)  │
│                          │ FieldDatabasePlaceholder (P23) │
└──────────────────────────┴────────────────────────────────┘
```

## Data Contracts & Provenance Compliance

### 1. Canonical Incident Report
Adheres to Phase 04 `incident.schema.json`:
- `id`: Unique identifier (e.g., `INC-FIELD-...`)
- `event_type`: Valid Phase 04 enum (`FLOOD_INUNDATION`, `EVACUATION_ORDER`, etc.)
- `severity`: Standard enum (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `location`: Point geometry `[longitude, latitude]` in WGS84 EPSG:4326 format.
- `metadata`: Field officer unit, reporter role, accuracy in meters.

### 2. Zero-Data Structured SMS Fallback
Matches Phase 04 `sms.schema.json` constraint of ≤160 characters:
```text
FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>
```
Example:
```text
FLOOD INC-CHENNAI-001 ACTIVE CRITICAL 13.08270 80.27070
```

### 3. Queue Item Data Contract
```typescript
interface PendingSyncItem<T = any> {
  id: string;
  type: 'INCIDENT_REPORT' | 'EVIDENCE_ITEM' | 'RESOURCE_REQUEST' | 'ASSIGNMENT_UPDATE';
  payload: T;
  timestamp: string; // ISO-8601
  retryCount: number;
  status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED';
  error?: string;
}
```

## Phase Boundaries
- **Phase 22 (Current)**: Touch UX, bilingual dictionary, GPS capture, in-memory sync queue, structured SMS generation, mock map foundation.
- **Phase 23**: Durable IndexedDB persistence, transactions, migrations.
- **Phase 24**: Service Worker background sync & runtime vector tile cache.
- **Phase 25**: Conflict resolution and multi-officer reconciliation.
- **Phase 26**: Telecom SMS gateway receiver & telemetry parsing.
