/**
 * NEXUS Command Center - Core Type Definitions
 * Phase 12 Foundation + Phase 13 Live GIS Dashboard
 */

export type ConnectionStatus = 'ONLINE' | 'DEGRADED' | 'OFFLINE';

export type DataMode = 'REAL' | 'SIMULATION' | 'DEMO' | 'UNKNOWN';

export type EmergencyType =
  | 'FLOOD'
  | 'CYCLONE'
  | 'LANDSLIDE'
  | 'WILDFIRE'
  | 'EXTREME_HEAT'
  | 'TORNADO'
  | 'INDUSTRIAL_ACCIDENT'
  | 'CHEMICAL_INCIDENT'
  | 'URBAN_INFRASTRUCTURE_FAILURE'
  | 'PUBLIC_HEALTH_EMERGENCY'
  | 'MAJOR_TRANSPORT_INCIDENT'
  | 'EARTHQUAKE';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN';

export type UserRole =
  | 'COMMANDER'
  | 'FIELD_OFFICER'
  | 'HOSPITAL_COORDINATOR'
  | 'SHELTER_COORDINATOR'
  | 'ADMIN';

export interface UserSession {
  userId: string;
  name: string;
  role: UserRole;
  jurisdiction: string;
}

export interface StateVersionInfo {
  version: number | null;
  lastUpdated: string | null;
  authority: string;
  hash?: string;
}

export type IncidentStatusType =
  | 'OPEN'
  | 'ACKNOWLEDGED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CANCELLED'
  | 'REPORTED'
  | 'DISPATCHED'
  | 'ON_SCENE';

export interface IncidentSummary {
  id: string;
  type: string;
  severity: SeverityLevel;
  status: IncidentStatusType;
  description: string;
  latitude: number;
  longitude: number;
  reportedAt: string;
  assignedUnit?: string;
  source?: string;
}

export interface FloodExposureInfo {
  is_exposed: boolean;
  status: 'EXPOSED' | 'CLEAR' | 'NOT_EVALUATED' | 'EVALUATION_ERROR';
  scenario_id?: string;
  mode?: string;
  evaluated: boolean;
}

export interface FacilityAuditRecord {
  timestamp: string;
  actor: string;
  action: string;
  state_version: number;
  details?: string;
}

export interface HospitalSummary {
  hospital_id: string;
  name: string;
  location: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  status: 'OPERATIONAL' | 'OVERLOADED' | 'EVACUATING' | 'CLOSED';
  accessibility: 'ALL_VEHICLES' | 'EMERGENCY_ONLY' | 'HIGH_CLEARANCE_ONLY' | 'IMPASSABLE';
  capacity: number;
  available_capacity: number;
  emergency_available: boolean;
  icu_available: number;
  last_updated: string;
  source: string;
  state_version?: number;
  flood_exposure?: FloodExposureInfo;
  history?: FacilityAuditRecord[];
}

export interface ShelterSummary {
  shelter_id: string;
  name: string;
  location: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  status: 'OPEN' | 'AT_CAPACITY' | 'STANDBY' | 'CLOSED';
  accessibility: 'ALL_VEHICLES' | 'EMERGENCY_ONLY' | 'HIGH_CLEARANCE_ONLY' | 'IMPASSABLE';
  capacity: number;
  available_capacity: number;
  has_power_backup: boolean;
  has_potable_water: boolean;
  last_updated: string;
  source: string;
  state_version?: number;
  flood_exposure?: FloodExposureInfo;
  history?: FacilityAuditRecord[];
}

export interface FacilitySummary {
  id: string;
  name: string;
  type: 'HOSPITAL' | 'SHELTER';
  capacityTotal: number;
  capacityOccupied: number;
  operationalStatus: string;
  powerStatus: 'GRID' | 'GENERATOR' | 'OFFLINE';
  lastUpdated: string;
  latitude?: number;
  longitude?: number;
  emergencyAvailable?: boolean;
  icuAvailable?: number;
  source?: string;
  stateVersion?: number;
  accessibility?: string;
  floodExposure?: FloodExposureInfo;
}


