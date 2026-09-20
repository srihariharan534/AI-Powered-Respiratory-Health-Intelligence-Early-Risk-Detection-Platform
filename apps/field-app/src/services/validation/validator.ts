/**
 * Validation utilities enforcing canonical Phase 04 schema requirements.
 */

import { CanonicalIncidentReport, IncidentEventType, IncidentSeverity } from '../../types';

export class DataValidator {
  public static validateIncident(report: Partial<CanonicalIncidentReport>): void {
    if (!report.incident_id || report.incident_id.length < 3) {
      throw new Error('Validation Error: incident_id must be at least 3 characters.');
    }

    if (!report.description || !report.description.trim()) {
      throw new Error('Validation Error: description is mandatory.');
    }

    const validSeverities: IncidentSeverity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    if (!report.severity || !validSeverities.includes(report.severity)) {
      throw new Error(`Validation Error: invalid severity "${report.severity}".`);
    }

    const validEventTypes: IncidentEventType[] = [
      'FLOOD_INUNDATION',
      'ROAD_BLOCKED',
      'BRIDGE_FAILURE',
      'EMBANKMENT_BREACH',
      'MEDICAL_EMERGENCY',
      'TRAPPED_PERSONS',
      'SHELTER_NEEDED',
      'RESOURCE_REQUEST',
    ];
    if (!report.event_type || !validEventTypes.includes(report.event_type)) {
      throw new Error(`Validation Error: invalid event_type "${report.event_type}".`);
    }

    if (!report.location || report.location.type !== 'Point' || !Array.isArray(report.location.coordinates)) {
      throw new Error('Validation Error: location must be a valid GeoJSON Point geometry.');
    }

    const [lon, lat] = report.location.coordinates;
    if (typeof lon !== 'number' || isNaN(lon) || lon < -180 || lon > 180) {
      throw new Error(`Validation Error: longitude must be between -180 and 180 (got ${lon}).`);
    }

    if (typeof lat !== 'number' || isNaN(lat) || lat < -90 || lat > 90) {
      throw new Error(`Validation Error: latitude must be between -90 and 90 (got ${lat}).`);
    }
  }
}
