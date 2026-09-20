/**
 * Deterministic Demo and Synthetic Datasets for NEXUS Command Center
 * Mode: DEMO / SYNTHETIC
 * Baseline Location: Chennai Central EOC Core [80.2707, 13.0827]
 * Coordinates convention: WGS84 [longitude, latitude]
 */

import {
  FloodExtentFeature,
  RoadFeature,
  BridgeFeature,
  IncidentSummary,
  FacilitySummary,
  RouteFeature,
  CriticalZone,
} from '../types';

export const DEMO_OPERATIONAL_AREA = {
  center: [80.2707, 13.0827] as [number, number], // [lon, lat]
  defaultZoom: 14,
  name: 'Chennai EOC Core Zone 1',
};

// 1. Flood Extents (Phase 10 Inundation Output / Demo Scenarios)
export const DEMO_FLOOD_FEATURES: FloodExtentFeature[] = [
  {
    id: 'F-001',
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [80.264, 13.078],
          [80.276, 13.078],
          [80.278, 13.085],
          [80.267, 13.086],
          [80.264, 13.078],
        ],
      ],
    },
    properties: {
      floodZoneId: 'F-001',
      name: 'Cooum Basin Central Inundation',
      severity: 'CRITICAL',
      waterDepthM: 1.35,
      scenarioId: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      source: 'NEXUS Flood Engine (Elevation Inundation Model)',
      updatedAt: '2026-09-19T14:30:00Z',
    },
  },
  {
    id: 'F-002',
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [80.258, 13.088],
          [80.268, 13.088],
          [80.266, 13.095],
          [80.255, 13.093],
          [80.258, 13.088],
        ],
      ],
    },
    properties: {
      floodZoneId: 'F-002',
      name: 'North Sector Secondary Swell',
      severity: 'MEDIUM',
      waterDepthM: 0.45,
      scenarioId: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      source: 'NEXUS Flood Engine',
      updatedAt: '2026-09-19T14:25:00Z',
    },
  },
];

// 2. Roads and Corridors (Phase 05 OSM Graph + Phase 08 Dynamic Overlay)
export const DEMO_ROAD_FEATURES: RoadFeature[] = [
  {
    id: 'R-101',
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [80.262, 13.081],
        [80.2707, 13.0827],
        [80.278, 13.084],
      ],
    },
    properties: {
      roadId: 'R-101',
      name: 'Poonamallee High Road East',
      roadType: 'bridge',
      status: 'BLOCKED',
      accessibility: 'IMPASSABLE',
      speedLimitKmh: 40.0,
      floodDepthCm: 95.0,
      isBridge: true,
      bridgeId: 'B-001',
      source: 'Digital Twin Overlay (Bridge Failure Cascade)',
      updatedAt: '2026-09-19T14:35:00Z',
    },
  },
  {
    id: 'R-102',
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [80.262, 13.081],
        [80.264, 13.089],
        [80.274, 13.092],
        [80.278, 13.084],
      ],
    },
    properties: {
      roadId: 'R-102',
      name: 'EVR Periyar Northern Diversion',
      roadType: 'primary',
      status: 'OPEN',
      accessibility: 'ALL_VEHICLES',
      speedLimitKmh: 50.0,
      floodDepthCm: 0.0,
      isBridge: false,
      source: 'OpenStreetMap Road Graph',
      updatedAt: '2026-09-19T14:00:00Z',
    },
  },
  {
    id: 'R-103',
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [80.262, 13.081],
        [80.261, 13.075],
        [80.272, 13.076],
        [80.278, 13.084],
      ],
    },
    properties: {
      roadId: 'R-103',
      name: 'Anna Salai Southern Bypass',
      roadType: 'primary',
      status: 'RESTRICTED',
      accessibility: 'HIGH_CLEARANCE',
      speedLimitKmh: 30.0,
      floodDepthCm: 25.0,
      isBridge: false,
      source: 'Digital Twin Overlay',
      updatedAt: '2026-09-19T14:20:00Z',
    },
  },
];

