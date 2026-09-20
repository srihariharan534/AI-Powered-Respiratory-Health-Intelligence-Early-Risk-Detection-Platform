/**
 * NEXUS Operational Districts & Multi-Hazard Context Registry
 * Authoritative definitions of supported administrative operational districts.
 * Each district provides geospatial coordinates, bounds, district-scoped EOC information,
 * and deterministic scenario datasets tailored to the active Emergency Type.
 */

import { EmergencyType, FacilitySummary, IncidentSummary, CriticalZone, RouteFeature, RoadFeature, BridgeFeature, FloodExtentFeature } from '../types';

export interface DistrictConfig {
  id: string;
  name: string;
  region: string;
  country: string;
  eocName: string;
  operationalArea: string;
  center: [number, number]; // [lon, lat]
  defaultZoom: number;
  dataStatus: 'FRESH' | 'STALE' | 'HISTORICAL' | 'SIMULATED';
}

export const DISTRICT_REGISTRY: Record<string, DistrictConfig> = {
  chennai: {
    id: 'chennai',
    name: 'Chennai',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Chennai District Emergency Operations Center',
    operationalArea: 'Chennai Core Zone 1',
    center: [80.2707, 13.0827],
    defaultZoom: 14,
    dataStatus: 'FRESH',
  },
  coimbatore: {
    id: 'coimbatore',
    name: 'Coimbatore',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Coimbatore District Emergency Operations Center',
    operationalArea: 'Coimbatore Industrial & Foothills Zone',
    center: [76.9558, 11.0168],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  madurai: {
    id: 'madurai',
    name: 'Madurai',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Madurai District Emergency Operations Center',
    operationalArea: 'Madurai Vaigai Riverine Sector',
    center: [78.1198, 9.9252],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  tiruchirappalli: {
    id: 'tiruchirappalli',
    name: 'Tiruchirappalli',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Tiruchirappalli District Emergency Operations Center',
    operationalArea: 'Kaveri Delta Convergence Sector',
    center: [78.7047, 10.7905],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  salem: {
    id: 'salem',
    name: 'Salem',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Salem District Emergency Operations Center',
    operationalArea: 'Salem Valley & Mining Perimeter',
    center: [78.1460, 11.6643],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  tiruppur: {
    id: 'tiruppur',
    name: 'Tiruppur',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Tiruppur District Emergency Operations Center',
    operationalArea: 'Noyyal Basin Industrial Corridor',
    center: [77.3411, 11.1085],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  erode: {
    id: 'erode',
    name: 'Erode',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Erode District Emergency Operations Center',
    operationalArea: 'Bhavani River Confluence Zone',
    center: [77.7172, 11.3410],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  vellore: {
    id: 'vellore',
    name: 'Vellore',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Vellore District Emergency Operations Center',
    operationalArea: 'Palar Basin Strategic Junction',
    center: [79.1325, 12.9165],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  thanjavur: {
    id: 'thanjavur',
    name: 'Thanjavur',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Thanjavur District Emergency Operations Center',
    operationalArea: 'Delta Agricultural Relief Sector',
    center: [79.1378, 10.7870],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
  tirunelveli: {
    id: 'tirunelveli',
    name: 'Tirunelveli',
    region: 'Tamil Nadu',
    country: 'India',
    eocName: 'Tirunelveli District Emergency Operations Center',
    operationalArea: 'Thamirabarani Coastal Flank',
    center: [77.7567, 8.7139],
    defaultZoom: 13,
    dataStatus: 'FRESH',
  },
};

export const DEFAULT_DISTRICT_ID = 'chennai';

/**
 * Returns district-scoped operational GIS and telemetry data
 * conditioned on both District and Emergency Type.
 */
export function getDistrictOperationalData(districtId: string, emergencyType: EmergencyType) {
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY[DEFAULT_DISTRICT_ID];
  const [lon, lat] = district.center;

  // 1. Incidents tailored to Emergency Type and District Coordinates
  const incidents: IncidentSummary[] = [
    {
      id: `INC-${district.id.slice(0, 3).toUpperCase()}-001`,
      type: `${emergencyType}_PRIMARY_EVENT`,
      severity: 'CRITICAL',
      status: 'REPORTED',
      description: `Critical ${emergencyType.replace(/_/g, ' ')} impact reported in ${district.name} central sector. Emergency dispatch and response teams assigned.`,
      latitude: lat + 0.002,
      longitude: lon + 0.002,
      reportedAt: '14:30:00',
      source: `FIELD_REPORT (${district.name} Officer #01)`,
      assignedUnit: 'RESCUE-UNIT-01',
    },
    {
      id: `INC-${district.id.slice(0, 3).toUpperCase()}-002`,
      type: 'ROAD_BLOCKAGE',
      severity: 'HIGH',
      status: 'DISPATCHED',
      description: `Infrastructure obstruction and road impassability due to ${emergencyType.toLowerCase()} on primary arterial bypass.`,
      latitude: lat + 0.006,
      longitude: lon - 0.005,
      reportedAt: '14:22:00',
      source: `${district.name} Police Dispatch`,
      assignedUnit: 'RECOVERY-TRUCK-01',
    },
    {
      id: `INC-${district.id.slice(0, 3).toUpperCase()}-003`,
      type: 'EVAC_ALERT',
      severity: 'MEDIUM',
      status: 'ON_SCENE',
      description: `Vulnerable demographic cluster requiring assisted transfer to designated ${district.name} shelter.`,
      latitude: lat - 0.005,
      longitude: lon - 0.003,
      reportedAt: '14:10:00',
      source: 'PUBLIC_HOTLINE',
      assignedUnit: 'AMBULANCE-02',
    },
  ];

  // 2. Hospitals in District
  const hospitals: FacilitySummary[] = [
    {
      id: `HOSP-${district.id.slice(0, 3).toUpperCase()}-01`,
      name: `${district.name} District Headquarters Hospital`,
      type: 'HOSPITAL',
      capacityTotal: 250,
      capacityOccupied: 198,
      operationalStatus: 'OPERATIONAL',
      powerStatus: 'GRID',
      lastUpdated: '14:20:00',
      latitude: lat + 0.008,
      longitude: lon - 0.007,
      emergencyAvailable: true,
      icuAvailable: 12,
      accessibility: 'ALL_VEHICLES',
      source: `${district.name} Health Directorate`,
      stateVersion: 104,
      floodExposure: { is_exposed: false, status: 'CLEAR', evaluated: true },
    },
    {
      id: `HOSP-${district.id.slice(0, 3).toUpperCase()}-02`,
      name: `${district.name} Government Trauma Care Centre`,
      type: 'HOSPITAL',
      capacityTotal: 150,
      capacityOccupied: 136,
      operationalStatus: 'OPERATIONAL',
      powerStatus: 'GENERATOR',
      lastUpdated: '14:15:00',
      latitude: lat - 0.007,
      longitude: lon + 0.006,
      emergencyAvailable: true,
      icuAvailable: 6,
      accessibility: 'ALL_VEHICLES',
      source: `${district.name} Health Directorate`,
      stateVersion: 104,
      floodExposure: { is_exposed: false, status: 'CLEAR', evaluated: true },
    },
  ];

  // 3. Shelters in District
  const shelters: FacilitySummary[] = [
    {
      id: `SHEL-${district.id.slice(0, 3).toUpperCase()}-01`,
      name: `${district.name} Community Relief & Evacuation Center`,
      type: 'SHELTER',
      capacityTotal: 500,
      capacityOccupied: 310,
      operationalStatus: 'OPEN',
      powerStatus: 'GRID',
      lastUpdated: '14:25:00',
      latitude: lat + 0.005,
      longitude: lon + 0.009,
      accessibility: 'ALL_VEHICLES',
      source: `${district.name} Revenue & Disaster Management`,
      stateVersion: 104,
      floodExposure: { is_exposed: false, status: 'CLEAR', evaluated: true },
    },
    {
      id: `SHEL-${district.id.slice(0, 3).toUpperCase()}-02`,
      name: `${district.name} North Multi-Purpose Cyclone/Disaster Shelter`,
      type: 'SHELTER',
      capacityTotal: 350,
      capacityOccupied: 220,
      operationalStatus: 'OPEN',
      powerStatus: 'GENERATOR',
      lastUpdated: '14:18:00',
      latitude: lat - 0.006,
      longitude: lon - 0.008,
      accessibility: 'ALL_VEHICLES',
      source: `${district.name} Revenue & Disaster Management`,
      stateVersion: 104,
      floodExposure: { is_exposed: false, status: 'CLEAR', evaluated: true },
    },
  ];

  // 4. Critical Operational Zones in District
  const criticalZones: CriticalZone[] = [
    {
      id: `ZONE-${district.id.slice(0, 3).toUpperCase()}-1`,
      name: `${district.name} Sector 1 (${district.operationalArea})`,
      severity: 'CRITICAL',
      waterDepthM: emergencyType === 'FLOOD' ? 1.2 : 0,
      affectedRoadsCount: 4,
      nearestHospital: `${district.name} District Headquarters Hospital`,
      nearestShelter: `${district.name} Community Relief & Evacuation Center`,
    },
    {
      id: `ZONE-${district.id.slice(0, 3).toUpperCase()}-2`,
      name: `${district.name} Sector 2 (Urban Transit Flank)`,
      severity: 'HIGH',
      waterDepthM: emergencyType === 'FLOOD' ? 0.6 : 0,
      affectedRoadsCount: 2,
      nearestHospital: `${district.name} Government Trauma Care Centre`,
      nearestShelter: `${district.name} North Multi-Purpose Cyclone/Disaster Shelter`,
    },
  ];

  // 5. Road Network Features in District
  const roadFeatures: RoadFeature[] = [
    {
      id: `ROAD-${district.id.slice(0, 3).toUpperCase()}-01`,
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [
          [lon - 0.015, lat - 0.004],
          [lon - 0.005, lat + 0.002],
          [lon + 0.005, lat + 0.004],
          [lon + 0.015, lat + 0.006],
        ],
      },
      properties: {
        roadId: `R-${district.id.slice(0, 3).toUpperCase()}-101`,
        name: `${district.name} Central Arterial Express`,
        roadType: 'primary' as const,
        status: 'BLOCKED',
        speedLimitKmh: 50,
        accessibility: 'IMPASSABLE',
        floodDepthCm: emergencyType === 'FLOOD' ? 85 : 0,
        source: 'OpenStreetMap + Dynamic Operational Overlay',
        updatedAt: '2026-09-20T14:30:00Z',
      },
    },
    {
      id: `ROAD-${district.id.slice(0, 3).toUpperCase()}-02`,
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [
          [lon - 0.015, lat + 0.008],
          [lon, lat + 0.010],
          [lon + 0.015, lat + 0.012],
        ],
      },
      properties: {
        roadId: `R-${district.id.slice(0, 3).toUpperCase()}-102`,
        name: `${district.name} Northern Perimeter Bypass`,
        roadType: 'secondary' as const,
        status: 'OPEN',
        speedLimitKmh: 60,
        accessibility: 'ALL_VEHICLES',
        floodDepthCm: 0,
        source: 'OpenStreetMap + Dynamic Operational Overlay',
        updatedAt: '2026-09-20T14:30:00Z',
      },
    },
  ];

  // 6. Bridges in District
  const bridgeFeatures: BridgeFeature[] = [
    {
      id: `BRG-${district.id.slice(0, 3).toUpperCase()}-01`,
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [lon + 0.001, lat + 0.003],
      },
      properties: {
        bridgeId: `B-${district.id.slice(0, 3).toUpperCase()}-01`,
        name: `${district.name} River Causeway Crossing`,
        roadId: `R-${district.id.slice(0, 3).toUpperCase()}-101`,
        status: 'FAILED',
        clearanceM: 1.1,
        source: 'Digital Twin State Authority',
        updatedAt: '2026-09-20T14:32:00Z',
      },
    },
  ];

  // 7. Dynamic Evacuation & Rerouting Routes in District
  const routes: RouteFeature[] = [
    {
      id: `RTE-${district.id.slice(0, 3).toUpperCase()}-01`,
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [
          [lon - 0.010, lat - 0.004],
          [lon, lat],
          [lon + 0.008, lat + 0.008],
        ],
      },
      properties: {
        routeId: `RTE-${district.id.slice(0, 3).toUpperCase()}-DIR`,
        name: `Primary Direct Corridor (${district.name})`,
        distanceKm: 3.2,
        travelTimeMin: 6.4,
        status: 'BLOCKED',
        isCurrent: false,
        startNode: `${district.name} South Junction`,
        endNode: `${district.name} EOC Node`,
      },
    },
    {
      id: `RTE-${district.id.slice(0, 3).toUpperCase()}-02`,
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [
          [lon - 0.010, lat - 0.004],
          [lon - 0.008, lat + 0.008],
          [lon, lat + 0.010],
          [lon + 0.008, lat + 0.008],
        ],
      },
      properties: {
        routeId: `RTE-${district.id.slice(0, 3).toUpperCase()}-DIV`,
        name: `Emergency Diversion via Northern Bypass (${district.name})`,
        distanceKm: 4.6,
        travelTimeMin: 9.1,
        status: 'REROUTED',
        isCurrent: true,
        startNode: `${district.name} South Junction`,
        endNode: `${district.name} EOC Node`,
        deltaDistanceKm: 1.4,
        deltaTravelTimeMin: 2.7,
        changeExplanation: `Direct causeway compromised by ${emergencyType.toLowerCase()} impact. Diversion via Northern Bypass active.`,
      },
    },
  ];

  // 8. Hazard Extent Polygon (Polygon around district center)
  const floodFeatures: FloodExtentFeature[] = [
    {
      id: `HAZ-${district.id.slice(0, 3).toUpperCase()}-01`,
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [lon - 0.006, lat - 0.005],
            [lon + 0.006, lat - 0.005],
            [lon + 0.007, lat + 0.004],
            [lon - 0.004, lat + 0.005],
            [lon - 0.006, lat - 0.005],
          ],
        ],
      },
      properties: {
        floodZoneId: `HAZ-${district.id.slice(0, 3).toUpperCase()}-01`,
        name: `${district.name} ${emergencyType.replace(/_/g, ' ')} Impact Polygon`,
        severity: 'CRITICAL',
        waterDepthM: emergencyType === 'FLOOD' ? 1.35 : 0.4,
        scenarioId: `${emergencyType}-${district.id.toUpperCase()}-SCENARIO`,
        mode: district.id === 'chennai' ? 'REAL' : 'SIMULATION',
        source: `NEXUS ${emergencyType} Model Engine`,
        updatedAt: '2026-09-20T14:30:00Z',
      },
    },
  ];

  // 9. Primary Recommendation tailored to District + Hazard
  const recommendation = {
    id: `REC-${emergencyType.slice(0, 4)}-${district.id.toUpperCase()}-01`,
    action: emergencyType === 'WILDFIRE' ? 'DISPATCH_FIRE_SUPPRESSION' : emergencyType === 'CYCLONE' ? 'INITIATE_COASTAL_EVACUATION' : emergencyType === 'LANDSLIDE' ? 'CLEAR_SLOPE_CORRIDOR' : emergencyType === 'EARTHQUAKE' ? 'STRUCTURAL_TRIAGE_DISPATCH' : 'DEPLOY_RESCUE_TEAM',
    target: `${criticalZones[0].name}`,
    priority: 1,
    reasoning: `Immediate operational prioritization for ${district.name} under ${emergencyType.replace(/_/g, ' ')} conditions. Critical access corridor compromised; diversion to ${hospitals[0].name} verified clear.`,
    score: 0.89,
    dataFreshness: district.dataStatus,
    factors: [
      { name: `${emergencyType.toLowerCase()}_exposure`, weight: 0.30, description: `Elevated ${emergencyType.toLowerCase()} severity in ${district.operationalArea}` },
      { name: 'population_vulnerability', weight: 0.25, description: `High density residential cluster in ${district.name} sector` },
      { name: 'route_clearance', weight: 0.25, description: `Northern Bypass corridor open to ${hospitals[0].name}` },
      { name: 'facility_capacity', weight: 0.20, description: `${hospitals[0].name} has available surge capacity` },
    ],
  };

  return {
    district,
    incidents,
    hospitals,
    shelters,
    criticalZones,
    roadFeatures,
    bridgeFeatures,
    routes,
    floodFeatures,
    recommendation,
  };
}