export interface VulnerabilityClusterSummary {
  id: string;
  zoneName: string;
  priorityScore: number;
  elderlyCount: number;
  mobilityImpairedCount: number;
  floodRiskLevel: 'NONE' | 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';
}

export interface SimulationSummary {
  scenarioId: string;
  name: string;
  rainfallMm: number;
  riverSurgeM: number;
  affectedRoadsCount: number;
  inundatedFacilitiesCount: number;
  computedAt: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  details: string;
  provenanceHash: string;
}

export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, unknown>;
  code?: string;
}

// -------------------------------------------------------------
// Phase 13 GIS Types (WGS84 [longitude, latitude] convention)
// -------------------------------------------------------------

export interface GeoPoint {
  type: 'Point';
  coordinates: [number, number]; // [lon, lat]
}

export interface GeoLineString {
  type: 'LineString';
  coordinates: [number, number][]; // [[lon, lat], ...]
}

export interface GeoPolygon {
  type: 'Polygon';
  coordinates: [number, number][][]; // [[[lon, lat], ...]]
}

export interface FloodExtentFeature {
  id: string;
  type: 'Feature';
  geometry: GeoPolygon;
  properties: {
    floodZoneId: string;
    name: string;
    severity: SeverityLevel;
    waterDepthM?: number;
    scenarioId?: string;
    mode: DataMode;
    source: string;
    updatedAt: string;
  };
}

export type RoadOperationalStatus = 'OPEN' | 'RESTRICTED' | 'BLOCKED' | 'UNKNOWN';

export interface RoadFeature {
  id: string;
  type: 'Feature';
  geometry: GeoLineString;
  properties: {
    roadId: string;
    name: string;
    roadType: 'primary' | 'secondary' | 'residential' | 'bridge' | 'motorway';
    status: RoadOperationalStatus;
    accessibility: 'ALL_VEHICLES' | 'EMERGENCY_ONLY' | 'HIGH_CLEARANCE' | 'IMPASSABLE';
    speedLimitKmh: number;
    floodDepthCm?: number;
    isBridge?: boolean;
    bridgeId?: string;
    source: string;
    updatedAt: string;
  };
}

export interface BridgeFeature {
  id: string;
  type: 'Feature';
  geometry: GeoPoint;
  properties: {
    bridgeId: string;
    name: string;
    roadId: string;
    status: 'OPEN' | 'AFFECTED' | 'FAILED' | 'UNKNOWN';
    clearanceM: number;
    source: string;
    updatedAt: string;
  };
}

export interface RouteFeature {
  id: string;
  type: 'Feature';
  geometry: GeoLineString;
  properties: {
    routeId: string;
    name: string;
    isCurrent: boolean;
    isBlocked?: boolean;
    distanceKm: number;
    travelTimeMin: number;
    status: 'ACTIVE' | 'BLOCKED' | 'PREVIOUS' | 'REROUTED';
    startNode: string;
    endNode: string;
    deltaDistanceKm?: number;
    deltaTravelTimeMin?: number;
    changeExplanation?: string;
  };
}

export interface CriticalZone {
  id: string;
  name: string;
  severity: SeverityLevel;
  waterDepthM?: number;
  affectedRoadsCount: number;
  nearestHospital: string;
  nearestShelter: string;
}

export type GisSelectedEntity =
  | { type: 'FLOOD'; data: FloodExtentFeature['properties'] & { id: string } }
  | { type: 'ROAD'; data: RoadFeature['properties'] & { id: string } }
  | { type: 'BRIDGE'; data: BridgeFeature['properties'] & { id: string } }
  | { type: 'INCIDENT'; data: IncidentSummary }
  | { type: 'HOSPITAL'; data: FacilitySummary }
  | { type: 'SHELTER'; data: FacilitySummary }
  | { type: 'ROUTE'; data: RouteFeature['properties'] & { id: string } }
  | null;