// 3. Bridges (Phase 08 / Phase 09 Digital Twin Entities)
export const DEMO_BRIDGE_FEATURES: BridgeFeature[] = [
  {
    id: 'B-001',
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [80.2707, 13.0827],
    },
    properties: {
      bridgeId: 'B-001',
      name: 'Central River Causeway Bridge',
      roadId: 'R-101',
      status: 'FAILED',
      clearanceM: 1.2,
      source: 'Digital Twin State Authority',
      updatedAt: '2026-09-19T14:32:00Z',
    },
  },
  {
    id: 'B-002',
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [80.264, 13.089],
    },
    properties: {
      bridgeId: 'B-002',
      name: 'North Crossing Flyover',
      roadId: 'R-102',
      status: 'OPEN',
      clearanceM: 5.8,
      source: 'Digital Twin State Authority',
      updatedAt: '2026-09-19T14:00:00Z',
    },
  },
];

// 4. Incidents (Phase 04 Data Contracts & Field Reports)
export const DEMO_INCIDENTS: IncidentSummary[] = [
  {
    id: 'INC-001',
    type: 'FLOOD_INUNDATION',
    severity: 'CRITICAL',
    status: 'REPORTED',
    description: 'Severe flash flood inundation near central bridge. Water depth 85cm, 12 citizens trapped.',
    latitude: 13.0827,
    longitude: 80.2707,
    reportedAt: '14:30:00',
    source: 'FIELD_REPORT (Field Officer #42)',
    assignedUnit: 'RESCUE-UNIT-03',
  },
  {
    id: 'INC-002',
    type: 'ROAD_BLOCKAGE',
    severity: 'HIGH',
    status: 'DISPATCHED',
    description: 'Fallen electric transformer across westbound lanes.',
    latitude: 13.0855,
    longitude: 80.2645,
    reportedAt: '14:22:00',
    source: 'POLICE_DISPATCH',
    assignedUnit: 'RECOVERY-TRUCK-01',
  },
  {
    id: 'INC-003',
    type: 'MEDICAL_EVAC',
    severity: 'MEDIUM',
    status: 'ON_SCENE',
    description: 'Oxygen supply exhaustion at local geriatric care home.',
    latitude: 13.0765,
    longitude: 80.2680,
    reportedAt: '14:10:00',
    source: 'PUBLIC_HOTLINE',
    assignedUnit: 'AMBULANCE-09',
  },
];

// 5. Facilities: Hospitals and Shelters
export const DEMO_HOSPITALS: FacilitySummary[] = [
  {
    id: 'H-001',
    name: 'District General Trauma Hospital',
    type: 'HOSPITAL',
    capacityTotal: 250,
    capacityOccupied: 216,
    operationalStatus: 'OPERATIONAL',
    powerStatus: 'GRID',
    lastUpdated: '14:20:00',
    latitude: 13.0900,
    longitude: 80.2600,
    emergencyAvailable: true,
    icuAvailable: 14,
    accessibility: 'ALL_VEHICLES',
    source: 'SYNTHETIC_DEMO',
    stateVersion: 1,
    floodExposure: {
      is_exposed: false,
      status: 'CLEAR',
      scenario_id: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      evaluated: true,
    },
  },
  {
    id: 'H-002',
    name: 'Metropolitan Surgical Institute',
    type: 'HOSPITAL',
    capacityTotal: 150,
    capacityOccupied: 148,
    operationalStatus: 'OVERLOADED',
    powerStatus: 'GENERATOR',
    lastUpdated: '14:28:00',
    latitude: 13.0740,
    longitude: 80.2750,
    emergencyAvailable: false,
    icuAvailable: 0,
    accessibility: 'EMERGENCY_ONLY',
    source: 'SYNTHETIC_DEMO',
    stateVersion: 1,
    floodExposure: {
      is_exposed: false,
      status: 'CLEAR',
      scenario_id: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      evaluated: true,
    },
  },
  {
    id: 'H-003',
    name: 'Cooum Riverside Memorial Hospital',
    type: 'HOSPITAL',
    capacityTotal: 180,
    capacityOccupied: 140,
    operationalStatus: 'OPERATIONAL',
    powerStatus: 'GRID',
    lastUpdated: '14:35:00',
    latitude: 13.0815,
    longitude: 80.2710,
    emergencyAvailable: true,
    icuAvailable: 6,
    accessibility: 'HIGH_CLEARANCE_ONLY',
    source: 'SYNTHETIC_DEMO',
    stateVersion: 1,
    floodExposure: {
      is_exposed: true,
      status: 'EXPOSED',
      scenario_id: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      evaluated: true,
    },
  },
];

