/**
 * Deterministic Field Data Fixtures (Phase 22).
 * Clearly labeled as DEMO DATA to preserve judge credibility.
 */

import { FieldAssignment } from '../../types';

export const DEMO_ASSIGNMENT: FieldAssignment = {
  assignment_id: 'ASSIGN-ALPHA-01',
  incident_id: 'INC-DEMO-001',
  task_name: 'Sector 4 Embankment Breach Inspection',
  instructions: 'Assess flood water progression along the Adyar river bend and verify whether road corridor remains passable for light emergency vehicles.',
  priority: 1,
  status: 'ASSIGNED',
  location: {
    name: 'Saidapet Bridge South Corridor',
    latitude: 13.0180,
    longitude: 80.2230,
  },
  assigned_at: '2026-09-20T06:30:00Z',
  data_mode: 'DEMO',
};
