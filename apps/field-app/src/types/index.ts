/**
 * NEXUS Field PWA Core Types (Phase 22)
 * Aligns strictly with Phase 04 Canonical Schemas (incident, sms, evidence).
 */

export type ConnectionStatus = 'ONLINE' | 'OFFLINE' | 'SYNCING' | 'SYNC_ERROR';

export type DataMode = 'LIVE' | 'DEMO' | 'CACHED' | 'OFFLINE' | 'SIMULATION';

export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type IncidentStatus = 'OPEN' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'RESOLVED' | 'CANCELLED';

export type IncidentEventType =
  | 'FLOOD_INUNDATION'
  | 'ROAD_BLOCKED'
  | 'BRIDGE_FAILURE'
  | 'EMBANKMENT_BREACH'
  | 'MEDICAL_EMERGENCY'
  | 'TRAPPED_PERSONS'
  | 'SHELTER_NEEDED'
  | 'RESOURCE_REQUEST';

export interface GeoPointLocation {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude] in WGS84
}

export interface IncidentEvidenceItem {
  evidence_id: string;
  type: 'photo' | 'video' | 'sensor_log' | 'manual_entry';
  uri?: string;
  file_name?: string;
  file_size?: number;
  mime_type?: string;
  captured_at: string;
  description?: string;
}

export interface CanonicalIncidentReport {
  schema_version: '1.0.0';
  incident_id: string;
  event_type: IncidentEventType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  priority: number;
  location: GeoPointLocation;
  reported_at: string;
  reported_by: string;
  description: string;
  source: 'field_officer' | 'sms' | 'manual_entry';
  evidence?: IncidentEvidenceItem[];
}

export interface FieldAssignment {
  assignment_id: string;
  incident_id: string;
  task_name: string;
  instructions: string;
  priority: number;
  status: 'ASSIGNED' | 'EN_ROUTE' | 'ON_SCENE' | 'COMPLETED';
  location: {
    name: string;
    latitude: number;
    longitude: number;
  };
  assigned_at: string;
  data_mode: DataMode;
}

export interface ResourceRequest {
  request_id: string;
  resource_type: 'RESCUE_BOAT' | 'MEDICAL_KIT' | 'FOOD_WATER' | 'SQUAD_BACKUP' | 'AMBULANCE' | 'SANDBAGS';
  quantity: number;
  urgency: 'IMMEDIATE' | 'HIGH' | 'ROUTINE';
  location: [number, number];
  reason: string;
  requested_by: string;
  requested_at: string;
  status: 'PENDING_SYNC' | 'SUBMITTED' | 'DISPATCHED';
}

export interface PendingSyncItem {
  queue_id: string;
  entity_type: 'INCIDENT' | 'EVIDENCE' | 'RESOURCE_REQUEST' | 'STATUS_UPDATE';
  payload: any;
  queued_at: string;
  status: 'QUEUED' | 'SYNCING' | 'ERROR';
  error_message?: string;
}
