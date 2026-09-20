/**
 * NEXUS Field PWA Database Layer Types (Phase 23)
 * Defines local storage metadata and schemas separate from canonical domain contracts.
 */

import {
  CanonicalIncidentReport,
  FieldAssignment,
  IncidentEvidenceItem,
  ResourceRequest,
} from '../types';

export type LocalSyncStatus =
  | 'LOCAL_ONLY'
  | 'PENDING_SYNC'
  | 'SYNCING'
  | 'SYNCED'
  | 'SYNC_ERROR';

export interface LocalMetadata {
  local_record_id: string;
  created_locally_at: string;
  updated_locally_at: string;
  sync_status: LocalSyncStatus;
  sync_attempts: number;
  last_sync_error?: string;
  server_record_id?: string;
}

export type DurableIncident = CanonicalIncidentReport & LocalMetadata;

export type DurableEvidence = IncidentEvidenceItem & {
  incident_id?: string;
  sync_status: LocalSyncStatus;
  local_record_id: string;
  blob_ref?: string;
};

export type DurableAssignment = FieldAssignment & {
  cached_at: string;
  is_cached: boolean;
  last_local_status_update?: string;
};

export type DurableResourceRequest = ResourceRequest & {
  local_record_id: string;
  created_locally_at: string;
  sync_status: LocalSyncStatus;
  sync_attempts: number;
  last_sync_error?: string;
};

export type OutboxEntityType =
  | 'INCIDENT'
  | 'EVIDENCE'
  | 'RESOURCE_REQUEST'
  | 'STATUS_UPDATE';

export type OutboxOperationType = 'CREATE' | 'UPDATE' | 'DELETE';

export type OutboxStatus = 'PENDING' | 'SYNCING' | 'SYNCED' | 'CONFLICT' | 'FAILED';

export interface OutboxOperation<T = any> {
  operation_id: string;
  entity_type: OutboxEntityType;
  entity_id: string;
  operation_type: OutboxOperationType;
  payload: T;
  created_at: string;
  updated_at: string;
  status: OutboxStatus;
  attempt_count: number;
  last_attempt_at?: string;
  last_error?: string;
  base_state_version?: number;
  conflict_data?: any;
}

export interface AppStateRecord {
  key: string;
  value: any;
  updated_at: string;
}

export const DB_NAME = 'nexus-field';
export const DB_VERSION = 1;

export const STORE_INCIDENTS = 'incidents';
export const STORE_EVIDENCE = 'evidence';
export const STORE_ASSIGNMENTS = 'assignments';
export const STORE_RESOURCE_REQUESTS = 'resource_requests';
export const STORE_OUTBOX = 'outbox';
export const STORE_APP_STATE = 'app_state';
