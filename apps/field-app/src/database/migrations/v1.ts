/**
 * Database Migration v1 (Phase 23)
 * Creates durable IndexedDB object stores and indexes for offline operations.
 */

import {
  STORE_INCIDENTS,
  STORE_EVIDENCE,
  STORE_ASSIGNMENTS,
  STORE_RESOURCE_REQUESTS,
  STORE_OUTBOX,
  STORE_APP_STATE,
} from '../types';

export function runMigrationV1(db: IDBDatabase): void {
  // 1. Incidents Store
  if (!db.objectStoreNames.contains(STORE_INCIDENTS)) {
    const incidentStore = db.createObjectStore(STORE_INCIDENTS, {
      keyPath: 'incident_id',
    });
    incidentStore.createIndex('status', 'status', { unique: false });
    incidentStore.createIndex('severity', 'severity', { unique: false });
    incidentStore.createIndex('event_type', 'event_type', { unique: false });
    incidentStore.createIndex('sync_status', 'sync_status', { unique: false });
    incidentStore.createIndex('created_locally_at', 'created_locally_at', { unique: false });
  }

  // 2. Evidence Store
  if (!db.objectStoreNames.contains(STORE_EVIDENCE)) {
    const evidenceStore = db.createObjectStore(STORE_EVIDENCE, {
      keyPath: 'evidence_id',
    });
    evidenceStore.createIndex('incident_id', 'incident_id', { unique: false });
    evidenceStore.createIndex('type', 'type', { unique: false });
    evidenceStore.createIndex('captured_at', 'captured_at', { unique: false });
    evidenceStore.createIndex('sync_status', 'sync_status', { unique: false });
  }

  // 3. Assignments Store
  if (!db.objectStoreNames.contains(STORE_ASSIGNMENTS)) {
    const assignmentStore = db.createObjectStore(STORE_ASSIGNMENTS, {
      keyPath: 'assignment_id',
    });
    assignmentStore.createIndex('status', 'status', { unique: false });
    assignmentStore.createIndex('priority', 'priority', { unique: false });
    assignmentStore.createIndex('incident_id', 'incident_id', { unique: false });
    assignmentStore.createIndex('assigned_at', 'assigned_at', { unique: false });
  }

  // 4. Resource Requests Store
  if (!db.objectStoreNames.contains(STORE_RESOURCE_REQUESTS)) {
    const resourceStore = db.createObjectStore(STORE_RESOURCE_REQUESTS, {
      keyPath: 'request_id',
    });
    resourceStore.createIndex('resource_type', 'resource_type', { unique: false });
    resourceStore.createIndex('urgency', 'urgency', { unique: false });
    resourceStore.createIndex('sync_status', 'sync_status', { unique: false });
    resourceStore.createIndex('created_locally_at', 'created_locally_at', { unique: false });
  }

  // 5. Outbox Store
  if (!db.objectStoreNames.contains(STORE_OUTBOX)) {
    const outboxStore = db.createObjectStore(STORE_OUTBOX, {
      keyPath: 'operation_id',
    });
    outboxStore.createIndex('status', 'status', { unique: false });
    outboxStore.createIndex('entity_type', 'entity_type', { unique: false });
    outboxStore.createIndex('entity_id', 'entity_id', { unique: false });
    outboxStore.createIndex('created_at', 'created_at', { unique: false });
  }

  // 6. App State Store
  if (!db.objectStoreNames.contains(STORE_APP_STATE)) {
    db.createObjectStore(STORE_APP_STATE, {
      keyPath: 'key',
    });
  }
}