export const DEMO_SHELTERS: FacilitySummary[] = [
  {
    id: 'S-001',
    name: 'Community Relief Center North',
    type: 'SHELTER',
    capacityTotal: 500,
    capacityOccupied: 290,
    operationalStatus: 'OPEN',
    powerStatus: 'GRID',
    lastUpdated: '14:15:00',
    latitude: 13.0950,
    longitude: 80.2550,
    accessibility: 'ALL_VEHICLES',
    source: 'SYNTHETIC_DEMO',
    stateVersion: 1,
    floodExposure: {
      is_exposed: false,
      status: 'CLEAR',
      scenario_id: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      evaluated: true,
    },
  },
  {
    id: 'S-002',
    name: 'Govt Higher Secondary Relief Camp',
    type: 'SHELTER',
    capacityTotal: 350,
    capacityOccupied: 320,
    operationalStatus: 'OPEN',
    powerStatus: 'GENERATOR',
    lastUpdated: '14:25:00',
    latitude: 13.0790,
    longitude: 80.2820,
    accessibility: 'ALL_VEHICLES',
    source: 'SYNTHETIC_DEMO',
    stateVersion: 1,
    floodExposure: {
      is_exposed: false,
      status: 'CLEAR',
      scenario_id: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      evaluated: true,
    },
  },
  {
    id: 'S-003',
    name: 'Central Riverfront Community Hall',
    type: 'SHELTER',
    capacityTotal: 400,
    capacityOccupied: 400,
    operationalStatus: 'AT_CAPACITY',
    powerStatus: 'GRID',
    lastUpdated: '14:32:00',
    latitude: 13.0805,
    longitude: 80.2725,
    accessibility: 'HIGH_CLEARANCE_ONLY',
    source: 'SYNTHETIC_DEMO',
    stateVersion: 1,
    floodExposure: {
      is_exposed: true,
      status: 'EXPOSED',
      scenario_id: 'FLOOD-SCENARIO-101',
      mode: 'SIMULATION',
      evaluated: true,
    },
  },
];


// 6. Routes (Phase 07 Dijkstra / Phase 08 Dynamic Rerouting)
export const DEMO_ROUTES: RouteFeature[] = [
  {
    id: 'ROUTE-PREV',
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [80.2600, 13.0900], // Hospital H-001
        [80.2620, 13.0810],
        [80.2707, 13.0827], // Causeway bridge B-001 (NOW BLOCKED)
        [80.2780, 13.0840],
        [80.2790, 13.0790], // Relief Camp S-002
      ],
    },
    properties: {
      routeId: 'ROUTE-001-ORIGINAL',
      name: 'Direct Causeway Corridor (Blocked)',
      isCurrent: false,
      isBlocked: true,
      distanceKm: 3.2,
      travelTimeMin: 6.4,
      status: 'BLOCKED',
      startNode: 'H-001',
      endNode: 'S-002',
      changeExplanation: 'Invalidated due to Bridge B-001 structural closure.',
    },
  },
  {
    id: 'ROUTE-CURR',
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: [
        [80.2600, 13.0900], // Hospital H-001
        [80.2640, 13.0890], // Via North flyover
        [80.2740, 13.0920],
        [80.2780, 13.0840],
        [80.2790, 13.0790], // Relief Camp S-002
      ],
    },
    properties: {
      routeId: 'ROUTE-001-REROUTED',
      name: 'Northern Bypass Diversion (Active)',
      isCurrent: true,
      isBlocked: false,
      distanceKm: 4.6,
      travelTimeMin: 9.1,
      status: 'REROUTED',
      startNode: 'H-001',
      endNode: 'S-002',
      deltaDistanceKm: 1.4,
      deltaTravelTimeMin: 2.7,
      changeExplanation: 'Dynamic Rerouter computed detour around flooded Bridge B-001 via Road R-102.',
    },
  },
];

// 7. Critical Zones Overview
export const DEMO_CRITICAL_ZONES: CriticalZone[] = [
  {
    id: 'ZONE-COUM-01',
    name: 'Cooum Basin Sector 1',
    severity: 'CRITICAL',
    waterDepthM: 1.35,
    affectedRoadsCount: 3,
    nearestHospital: 'District General Trauma Hospital (3.2 km)',
    nearestShelter: 'Community Relief Center North (1.8 km)',
  },
  {
    id: 'ZONE-NORTH-02',
    name: 'North Swell Sector 2',
    severity: 'MEDIUM',
    waterDepthM: 0.45,
    affectedRoadsCount: 1,
    nearestHospital: 'District General Trauma Hospital (1.1 km)',
    nearestShelter: 'Community Relief Center North (0.6 km)',
  },
];
